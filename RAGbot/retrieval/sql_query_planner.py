"""LLM planner for iterative, read-only SQL Agentic RAG."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence


ALLOWED_TABLES = {"property_measurements", "specimen_records", "papers"}
ALLOWED_PROPERTY_TARGETS = {"specimen", "base_metal", "filler_metal"}
ALLOWED_PROCESS_TASKS = {"none", "return", "filter", "compare"}
ALLOWED_PROCESS_ACCESS_MODES = {"none", "full_json", "semantic_keys"}
FORBIDDEN_SQL = re.compile(
    r"\b(?:insert|update|delete|drop|alter|create|replace|attach|detach|pragma|"
    r"vacuum|reindex|analyze|load_extension|readfile|writefile|pragma_|"
    r"savepoint|release|rollback|commit)\b",
    re.IGNORECASE,
)
TABLE_REFERENCE_RE = re.compile(
    r"\b(?:from|join)\s+[\"`\[]?([a-zA-Z_][a-zA-Z0-9_]*)",
    re.IGNORECASE,
)
PARAMETER_RE = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)")
STRING_LITERAL_RE = re.compile(r"'(?:''|[^'])*'")
CTE_NAME_RE = re.compile(
    r"(?:\bwith\b|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+as\s*\(",
    re.IGNORECASE,
)


class SQLPlanError(ValueError):
    """Raised when an LLM-generated retrieval plan is unsafe or malformed."""


@dataclass
class SQLQueryPlan:
    sql: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    target_property: str = ""
    property_target: str = "specimen"
    process_access_mode: str = "none"
    process_parameter_query: str = ""
    process_task: str = "none"
    comparison_controls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProcessKeySelection:
    selected_parameters: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WeldingSQLPlanner:
    """Plan candidate SQL and select process keys discovered at query time."""

    def __init__(
        self,
        invoke_llm: Callable[..., str],
        schema_context: str,
        max_rows: int = 120,
    ):
        self.invoke_llm = invoke_llm
        self.schema_context = schema_context
        self.max_rows = max_rows

    def plan(self, question: str, limit: Optional[int] = None) -> SQLQueryPlan:
        requested_limit = max(1, min(int(limit or self.max_rows), self.max_rows))
        base_prompt = _planner_prompt(question, requested_limit, self.schema_context)
        validation_error = ""
        for _ in range(2):
            prompt = base_prompt
            if validation_error:
                prompt += (
                    "\n\nThe previous plan failed safety validation: "
                    + validation_error
                    + "\nCorrect the plan and return the complete JSON object."
                )
            content = self.invoke_llm(
                prompt,
                system_prompt=(
                    "You are an iterative SQL agent for a welding relational database. Generate candidate SQL from the actual schema. "
                    "Declare a JSON inspection task when process parameters are needed. Return only JSON, without Markdown or reasoning."
                ),
                max_tokens=1900,
            )
            try:
                plan = _plan_from_payload(_extract_json_object(content))
                validate_sql_plan(plan)
                return plan
            except SQLPlanError as exc:
                validation_error = str(exc)
        raise SQLPlanError(validation_error or "Agent failed to produce a valid retrieval plan")

    def select_process_keys(
        self,
        question: str,
        process_parameter_query: str,
        catalog: Sequence[Dict[str, Any]],
        feedback: str = "",
    ) -> ProcessKeySelection:
        prompt = _process_key_prompt(
            question=question,
            process_parameter_query=process_parameter_query,
            catalog=catalog,
            feedback=feedback,
        )
        content = self.invoke_llm(
            prompt,
            system_prompt=(
                "You review vector-retrieved welding process candidates. Select only existing "
                "action_name and parameter_name pairs from the supplied catalog. Do not rewrite or invent them. Return only JSON."
            ),
            max_tokens=1400,
        )
        payload = _extract_json_object(content)
        available = {
            (str(item.get("action_name") or ""), str(item.get("parameter_name") or ""))
            for item in catalog
        }
        selected = []
        for item in payload.get("selected_parameters") or []:
            if not isinstance(item, dict):
                continue
            pair = (
                str(item.get("action_name") or ""),
                str(item.get("parameter_name") or ""),
            )
            normalized = {"action_name": pair[0], "parameter_name": pair[1]}
            if pair in available and normalized not in selected:
                selected.append(normalized)
        return ProcessKeySelection(selected_parameters=selected)


def validate_sql_plan(plan: SQLQueryPlan) -> None:
    if plan.property_target not in ALLOWED_PROPERTY_TARGETS:
        raise SQLPlanError(f"Unsupported property_target: {plan.property_target}")
    if plan.process_task not in ALLOWED_PROCESS_TASKS:
        raise SQLPlanError(f"Unsupported process_task: {plan.process_task}")
    if plan.process_access_mode not in ALLOWED_PROCESS_ACCESS_MODES:
        raise SQLPlanError(
            f"Unsupported process_access_mode: {plan.process_access_mode}"
        )
    if plan.process_access_mode == "none":
        if plan.process_task != "none" or plan.process_parameter_query.strip():
            raise SQLPlanError("none process access cannot contain a process task or query")
    elif plan.process_access_mode == "full_json":
        if plan.process_task != "return" or plan.process_parameter_query.strip():
            raise SQLPlanError("full_json requires process_task=return and an empty process query")
    else:
        if not plan.process_parameter_query.strip():
            raise SQLPlanError(
                "semantic_keys process access requires process_parameter_query"
            )
        if plan.process_task == "none":
            raise SQLPlanError("semantic_keys process access requires a process_task")

    sql = plan.sql.strip()
    if sql.endswith(";"):
        sql = sql[:-1].rstrip()
    if not re.match(r"^(?:select|with)\b", sql, re.IGNORECASE):
        raise SQLPlanError("SQL must start with SELECT or WITH")
    if ";" in sql:
        raise SQLPlanError("Only one SQL statement is allowed")
    if "--" in sql or "/*" in sql or "*/" in sql:
        raise SQLPlanError("SQL comments are not allowed")
    if FORBIDDEN_SQL.search(sql):
        raise SQLPlanError("SQL contains a forbidden operation")
    if "?" in sql:
        raise SQLPlanError("Use named parameters instead of positional parameters")
    if STRING_LITERAL_RE.search(sql):
        raise SQLPlanError("All SQL string values and LIKE patterns must use named parameters")
    if re.search(r"\bjson_(?:tree|each|extract)\s*\(", sql, re.IGNORECASE):
        raise SQLPlanError("Initial SQL must leave welding_params inspection to the JSON tool")

    referenced_tables = {name.lower() for name in TABLE_REFERENCE_RE.findall(sql)}
    cte_names = {name.lower() for name in CTE_NAME_RE.findall(sql)}
    unknown_tables = referenced_tables.difference(ALLOWED_TABLES).difference(cte_names)
    if unknown_tables:
        raise SQLPlanError(f"SQL references non-whitelisted tables: {sorted(unknown_tables)}")
    if not referenced_tables.intersection({"property_measurements", "specimen_records"}):
        raise SQLPlanError("SQL must query the normalized welding dataset")

    placeholders = set(PARAMETER_RE.findall(sql))
    missing = placeholders.difference(plan.parameters)
    extra = set(plan.parameters).difference(placeholders)
    if missing:
        raise SQLPlanError(f"Missing SQL parameters: {sorted(missing)}")
    if extra:
        raise SQLPlanError(f"Unused SQL parameters: {sorted(extra)}")
    for key, value in plan.parameters.items():
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise SQLPlanError(f"Parameter {key} must be a scalar value")

    lowered = sql.lower()
    if not all(alias in lowered for alias in ("property_id", "specimen_id")):
        raise SQLPlanError("SQL must return property_id and specimen_id")
    if plan.target_property and not all(
        column in lowered for column in ("property_name", "property_target")
    ):
        raise SQLPlanError(
            "Performance SQL must filter property_name and property_target"
        )
    plan.sql = sql


def _plan_from_payload(payload: Dict[str, Any]) -> SQLQueryPlan:
    controls = payload.get("comparison_controls") or []
    if not isinstance(controls, list):
        raise SQLPlanError("comparison_controls must be a list")
    parameters = payload.get("parameters") or {}
    if not isinstance(parameters, dict):
        raise SQLPlanError("parameters must be an object")
    return SQLQueryPlan(
        sql=str(payload.get("sql") or "").strip(),
        parameters=parameters,
        target_property=str(payload.get("target_property") or ""),
        property_target=str(payload.get("property_target") or "specimen"),
        process_access_mode=str(payload.get("process_access_mode") or "none").lower(),
        process_parameter_query=str(payload.get("process_parameter_query") or ""),
        process_task=str(payload.get("process_task") or "none").lower(),
        comparison_controls=[str(value) for value in controls],
    )


def _extract_json_object(content: str) -> Dict[str, Any]:
    try:
        payload = json.loads(str(content).strip())
    except json.JSONDecodeError as exc:
        raise SQLPlanError("Planner did not return a valid JSON object") from exc
    if not isinstance(payload, dict):
        raise SQLPlanError("Planner output must be a JSON object")
    return payload


def _planner_prompt(question: str, limit: int, schema_context: str) -> str:
    return f"""
