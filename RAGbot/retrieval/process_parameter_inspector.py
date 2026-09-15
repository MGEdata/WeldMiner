"""Schema-on-read inspection and analysis of welding process JSON."""
from __future__ import annotations

import math
import re
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .measurement_parser import parse_measurement_cell


@dataclass
class ProcessParameterFact:
    specimen_id: int
    json_path: str
    action_name: str
    parameter_name: str
    raw_value: str
    numeric_value: Optional[float]
    value_min: Optional[float]
    value_max: Optional[float]
    unit_raw: str
    canonical_value: Optional[float]
    canonical_min: Optional[float]
    canonical_max: Optional[float]
    canonical_unit: str
    parsing_policy: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProcessParameterInspector:
    """Inspect selected observation JSON without creating a persistent parameter table."""

    def __init__(self, db_path: str, max_observations: int = 200):
        self.db_path = Path(db_path)
        self.max_observations = max_observations

    def discover_keys(
        self,
        specimen_ids: Sequence[int],
        max_keys: int = 160,
    ) -> List[Dict[str, Any]]:
        leaves = self._load_leaves(specimen_ids)
        grouped: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for leaf in leaves:
            action_name = str(leaf["action_name"])
            parameter_name = str(leaf["parameter_name"])
            key = (action_name, parameter_name)
            item = grouped.setdefault(
                key,
                {
                    "action_name": action_name,
                    "parameter_name": parameter_name,
                    "count": 0,
                    "specimen_count": set(),
                    "sample_values": [],
                    "sample_paths": [],
                },
            )
            item["count"] += 1
            item["specimen_count"].add(leaf["specimen_id"])
            _append_unique(item["sample_values"], str(leaf["raw_value"]), 3)
            _append_unique(item["sample_paths"], str(leaf["json_path"]), 3)

        catalog = []
        for item in grouped.values():
            catalog.append(
                {
                    **item,
                    "specimen_count": len(item["specimen_count"]),
                }
            )
        catalog.sort(
            key=lambda item: (item["specimen_count"], item["count"]),
            reverse=True,
        )
        return catalog[:max_keys]

    def inspect(
        self,
        specimen_ids: Sequence[int],
        selected_parameters: Iterable[Dict[str, str]],
    ) -> List[ProcessParameterFact]:
        selected_pairs = {
            (
                str(item.get("action_name") or ""),
                str(item.get("parameter_name") or ""),
            )
            for item in selected_parameters
            if str(item.get("parameter_name") or "").strip()
        }
        if not selected_pairs:
            return []
        facts = []
        for leaf in self._load_leaves(specimen_ids):
            pair = (str(leaf["action_name"]), str(leaf["parameter_name"]))
            if pair not in selected_pairs:
                continue
            facts.append(_parse_fact(leaf))
        return facts

    def inspect_all(
        self,
        specimen_ids: Sequence[int],
    ) -> List[ProcessParameterFact]:
        """Parse every non-empty leaf from the selected observations' process JSON."""
        return [_parse_fact(leaf) for leaf in self._load_leaves(specimen_ids)]

    def _load_leaves(self, specimen_ids: Sequence[int]) -> List[Dict[str, Any]]:
        ids = _ordered_unique_ints(specimen_ids)[: self.max_observations]
        if not ids or not self.db_path.exists():
            return []
        placeholders = ",".join("?" for _ in ids)
        sql = f"""
            SELECT
                s.specimen_id AS specimen_id,
                j.fullkey AS json_path,
                CAST(j.key AS TEXT) AS parameter_name,
                CAST(j.atom AS TEXT) AS raw_value
            FROM specimen_records s,
                 json_tree(NULLIF(s.welding_params, '')) AS j
            WHERE s.specimen_id IN ({placeholders})
              AND j.atom IS NOT NULL
              AND j.key IS NOT NULL
              AND TRIM(CAST(j.key AS TEXT)) <> ''
              AND TRIM(CAST(j.atom AS TEXT)) <> ''
        """
        uri = self.db_path.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        try:
            leaves = [dict(row) for row in conn.execute(sql, ids).fetchall()]
            for leaf in leaves:
                leaf["action_name"] = _process_context(str(leaf.get("json_path") or ""))
            return leaves
        finally:
            conn.close()


