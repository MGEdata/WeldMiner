"""Persistent semantic index for welding action and parameter-name pairs."""
from __future__ import annotations

import math
import sqlite3
from array import array
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import requests


@dataclass
class ProcessVectorMatch:
    action_name: str
    parameter_name: str
    vector_score: float
    count: int
    specimen_count: int
    sample_values: List[str]
    sample_paths: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_catalog_item(self) -> Dict[str, Any]:
        return {
            "action_name": self.action_name,
            "parameter_name": self.parameter_name,
            "vector_score": round(self.vector_score, 6),
            "count": self.count,
            "specimen_count": self.specimen_count,
            "sample_values": self.sample_values,
            "sample_paths": self.sample_paths,
        }


class ProcessVectorStore:
    """Embed action/parameter pairs in the main RAG SQLite database."""

    def __init__(
        self,
        source_db_path: str,
        api_key: str,
        base_url: str,
        model: str,
        batch_size: int = 10,
        embed_texts: Optional[Callable[[Sequence[str]], Sequence[Sequence[float]]]] = None,
    ):
        self.source_db_path = Path(source_db_path)
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.batch_size = max(1, min(int(batch_size), 10))
        self._embed_override = embed_texts
        self._query_cache: Dict[str, List[float]] = {}

    @property
    def available(self) -> bool:
        return bool(self._embed_override or (self.api_key and self.base_url and self.model))

    def count(self) -> int:
        if not self.source_db_path.exists():
            return 0
        conn = self._connect()
        try:
            return int(
                conn.execute(
                    "SELECT COUNT(*) FROM process_parameter_vectors WHERE embedding_model = ?",
                    (self.model,),
                ).fetchone()[0]
            )
        finally:
            conn.close()

    def search(
        self,
        query: str,
        catalog: Sequence[Dict[str, Any]],
        top_k: int = 48,
    ) -> List[ProcessVectorMatch]:
        if not query.strip() or not catalog or not self.available:
            return []
        self.ensure_catalog(catalog)
        query_vector = self._query_vector(query)
        catalog_by_pair = {
            _catalog_pair(item): item
            for item in catalog
            if str(item.get("parameter_name") or "").strip()
        }
        candidate_pairs = set(catalog_by_pair)
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT action_name, parameter_name, embedding
                FROM process_parameter_vectors
                WHERE embedding_model = ?
                """,
                (self.model,),
            ).fetchall()
        finally:
            conn.close()

        scored = []
        for action_name, parameter_name, blob in rows:
            pair = (str(action_name or ""), str(parameter_name))
            if pair not in candidate_pairs:
                continue
            item = catalog_by_pair[pair]
            scored.append(
                ProcessVectorMatch(
                    action_name=pair[0],
                    parameter_name=pair[1],
                    vector_score=_cosine_similarity(query_vector, _decode_vector(blob)),
                    count=int(item.get("count") or 0),
                    specimen_count=int(item.get("specimen_count") or 0),
                    sample_values=[str(value) for value in item.get("sample_values") or []],
                    sample_paths=[str(value) for value in item.get("sample_paths") or []],
                )
            )
        scored.sort(
            key=lambda item: (item.vector_score, item.specimen_count, item.count),
            reverse=True,
        )
        return scored[: max(1, min(int(top_k), len(scored)))]

    def ensure_catalog(self, catalog: Sequence[Dict[str, Any]]) -> int:
        documents: Dict[Tuple[str, str], str] = {}
        for item in catalog:
            pair = _catalog_pair(item)
            if pair[1]:
                documents[pair] = _embedding_text(*pair)
        if not documents:
            return 0

        conn = self._connect()
        try:
            existing = {
                (str(row[0] or ""), str(row[1]))
                for row in conn.execute(
                    """
                    SELECT action_name, parameter_name
                    FROM process_parameter_vectors
                    WHERE embedding_model = ?
                    """,
                    (self.model,),
                ).fetchall()
            }
            missing = [(pair, text) for pair, text in documents.items() if pair not in existing]
            inserted = 0
            for batch in _chunks(missing, self.batch_size):
                texts = [item[1] for item in batch]
                vectors = list(self._embed(texts))
                if len(vectors) != len(batch):
                    raise RuntimeError(
                        f"Embedding API returned {len(vectors)} vectors for {len(batch)} texts"
                    )
                rows = []
                for ((action_name, parameter_name), _), vector_values in zip(batch, vectors):
                    vector = [float(value) for value in vector_values]
                    if not vector:
                        raise RuntimeError("Embedding API returned an empty vector")
                    rows.append((action_name, parameter_name, self.model, _encode_vector(vector)))
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO process_parameter_vectors (
                        action_name, parameter_name, embedding_model, embedding
                    ) VALUES (?, ?, ?, ?)
                    """,
                    rows,
                )
                conn.commit()
                inserted += len(rows)
            return inserted
        finally:
            conn.close()

    def _query_vector(self, query: str) -> List[float]:
        text = f"Welding process action and parameter concept to retrieve: {query.strip()}"
        cache_key = f"{self.model}\n{text}"
        if cache_key not in self._query_cache:
            vectors = list(self._embed([text]))
            if not vectors or not vectors[0]:
                raise RuntimeError("Embedding API returned no query vector")
            self._query_cache[cache_key] = [float(value) for value in vectors[0]]
        return self._query_cache[cache_key]

    def _embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        if self._embed_override:
            return self._embed_override(texts)
        session = requests.Session()
        session.trust_env = False
        response = session.post(
            self.base_url.rstrip("/") + "/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self.model, "input": list(texts)},
            timeout=90,
        )
        response.raise_for_status()
        payload = response.json()
        data = sorted(payload.get("data") or [], key=lambda item: int(item.get("index", 0)))
        return [item["embedding"] for item in data]

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.source_db_path), timeout=30)


def _catalog_pair(item: Dict[str, Any]) -> Tuple[str, str]:
    return (
        str(item.get("action_name") or "").strip(),
        str(item.get("parameter_name") or "").strip(),
    )


def _embedding_text(action_name: str, parameter_name: str) -> str:
    action = action_name or "Unspecified process action"
    return f"Welding process action: {action}; process parameter name: {parameter_name}"


def _encode_vector(values: Sequence[float]) -> bytes:
    return array("f", (float(value) for value in values)).tobytes()


def _decode_vector(blob: bytes) -> List[float]:
    values = array("f")
    values.frombytes(blob)
    return list(values)


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        return -1.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else -1.0


def _chunks(values: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]