Plan the initial candidate SQL query using the actual database schema. Do not use vector
retrieval for properties or papers, or use paper abstracts or full text. Only specific
process-parameter concepts may use parameter-key vector retrieval within the SQL candidate set.

Database schema and data semantics:
{schema_context}

Relationship semantics:
1. papers.paper_id = specimen_records.paper_id.
2. specimen_records.specimen_id = property_measurements.specimen_id.
3. Each specimen_records row describes a specimen under specific processing, test methods,
   test conditions, and testing regions.
4. Only property_target='specimen' denotes properties of the specimen associated with the
   current welding process. base_metal and filler_metal denote reference material properties.
   target_id identifies a base-metal or filler-metal slot, not a replicate specimen.
5. welding_params contains valid JSON with inconsistent keys, nesting, and units. Do not guess
   JSON paths in the initial SQL. Select one of these process access modes:
   - none: only structured fields are needed; do not read process JSON.
   - full_json: the question requests the complete process, all parameters, or the processing
     sequence for one or a few ranked records. Read the full JSON directly, without vector
     retrieval or changes to the SQL ranking.
   - semantic_keys: the question requests specific parameters such as heat input, current,
     voltage, travel speed, or preheat temperature, or filters/compares records by them.
     Retrieve candidate process keys by vectors, then parse exact values from the original JSON.