def analyze_process_performance(
    facts: Sequence[ProcessParameterFact],
    performance_by_specimen: Dict[int, Dict[str, Any]],
    comparison_controls: Sequence[str] = (),
    max_pairs: int = 80,
) -> Dict[str, Any]:
    pairs = []
    for fact in facts:
        performance = performance_by_specimen.get(fact.specimen_id)
        parameter_value = (
            fact.canonical_value
            if fact.canonical_value is not None
            else fact.numeric_value
        )
        performance_value = performance.get("numeric_value") if performance else None
        if parameter_value is None or performance_value is None:
            continue
        unit = fact.canonical_unit or fact.unit_raw or "unit_not_identified"
        pairs.append(
            {
                "specimen_id": fact.specimen_id,
                "action_name": fact.action_name,
                "parameter_name": fact.parameter_name,
                "parameter_value": parameter_value,
                "parameter_min": fact.canonical_min if fact.canonical_unit else fact.value_min,
                "parameter_max": fact.canonical_max if fact.canonical_unit else fact.value_max,
                "parameter_unit": unit,
                "parameter_raw_value": fact.raw_value,
                "performance_property": performance.get("property"),
                "performance_value": performance_value,
                "performance_unit": performance.get("unit") or "",
                "control_values": {
                    control: performance.get(control)
                    for control in comparison_controls
                    if performance.get(control) not in (None, "")
                },
            }
        )

    groups: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
    for pair in pairs:
        controls_key = repr(sorted(pair["control_values"].items()))
        key = (
            pair["parameter_unit"],
            pair["action_name"] or "unspecified",
            controls_key,
        )
        groups.setdefault(key, []).append(pair)

    summaries = []
    for (unit, context, _), records in groups.items():
        parameter_values = [float(item["parameter_value"]) for item in records]
        performance_values = [float(item["performance_value"]) for item in records]
        summaries.append(
            {
                "action_name": context,
                "control_values": records[0]["control_values"],
                "parameter_unit": unit,
                "pair_count": len(records),
                "specimen_count": len({item["specimen_id"] for item in records}),
                "parameter_min": min(parameter_values),
                "parameter_max": max(parameter_values),
                "performance_mean": sum(performance_values) / len(performance_values),
                "performance_min": min(performance_values),
                "performance_max": max(performance_values),
                "spearman_correlation": _spearman(parameter_values, performance_values),
                "equal_count_bins": _equal_count_bins(records, bin_count=3),
            }
        )
    summaries.sort(key=lambda item: item["pair_count"], reverse=True)

    return {
        "fact_count": len(facts),
        "numeric_pair_count": len(pairs),
        "paired_specimen_count": len({pair["specimen_id"] for pair in pairs}),
        "groups": summaries,
        "paired_records": pairs[:max_pairs],
        "warnings": _analysis_warnings(facts, pairs, summaries),
    }


def _parse_fact(leaf: Dict[str, Any]) -> ProcessParameterFact:
    name = str(leaf.get("parameter_name") or "")
    raw_value = str(leaf.get("raw_value") or "")
    parsed = parse_measurement_cell(raw_value)
    unit_raw = _extract_unit(name + " " + raw_value)
    factor, canonical_unit = _unit_conversion(unit_raw)

    def convert(value: Optional[float]) -> Optional[float]:
        return value * factor if value is not None and factor is not None else None

    return ProcessParameterFact(
        specimen_id=int(leaf["specimen_id"]),
        json_path=str(leaf.get("json_path") or ""),
        action_name=str(leaf.get("action_name") or ""),
        parameter_name=name,
        raw_value=raw_value,
        numeric_value=parsed.numeric_for_ranking,
        value_min=parsed.value_min,
        value_max=parsed.value_max,
        unit_raw=unit_raw,
        canonical_value=convert(parsed.numeric_for_ranking),
        canonical_min=convert(parsed.value_min),
        canonical_max=convert(parsed.value_max),
        canonical_unit=canonical_unit,
        parsing_policy=parsed.aggregation_policy,
    )


def _extract_unit(text: str) -> str:
    normalized = (
        text.replace("−", "-")
        .replace("⁻", "-")
        .replace("¹", "1")
        .replace("²", "2")
        .replace("·", "")
    )
    parenthesized = re.findall(r"/\s*\(([^()]*)\)", normalized)
    if parenthesized:
        return parenthesized[-1].strip()
    direct = re.findall(
        r"\b(?:kJ|KJ|J)\s*(?:/|\\cdot)?\s*(?:mm|cm|m|min)(?:\^?\{?-?[12]\}?)?",
        normalized,
        flags=re.IGNORECASE,
    )
    return direct[-1].replace(" ", "") if direct else ""


