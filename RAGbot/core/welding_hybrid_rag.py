"""Iterative SQL Agentic RAG over normalized welding observations and JSON process data."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import requests

from ..config import (
    DEFAULT_TOP_K,
    LLM_MODEL,
    PROCESS_EMBEDDING_MODEL,
    PROCESS_VECTOR_TOP_K,
    QWEN_API_BASE_URL,
    QWEN_API_KEY,
)
from ..retrieval.process_parameter_inspector import (
    ProcessParameterFact,
    ProcessParameterInspector,
    analyze_process_performance,
)
from ..retrieval.process_vector_store import ProcessVectorMatch, ProcessVectorStore
from ..retrieval.sql_query_planner import SQLQueryPlan, WeldingSQLPlanner
from ..retrieval.sql_retriever import WeldingSQLRetriever


class WeldingAgenticRAG:
    """SQL-only Agentic RAG with query-time process JSON inspection."""

    def __init__(
        self,
        db_path: str = "extraction_results.db",
        top_k: int = DEFAULT_TOP_K,
        enable_process_vectors: bool = True,
        max_agent_iterations: int = 3,
        process_candidate_limit: int = 120,
        process_vector_top_k: int = PROCESS_VECTOR_TOP_K,
    ):
        self.db_path = db_path
        self.top_k = top_k
        self.enable_process_vectors = bool(enable_process_vectors)
        self.max_agent_iterations = max(1, min(int(max_agent_iterations), 3))
        self.process_candidate_limit = max(top_k, min(int(process_candidate_limit), 200))
        self.process_vector_top_k = max(8, min(int(process_vector_top_k), 96))
        self.record_count = 0
        self.paper_count = 0
        self.llm_enabled = bool(QWEN_API_KEY and QWEN_API_BASE_URL)
        self.sql_planner = None
        self.sql_retriever = WeldingSQLRetriever(
            db_path,
            max_rows=self.process_candidate_limit,
        )
        self.process_inspector = ProcessParameterInspector(
            db_path,
            max_observations=self.process_candidate_limit,
        )
        self.process_vector_store = ProcessVectorStore(
            source_db_path=db_path,
            api_key=QWEN_API_KEY if self.enable_process_vectors else "",
            base_url=QWEN_API_BASE_URL,
            model=PROCESS_EMBEDDING_MODEL,
        )
        self.last_query_plan: Optional[SQLQueryPlan] = None
        self.last_planning_error: Optional[str] = None
        self.last_agent_trace: List[Dict[str, Any]] = []
        self.last_process_analysis: Optional[Dict[str, Any]] = None

        if self.llm_enabled:
            self.sql_planner = WeldingSQLPlanner(
                invoke_llm=self._invoke_planner_model,
                schema_context=self.sql_retriever.describe_schema(),
                max_rows=self.process_candidate_limit,
            )

    def index_database(self) -> bool:
        """Validate the normalized database and cache lightweight counts."""
        db_file = Path(self.db_path)
        if not db_file.exists():
            return False
        conn = sqlite3.connect(str(db_file))
        try:
            required = {"papers", "specimen_records", "property_measurements"}
            existing = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            if not required.issubset(existing):
                return False
            self.record_count = int(
                conn.execute("SELECT COUNT(*) FROM specimen_records").fetchone()[0]
            )
            self.paper_count = int(conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0])
            return self.record_count > 0
        finally:
            conn.close()

    def retrieve(self, question: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Run candidate SQL, inspect process JSON when needed, and verify evidence."""
        if not self.record_count:
            self.index_database()
        final_k = top_k or self.top_k
        self.last_query_plan = None
        self.last_planning_error = None
        self.last_agent_trace = []
        self.last_process_analysis = None

        if not self.sql_planner:
            self.last_planning_error = "Agentic retrieval requires an initialized LLM planner."
            return []

        try:
            plan = self.sql_planner.plan(
                question,
                limit=self.process_candidate_limit,
            )
            self.last_query_plan = plan
            self.last_agent_trace.append(
                {
                    "iteration": 0,
                    "tool": "sql_planner",
                    "status": "completed",
                    "detail": {
                        "process_access_mode": plan.process_access_mode,
                        "process_parameter_query": plan.process_parameter_query,
                        "process_task": plan.process_task,
                    },
                }
            )

            sql_result = self.sql_retriever.execute(
                plan,
                expected_property=plan.target_property,
                expected_target=plan.property_target,
            )
            hits = sql_result.hits
            self.last_agent_trace.append(
                {
                    "iteration": 0,
                    "tool": "execute_sql",
                    "status": "completed" if hits else "no_results",
                    "detail": {
                        "candidate_count": sql_result.candidate_count,
                        "specimen_count": len(hits),
                    },
                }
            )
            if not hits:
                return []

            if plan.process_access_mode == "full_json":
                hits = self._read_full_process_json(hits[:final_k])
                return hits
            if plan.process_access_mode == "semantic_keys":
                hits = self._inspect_process_parameters(question, plan, hits)
            return hits[:final_k]
        except Exception as exc:
            self.last_planning_error = str(exc)
            self.last_agent_trace.append(
                {
                    "iteration": len(self.last_agent_trace),
                    "tool": "agent",
                    "status": "failed",
                    "detail": {"error": str(exc)},
                }
            )
            return []

    def _read_full_process_json(
        self,
        hits: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Attach every process JSON leaf without vector search or SQL reordering."""
        specimen_ids = _specimen_ids(hits)
        facts = self.process_inspector.inspect_all(specimen_ids)
        facts_by_specimen: Dict[int, List[Dict[str, Any]]] = {}
        for fact in facts:
            facts_by_specimen.setdefault(fact.specimen_id, []).append(
                fact.to_dict()
            )

        warnings = []
        if not facts:
            warnings.append(
                "Candidate specimens contain no expandable welding_params JSON leaf parameters."
            )
        self.last_process_analysis = {
            "process_access_mode": "full_json",
            "candidate_specimen_count": len(specimen_ids),
            "fact_count": len(facts),
            "parsed_specimen_count": len(facts_by_specimen),
            "sql_order_preserved": True,
            "vector_search": {
                "enabled": self.enable_process_vectors,
                "used": False,
                "reason": "Read the complete process directly from the original JSON; parameter-key vector retrieval is unnecessary.",
            },
            "warnings": warnings,
        }
        self.last_agent_trace.append(
            {
                "iteration": 1,
                "tool": "read_full_process_json",
                "status": "completed" if facts else "no_results",
                "detail": {
                    "candidate_specimens": len(specimen_ids),
                    "parsed_specimens": len(facts_by_specimen),
                    "fact_count": len(facts),
                    "sql_order_preserved": True,
                    "vector_search_used": False,
                },
            }
        )
        for hit in hits:
            channels = hit.setdefault("channels", [])
            if "full_json" not in channels:
                channels.append("full_json")
        _attach_process_results(
            hits,
            facts,
            self.last_process_analysis,
            facts_by_specimen,
        )
        return hits

    def _inspect_process_parameters(
        self,
        question: str,
        plan: SQLQueryPlan,
        hits: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        specimen_ids = _specimen_ids(hits)
        catalog = self.process_inspector.discover_keys(specimen_ids, max_keys=4000)
        self.last_agent_trace.append(
            {
                "iteration": 1,
                "tool": "discover_process_keys",
                "status": "completed" if catalog else "no_results",
                "detail": {
                    "candidate_specimens": len(specimen_ids),
                    "discovered_action_parameter_count": len(catalog),
                    "catalog_truncated": len(catalog) >= 4000,
                },
            }
        )
        if not catalog:
            self.last_process_analysis = {
                "fact_count": 0,
                "numeric_pair_count": 0,
                "groups": [],
                "paired_records": [],
                "warnings": ["Candidate specimens contain no expandable welding_params JSON leaf parameters."],
            }
            _attach_process_results(hits, [], self.last_process_analysis, {})
            return hits

        selected_parameters: List[Dict[str, str]] = []
        facts: List[ProcessParameterFact] = []
        analysis: Dict[str, Any] = {}
        feedback = ""
        previous_pair_count = -1
        last_selection: Dict[str, Any] = {}
        vector_matches: List[ProcessVectorMatch] = []
        performance_map = _performance_by_specimen(hits, plan.target_property)

        if not self.process_vector_store.available:
            raise RuntimeError("semantic_keys mode requires an available process embedding service.")

        for iteration in range(1, self.max_agent_iterations + 1):
            vector_limit = min(
                len(catalog),
                self.process_vector_top_k * iteration,
            )
            vector_matches = self.process_vector_store.search(
                query=plan.process_parameter_query,
                catalog=catalog,
                top_k=vector_limit,
            )
            if not vector_matches:
                raise RuntimeError("Process vector retrieval returned no candidate action/parameter names.")
            selection_catalog = [match.to_catalog_item() for match in vector_matches]
            self.last_agent_trace.append(
                {
                    "iteration": iteration,
                    "tool": "search_process_vectors",
                    "status": "completed",
                    "detail": {
                        "query": plan.process_parameter_query,
                        "candidate_pair_count": len(catalog),
                        "returned_pair_count": len(vector_matches),
                        "top_k": vector_limit,
                        "embedding_model": PROCESS_EMBEDDING_MODEL,
                        "top_matches": [
                            {
                                "action_name": match.action_name,
                                "parameter_name": match.parameter_name,
                                "score": round(match.vector_score, 4),
                            }
                            for match in vector_matches[:12]
                        ],
                    },
                }
            )

            selection = self.sql_planner.select_process_keys(
                question=question,
                process_parameter_query=plan.process_parameter_query,
                catalog=selection_catalog,
                feedback=feedback,
            )
            last_selection = selection.to_dict()
            for item in selection.selected_parameters:
                if item not in selected_parameters:
                    selected_parameters.append(item)

            facts = self.process_inspector.inspect(specimen_ids, selected_parameters)
            analysis = analyze_process_performance(
                facts,
                performance_map,
                comparison_controls=plan.comparison_controls,
            )
            pair_count = int(analysis.get("numeric_pair_count") or 0)
            sufficient = _process_evidence_sufficient(plan.process_task, facts, analysis)
            iteration_status = (
                "sufficient"
                if sufficient
                else "insufficient"
                if iteration == self.max_agent_iterations
                else "retry"
            )
            self.last_agent_trace.append(
                {
                    "iteration": iteration,
                    "tool": "inspect_process_json",
                    "status": iteration_status,
                    "detail": {
                        "selected_parameters": selection.selected_parameters,
                        "accumulated_parameters": selected_parameters,
                        "fact_count": len(facts),
                        "numeric_pair_count": pair_count,
                    },
                }
            )
            if sufficient:
                break
            if pair_count == previous_pair_count and not selection.selected_parameters:
                break
            previous_pair_count = pair_count
            feedback = (
                f"Selected {selected_parameters}, yielding {len(facts)} parameter facts and {pair_count} "
                "numeric pairs sharing the same specimen_id. Evidence remains insufficient. Select missing actual action/parameter pairs from the catalog; "
                "do not repeat invalid keys."
            )

        self.last_process_analysis = {
            **analysis,
            "process_access_mode": "semantic_keys",
            "parameter_query": plan.process_parameter_query,
            "process_task": plan.process_task,
            "selected_parameters": selected_parameters,
            "selection": last_selection,
            "comparison_controls": plan.comparison_controls,
            "candidate_specimen_count": len(specimen_ids),
            "candidate_limit": self.process_candidate_limit,
            "candidate_may_be_truncated": len(specimen_ids) >= self.process_candidate_limit,
            "vector_search": {
                "enabled": self.enable_process_vectors,
                "used": True,
                "embedding_model": PROCESS_EMBEDDING_MODEL,
                "indexed_action_parameter_count": self.process_vector_store.count(),
                "matched_action_parameters": [match.to_dict() for match in vector_matches[:40]],
            },
        }
        if self.last_process_analysis["candidate_may_be_truncated"]:
            self.last_process_analysis.setdefault("warnings", []).append(
                "The candidate count reached the query limit. Statistics describe this candidate set, not untruncated results from the entire database."
            )
        facts_by_specimen: Dict[int, List[Dict[str, Any]]] = {}
        for fact in facts:
            facts_by_specimen.setdefault(fact.specimen_id, []).append(fact.to_dict())
        ordered_hits = sorted(
            hits,
            key=lambda hit: (
                0 if _hit_specimen_id(hit) in facts_by_specimen else 1,
                -float(hit.get("score", 0)),
            ),
        )
        _attach_process_results(
            ordered_hits,
            facts,
            self.last_process_analysis,
            facts_by_specimen,
        )
        return ordered_hits

    def query(self, question: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """Retrieve verified evidence and ask the model to synthesize the answer."""
        hits = self.retrieve(question, top_k=top_k)
        shared = {
            "contexts": hits,
            "query_plan": self.last_query_plan.to_dict() if self.last_query_plan else None,
            "planning_error": self.last_planning_error,
            "agent_trace": self.last_agent_trace,
            "process_analysis": self.last_process_analysis,
        }
        if not hits:
            return {
                "answer": "没有在当前焊接数据库中检索到足够相关的数据。",
                "error": None,
                **shared,
            }
        if not self.llm_enabled:
            return {
                "answer": "已完成结构化检索，但当前未配置可用的语言模型。请查看检索证据。",
                "error": "LLM is not initialized.",
                **shared,
            }

        prompt = _build_answer_prompt(question, hits, self.last_process_analysis)
        try:
            content = self._invoke_qwen_http(prompt, max_tokens=1800)
            return {"answer": content, "error": None, **shared}
        except Exception as exc:
            return {
                "answer": "回答生成失败，但结构化检索已经完成。请查看检索证据。",
                "error": str(exc),
                **shared,
            }

    def _invoke_planner_model(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 1800,
    ) -> str:
        return self._invoke_qwen_http(
            prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
        )

    def _invoke_qwen_http(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1800,
    ) -> str:
        response = requests.post(
            QWEN_API_BASE_URL.rstrip("/") + "/chat/completions",
            headers={
                "Authorization": f"Bearer {QWEN_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLM_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                        or (
                            "You are a welding data analysis assistant. Answer only from SQL results and evidence parsed from original JSON. "
                            "Do not invent processes, parameters, properties, or causal conclusions."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": max_tokens,
            },
            timeout=180,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    def get_stats(self) -> Dict[str, Any]:
        if not self.record_count:
            self.index_database()
        return {
            "database_path": self.db_path,
            "record_count": self.record_count,
            "paper_count": self.paper_count,
            "sql_planner_enabled": self.sql_planner is not None,
            "max_agent_iterations": self.max_agent_iterations,
            "process_candidate_limit": self.process_candidate_limit,
            "llm_initialized": self.llm_enabled,
            "llm_model": LLM_MODEL,
            "process_vector_enabled": self.enable_process_vectors,
            "process_vector_available": self.process_vector_store.available,
            "process_vector_model": PROCESS_EMBEDDING_MODEL,
            "process_vector_index_count": self.process_vector_store.count(),
            "retrieval_tools": [
                "execute_sql",
                "read_full_process_json",
                "search_process_vectors",
                "inspect_process_json",
            ],
        }


def _specimen_ids(hits: Sequence[Dict[str, Any]]) -> List[int]:
    result = []
    seen = set()
    for hit in hits:
        specimen_id = _hit_specimen_id(hit)
        if specimen_id is not None and specimen_id not in seen:
            seen.add(specimen_id)
            result.append(specimen_id)
    return result


def _hit_specimen_id(hit: Dict[str, Any]) -> Optional[int]:
    evidence = hit.get("metadata", {}).get("evidence", {})
    specimens = evidence.get("specimens") or []
    if specimens and specimens[0].get("specimen_id") is not None:
        return int(specimens[0]["specimen_id"])
    record_id = str(hit.get("record_id") or "")
    if record_id.startswith("specimen:"):
        return int(record_id.split(":", 1)[1])
    return None


def _performance_by_specimen(
    hits: Sequence[Dict[str, Any]],
    target_property: str,
) -> Dict[int, Dict[str, Any]]:
    result = {}
    for hit in hits:
        evidence = hit.get("metadata", {}).get("evidence", {})
        for specimen in evidence.get("specimens") or []:
            specimen_id = int(specimen["specimen_id"])
            selected = [
                prop
                for prop in specimen.get("properties") or []
                if prop.get("selected_by_sql")
                and (
                    not target_property
                    or prop.get("property_name") == target_property
                )
            ]
            if not selected:
                continue
            prop = max(
                selected,
                key=lambda item: (
                    float(item["average_value"])
                    if item.get("average_value") is not None
                    else float("-inf")
                ),
            )
            item = {
                "property": prop.get("property_name"),
                "numeric_value": prop.get("average_value"),
                "unit": prop.get("property_unit") or "",
                "base_metal": evidence.get("base_metal") or "",
                "filler_metal": evidence.get("filler_metal") or "",
                "welding_method": evidence.get("welding_method") or "",
                "test_area": specimen.get("test_area") or "",
                "test_method": specimen.get("test_method") or "",
            }
            for related in specimen.get("properties") or []:
                property_name = related.get("property_name")
                if property_name and property_name not in item:
                    item[property_name] = related.get("average_value")
            result[specimen_id] = item
    return result


def _process_evidence_sufficient(
    process_task: str,
    facts: Sequence[ProcessParameterFact],
    analysis: Dict[str, Any],
) -> bool:
    if process_task == "return":
        return bool(facts)
    if process_task == "compare":
        return any(
            int(group.get("specimen_count") or 0) >= 3
            for group in analysis.get("groups") or []
        )
    if process_task == "filter":
        return int(analysis.get("numeric_pair_count") or 0) >= 3
    return True


def _attach_process_results(
    hits: Sequence[Dict[str, Any]],
    facts: Sequence[ProcessParameterFact],
    analysis: Dict[str, Any],
    facts_by_specimen: Dict[int, List[Dict[str, Any]]],
) -> None:
    for index, hit in enumerate(hits):
        evidence = hit.get("metadata", {}).get("evidence")
        if not evidence:
            continue
        for specimen in evidence.get("specimens") or []:
            specimen_id = int(specimen["specimen_id"])
            specimen["process_parameters"] = facts_by_specimen.get(specimen_id, [])
        if index == 0:
            evidence["process_analysis"] = analysis
        hit["context"] = json.dumps(evidence, ensure_ascii=False, default=str, indent=2)


def _build_answer_prompt(
    question: str,
    hits: List[Dict[str, Any]],
    process_analysis: Optional[Dict[str, Any]],
) -> str:
    evidence = []
    for rank, hit in enumerate(hits, start=1):
        structured = hit.get("metadata", {}).get("evidence")
        if structured:
            compact = dict(structured)
            compact.pop("process_analysis", None)
            evidence.append(
                {
                    "rank": rank,
                    "channels": hit.get("channels", []),
                    "query_plan": hit.get("metadata", {}).get("query_plan"),
                    **compact,
                }
            )
    analysis_json = json.dumps(process_analysis or {}, ensure_ascii=False, default=str)
    evidence_json = json.dumps(evidence, ensure_ascii=False, default=str)
    if len(evidence_json) > 45000:
        evidence_json = evidence_json[:45000]
    return (
        "Answer strictly from SQL results and parsed original process JSON. Vector similarity "
        "is for candidate retrieval only, not evidence for parameter values or conclusions.\n"
        "1. Process parameters and properties must belong to the same specimen_id.\n"
        "2. Distinguish root, fill, and cap passes, internal/external welding, and multiple wires. Do not merge them arbitrarily.\n"
        "3. For process-parameter comparisons, prioritize stratified statistics, sample counts, and units in process_analysis.\n"
        "4. Describe observed differences and associations only; do not present correlation as causation.\n"
        "5. Explicitly state small sample sizes, unknown units, and differences in control conditions.\n"
        "6. Cite source papers and preserve original ranges and replicate-value conventions.\n"
        "7. For process_access_mode=full_json, follow the SQL ranking and present the record's complete "
        "process hierarchy. Do not replace the record based on whether a parameter is available.\n\n"
        f"User question: {question}\n\n"
        f"Runtime process-property analysis: {analysis_json}\n\n"
        f"Structured evidence: {evidence_json}"
    )
