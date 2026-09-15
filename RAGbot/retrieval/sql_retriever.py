"""Execute validated SQL plans and expand specimen/property evidence."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .sql_query_planner import SQLPlanError, SQLQueryPlan, validate_sql_plan


@dataclass
class SQLExecutionResult:
    hits: List[Dict[str, Any]]
    candidate_count: int


class WeldingSQLRetriever:
    def __init__(self, db_path: str, max_rows: int = 12):
        self.db_path = Path(db_path)
        self.max_rows = max_rows

    def describe_schema(self) -> str:
        """Build compact context directly from the specimen-centric database."""
        if not self.db_path.exists():
            return "Database file does not exist."
        conn = self._connect_read_only()
        conn.row_factory = sqlite3.Row
        try:
            lines = []
            schema_columns: Dict[str, set[str]] = {}
            for table in ("papers", "specimen_records", "property_measurements"):
                columns = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
                schema_columns[table] = {str(row["name"]) for row in columns}
                column_text = ", ".join(
                    f"{row['name']} {row['type'] or 'TEXT'}" for row in columns
                )
                count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                lines.append(f"{table} ({count} rows): {column_text}")
                for key in conn.execute(f'PRAGMA foreign_key_list("{table}")'):
                    lines.append(
                        f"  FK {table}.{key['from']} -> {key['table']}.{key['to']}"
                    )

            samples = (
                ("property_measurements", "property_target"),
                ("property_measurements", "property_name"),
                ("specimen_records", "welding_method"),
                ("specimen_records", "test_area"),
                ("specimen_records", "base_metal"),
            )
            for table, column in samples:
                if column not in schema_columns.get(table, set()):
                    continue
                values = conn.execute(
                    f'SELECT DISTINCT "{column}" FROM "{table}" '
                    f'WHERE "{column}" IS NOT NULL AND trim("{column}") <> \'\' LIMIT 40'
                ).fetchall()
                lines.append(
                    f"Observed {table}.{column} values: "
                    f"{[_compact_schema_value(row[0]) for row in values]}"
                )
            return "\n".join(lines)
        finally:
            conn.close()

    def execute(
        self,
        plan: SQLQueryPlan,
        expected_property: str = "",
        expected_target: str = "specimen",
    ) -> SQLExecutionResult:
        validate_sql_plan(plan)
        if not self.db_path.exists():
            raise SQLPlanError(f"Database not found: {self.db_path}")

        parameters = dict(plan.parameters)
        if "limit" in parameters:
            parameters["limit"] = max(1, min(int(parameters["limit"]), self.max_rows))
        parameters["__max_rows"] = self.max_rows
        verification_join = ""
        if expected_property:
            parameters["__expected_property"] = expected_property
            parameters["__expected_target"] = expected_target
            verification_join = """
                JOIN property_measurements AS verified_property
                  ON verified_property.property_id = planned_candidates.property_id
                 AND verified_property.specimen_id = planned_candidates.specimen_id
                WHERE verified_property.property_name = :__expected_property
                  AND verified_property.property_target = :__expected_target
            """
        wrapped_sql = (
            f"SELECT planned_candidates.* FROM ({plan.sql}) AS planned_candidates "
            f"{verification_join} LIMIT :__max_rows"
        )

        conn = self._connect_read_only()
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("EXPLAIN QUERY PLAN " + wrapped_sql, parameters).fetchall()
            candidate_rows = conn.execute(wrapped_sql, parameters).fetchall()
            property_ids = _ordered_unique(
                int(row["property_id"])
                for row in candidate_rows
                if row["property_id"] is not None
            )
            specimen_ids = _ordered_unique(
                int(row["specimen_id"])
                for row in candidate_rows
                if row["specimen_id"] is not None
            )
            hits = self._expand_evidence(conn, plan, specimen_ids, property_ids)
        finally:
            conn.close()
        return SQLExecutionResult(hits=hits, candidate_count=len(candidate_rows))

    def _connect_read_only(self) -> sqlite3.Connection:
        uri = self.db_path.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=10)
        conn.execute("PRAGMA query_only = ON")
        return conn

    def _expand_evidence(
        self,
        conn: sqlite3.Connection,
        plan: SQLQueryPlan,
        specimen_ids: List[int],
        property_ids: List[int],
    ) -> List[Dict[str, Any]]:
        if not specimen_ids:
            return []
        specimen_ids = specimen_ids[: self.max_rows]
        specimen_marks = ",".join("?" for _ in specimen_ids)
        property_marks = ",".join("?" for _ in property_ids) if property_ids else "NULL"
        rows = conn.execute(
            f"""
            SELECT
                s.specimen_id,
                s.paper_id,
                s.base_metal,
                s.filler_metal,
                s.welding_method,
                s.welding_params,
                s.test_method,
                s.test_condition,
                s.test_area,
                p.title,
                p.doi,
                m.property_id,
                m.target_id,
                m.property_target,
                m.property_name,
                m.raw_value,
                m.average_value,
                m.property_unit
            FROM specimen_records AS s
            JOIN property_measurements AS m ON m.specimen_id = s.specimen_id
            LEFT JOIN papers AS p ON p.paper_id = s.paper_id
            WHERE s.specimen_id IN ({specimen_marks})
              AND (m.property_target = 'specimen' OR m.property_id IN ({property_marks}))
            """,
            [*specimen_ids, *property_ids],
        ).fetchall()

        grouped: Dict[int, Dict[str, Any]] = {}
        selected_ids = set(property_ids)
        for row in rows:
            specimen_id = int(row["specimen_id"])
            item = grouped.setdefault(
                specimen_id,
                {
                    "specimen_id": specimen_id,
                    "paper_id": row["paper_id"],
                    "base_metal": row["base_metal"] or "",
                    "filler_metal": row["filler_metal"] or "",
                    "welding_method": row["welding_method"] or "",
                    "welding_params": _decode_json(row["welding_params"]),
                    "test_method": row["test_method"] or "",
                    "test_condition": _decode_json(row["test_condition"]),
                    "test_area": row["test_area"] or "",
                    "title": row["title"] or "",
                    "doi": row["doi"] or "",
                    "properties": [],
                },
            )
            item["properties"].append(
                {
                    "property_id": row["property_id"],
                    "property_name": row["property_name"],
                    "property_target": row["property_target"],
                    "target_id": row["target_id"],
                    "raw_value": row["raw_value"],
                    "average_value": row["average_value"],
                    "property_unit": row["property_unit"] or "",
                    "selected_by_sql": row["property_id"] in selected_ids,
                }
            )

        order = {specimen_id: index for index, specimen_id in enumerate(specimen_ids)}
        hits = []
        for specimen_id in specimen_ids:
            item = grouped.get(specimen_id)
            if not item:
                continue
            specimen = {
                "specimen_id": specimen_id,
                "test_method": item["test_method"],
                "test_condition": item["test_condition"],
                "test_area": item["test_area"],
                "properties": item["properties"],
            }
            evidence = {
                "record_id": f"specimen:{specimen_id}",
                "paper_id": item["paper_id"],
                "paper": item["title"],
                "doi": item["doi"],
                "base_metal": item["base_metal"],
                "filler_metal": item["filler_metal"],
                "welding_method": item["welding_method"],
                "welding_params": item["welding_params"],
                "specimens": [specimen],
            }
            rank = order[specimen_id] + 1
            hits.append(
                {
                    "record_id": evidence["record_id"],
                    "score": float(self.max_rows - rank + 1),
                    "channels": ["sql"],
                    "context": json.dumps(evidence, ensure_ascii=False, default=str, indent=2),
                    "metadata": {
                        "paper_id": item["paper_id"],
                        "specimen_id": specimen_id,
                        "welding_method": item["welding_method"],
                        "base_metal": item["base_metal"],
                        "query_plan": plan.to_dict(),
                        "evidence": evidence,
                    },
                }
            )
        return hits


def _ordered_unique(values: Any) -> List[int]:
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _compact_schema_value(value: Any, max_length: int = 80) -> str:
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return text if len(text) <= max_length else text[: max_length - 3] + "..."


def _decode_json(value: Any) -> Any:
    if value in (None, ""):
        return {}
    if isinstance(value, (dict, list)):
        return value
    return json.loads(str(value))