def _unit_conversion(unit: str) -> Tuple[Optional[float], str]:
    text = unit.lower().replace(" ", "").replace("·", "")
    text = text.replace("^{-1}", "-1").replace("^(-1)", "-1")
    text = text.replace("^−1", "-1").replace("⁻¹", "-1")
    text = text.replace("-¹", "-1").replace("−¹", "-1")
    text = text.replace("-1", "")
    conversions = {
        "kj/mm": 1.0,
        "kjmm": 1.0,
        "kj/cm": 0.1,
        "kjcm": 0.1,
        "j/mm": 0.001,
        "jmm": 0.001,
        "j/cm": 0.0001,
        "jcm": 0.0001,
        "kj/m": 0.001,
        "kjm": 0.001,
        "j/m": 0.000001,
        "jm": 0.000001,
    }
    factor = conversions.get(text)
    return (factor, "kJ/mm") if factor is not None else (None, "")


def _process_context(json_path: str) -> str:
    quoted = re.findall(r'\."([^"]+)"', json_path)
    if len(quoted) >= 2:
        return quoted[-2]
    plain = [part for part in re.split(r"\.|\[\d+\]", json_path) if part and part != "$"]
    return plain[-2] if len(plain) >= 2 else ""


def _equal_count_bins(records: Sequence[Dict[str, Any]], bin_count: int) -> List[Dict[str, Any]]:
    ordered = sorted(records, key=lambda item: float(item["parameter_value"]))
    if len(ordered) < bin_count:
        return []
    bins = []
    for index in range(bin_count):
        start = math.floor(index * len(ordered) / bin_count)
        end = math.floor((index + 1) * len(ordered) / bin_count)
        chunk = ordered[start:end]
        if not chunk:
            continue
        parameters = [float(item["parameter_value"]) for item in chunk]
        performances = [float(item["performance_value"]) for item in chunk]
        bins.append(
            {
                "bin": index + 1,
                "count": len(chunk),
                "parameter_min": min(parameters),
                "parameter_max": max(parameters),
                "performance_mean": sum(performances) / len(performances),
                "performance_min": min(performances),
                "performance_max": max(performances),
            }
        )
    return bins


def _spearman(x_values: Sequence[float], y_values: Sequence[float]) -> Optional[float]:
    if len(x_values) < 3 or len(set(x_values)) < 2 or len(set(y_values)) < 2:
        return None
    x_ranks = _ranks(x_values)
    y_ranks = _ranks(y_values)
    x_mean = sum(x_ranks) / len(x_ranks)
    y_mean = sum(y_ranks) / len(y_ranks)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_ranks, y_ranks))
    denominator = math.sqrt(
        sum((x - x_mean) ** 2 for x in x_ranks)
        * sum((y - y_mean) ** 2 for y in y_ranks)
    )
    return numerator / denominator if denominator else None


def _ranks(values: Sequence[float]) -> List[float]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][1] == ordered[index][1]:
            end += 1
        average_rank = (index + 1 + end) / 2
        for position in range(index, end):
            ranks[ordered[position][0]] = average_rank
        index = end
    return ranks


def _analysis_warnings(
    facts: Sequence[ProcessParameterFact],
    pairs: Sequence[Dict[str, Any]],
    summaries: Sequence[Dict[str, Any]],
) -> List[str]:
    warnings = []
    if not facts:
        warnings.append("No agent-selected process parameter keys were found in the candidate observations.")
    if facts and not pairs:
        warnings.append("Process parameters cannot be numerically paired with target properties sharing the same specimen_id.")
    if any(not fact.unit_raw for fact in facts):
        warnings.append("Some process parameters have unknown units and were excluded from statistics for normalized units.")
    if len({summary["parameter_unit"] for summary in summaries}) > 1:
        warnings.append("Some parameter units cannot be reconciled; statistics are grouped by unit.")
    if any(summary["specimen_count"] < 3 for summary in summaries):
        warnings.append("Some groups contain fewer than three samples and support descriptive evidence only.")
    return warnings


def _ordered_unique_ints(values: Sequence[int]) -> List[int]:
    seen = set()
    result = []
    for value in values:
        number = int(value)
        if number not in seen:
            seen.add(number)
            result.append(number)
    return result


def _append_unique(target: List[str], value: str, limit: int) -> None:
    if value not in target and len(target) < limit:
        target.append(value)
