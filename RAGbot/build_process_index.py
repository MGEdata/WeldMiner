"""Precompute database process-key embeddings before interactive RAG queries."""
from __future__ import annotations

import os
from contextlib import closing
import sqlite3
import sys
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from RAGbot.retrieval.process_parameter_inspector import ProcessParameterInspector
from RAGbot.retrieval.process_vector_store import ProcessVectorStore

# Edit these settings, then run this file directly in your IDE.
DATABASE_PATH = ""  # Empty: read RAG_DATABASE_PATH from the root .env.
ENV_FILE = PROJECT_ROOT / ".env"
API_KEY = ""  # Empty: read QWEN_API_KEY.
BASE_URL = ""  # Empty: read QWEN_API_BASE_URL; choose your service region.
MODEL = ""  # Empty: read QWEN_EMBEDDING_MODEL (default: text-embedding-v3).
SPECIMEN_BATCH_SIZE = 200
EMBEDDING_BATCH_SIZE = 10
REFRESH_EXISTING = False  # True: re-embed current keys, e.g. after changing prompt language.


def build_index(database_path, store, *, specimen_batch_size=200, refresh=False):
    """Scan all specimens and deduplicate globally before making embedding requests.

    A failed API batch leaves earlier committed batches available for resuming.
    Refresh replaces each batch only after its embedding request succeeds.
    """
    source = Path(database_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source != store.source_db_path.expanduser().resolve():
        raise ValueError("The inspector and vector store must use the same database")
    if not 1 <= specimen_batch_size <= 900:
        raise ValueError("SPECIMEN_BATCH_SIZE must be between 1 and 900")
    started = perf_counter()
    conn = sqlite3.connect(str(source))
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(specimen_records)")}
        if not {"specimen_id", "welding_params"}.issubset(columns):
            raise ValueError("Expected specimen_records with specimen_id and welding_params columns")
        # Reuse the runtime cache schema; source specimen records are never modified.
        conn.execute("""CREATE TABLE IF NOT EXISTS process_parameter_vectors (
            action_name TEXT NOT NULL DEFAULT '',
            parameter_name TEXT NOT NULL,
            embedding_model TEXT NOT NULL,
            embedding BLOB NOT NULL,
            PRIMARY KEY (action_name, parameter_name, embedding_model)
        )""")
        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM specimen_records").fetchone()[0]
    finally:
        conn.close()

    inspector = ProcessParameterInspector(str(source), max_observations=specimen_batch_size)
    processed = written = 0
    unique_catalog = {}
    occurrences = 0
    last_id = None
    while True:
        with closing(sqlite3.connect(str(source))) as conn:
            if last_id is None:
                rows = conn.execute(
                    "SELECT specimen_id FROM specimen_records ORDER BY specimen_id LIMIT ?",
                    (specimen_batch_size,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT specimen_id FROM specimen_records WHERE specimen_id > ? ORDER BY specimen_id LIMIT ?",
                    (last_id, specimen_batch_size),
                ).fetchall()
        if not rows:
            break
        ids = [row[0] for row in rows]
        # No query-time top-key cap: index every discovered key in every batch.
        catalog = inspector.discover_keys(ids, max_keys=sys.maxsize)
        for item in catalog:
            pair = (str(item.get("action_name") or "").strip(), str(item["parameter_name"]).strip())
            if pair[1]:
                occurrences += item["count"]
                unique_catalog.setdefault(pair, {"action_name": pair[0], "parameter_name": pair[1]})
        processed += len(ids)
        last_id = ids[-1]
        print(f"Scan [{processed}/{total}]: {occurrences} parameter occurrences; {len(unique_catalog)} unique action/parameter pairs", flush=True)

    catalog = [unique_catalog[pair] for pair in sorted(unique_catalog)]
    with closing(sqlite3.connect(str(source))) as conn:
        cached = {(str(a), str(p)) for a, p in conn.execute(
            "SELECT action_name, parameter_name FROM process_parameter_vectors WHERE embedding_model = ?",
            (store.model,),
        )}
    reused = 0 if refresh else sum(pair in cached for pair in unique_catalog)
    pending = len(catalog) - reused
    print(f"Deduplication complete: {len(catalog)} unique pairs, {reused} cached, {pending} to encode", flush=True)
    def progress(done, count):
        print(f"Embedding [{done}/{count}] pairs saved", flush=True)
    written = store.ensure_catalog(catalog, refresh=refresh, progress=progress)
    result = {
        "specimens": processed, "unique_keys": len(unique_catalog), "parameter_occurrences": occurrences, "cached_keys_reused": reused, "embeddings_written": written,
        "cached_for_model": store.count(), "model": store.model,
        "seconds": round(perf_counter() - started, 3),
    }
    print(result, flush=True)
    return result


def main():
    load_dotenv(ENV_FILE, override=False)
    source = Path(DATABASE_PATH or os.getenv("RAG_DATABASE_PATH") or "data/welding_rag.db").expanduser()
    if not source.is_absolute():
        source = PROJECT_ROOT / source
    key = API_KEY or os.getenv("QWEN_API_KEY")
    url = BASE_URL or os.getenv("QWEN_API_BASE_URL")
    model = MODEL or os.getenv("QWEN_EMBEDDING_MODEL") or "text-embedding-v3"
    if not key or not url:
        raise ValueError("Set QWEN_API_KEY and the regional QWEN_API_BASE_URL in .env or the settings above")
    store = ProcessVectorStore(str(source), key, url, model, batch_size=EMBEDDING_BATCH_SIZE)
    build_index(source, store, specimen_batch_size=SPECIMEN_BATCH_SIZE, refresh=REFRESH_EXISTING)


if __name__ == "__main__":
    main()