6. Use only numeric fields present in the live schema. property_measurements stores raw_value
   and average_value. average_value directly copies source-table averages only for tensile
   strength, yield strength, elongation, and impact energy. Hardness and other data without an
   average column retain raw text only. Do not calculate arbitrary averages in SQL.
7. papers.abstract is optional metadata only. Do not use it to retrieve or rank properties or
   processes, or as evidence in an answer.

Planning requirements:
1. SQL selects candidate specimens using structured material, welding method, testing region,
   test condition, and property fields only.
2. Return m.property_id AS property_id and m.specimen_id AS specimen_id.
3. Use named parameters for every string and LIKE pattern. No single-quoted string literals in SQL.
4. Property queries must use property_name and property_target.
5. Process-parameter comparisons must cover comparable candidates, not just the highest record.
   Use at most :limit={limit}. Ordinary maximum/minimum queries may use a smaller LIMIT.
6. List fields to control or stratify in comparison_controls, such as base_material,
   welding_method, testing_area, impact test temperature, and specimen dimensions.
   Do not invent conditions absent from the database.
7. Use full_json for the complete process associated with the highest property value;
   semantic_keys for property differences at different heat inputs; and none when returning
   only structured fields such as welding_method.
8. Return only the fields declared below. Retrieval settings, numeric conventions, process
   inspection, and evidence expansion are controlled by the program; do not add status fields.

Output JSON:
{{
  "sql": "...",
  "parameters": {{"...": "..."}},
  "target_property": "canonical property name; empty string for non-property queries",
  "property_target": "specimen|base_metal|filler_metal",
  "process_access_mode": "none|full_json|semantic_keys",
  "process_parameter_query": "specific parameter concept for semantic_keys only; otherwise empty",
  "process_task": "none|return|filter|compare",
  "comparison_controls": ["field name"]
}}

User question: {question}
""".strip()


def _process_key_prompt(
    question: str,
    process_parameter_query: str,
    catalog: Sequence[Dict[str, Any]],
    feedback: str,
) -> str:
    catalog_json = json.dumps(list(catalog), ensure_ascii=False, default=str)
    return f"""
User question: {question}
Target process-parameter concept: {process_parameter_query}

The following catalog contains actual leaf nodes from candidate specimens' welding_params
JSON, retrieved by joint vector similarity of action_name and parameter_name. Review and
select complete process-action/parameter-name pairs that match the target concept.
Consider synonyms, welding stages, internal/external welding, and multiple wires. Do not
select unrelated parameters just because their numeric formats are similar. Vector scores
rank candidates only and are not evidence for the final answer.

Previous feedback: {feedback or 'None'}

Parameter catalog: {catalog_json}

Output JSON:
{{
  "selected_parameters": [
    {{"action_name": "exact catalog value", "parameter_name": "exact catalog value"}}
  ]
}}
""".strip()
