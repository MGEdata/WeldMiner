"""
Parse measurement cells that may contain parallel specimens or reported averages.

The parser keeps the original cell text for evidence, while exposing normalized
numbers for ranking, filtering, and statistics in RAG.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


SOURCE_ONLY_RE = re.compile(
    r"^\s*(?:fig(?:ure)?|table|tab\.?|图|表)\s*\.?\s*\d+[a-zA-Z]?\s*$",
    re.IGNORECASE,
)

NUMBER_RE = re.compile(
    r"""
    [-+]?
    (?:
        \d+(?:\.\d*)?
        |
        \.\d+
    )
    (?:
        \s*
        (?:
            [eE]
            |
            [×xX]\s*10\s*(?:\^|\*\*)?\s*\{?
        )
        \s*[-+]?\d+\}?
    )?
    """,
    re.VERBOSE,
)

AVERAGE_LABEL_RE = re.compile(r"\b(?:average|avg|mean)\b|平均|均值", re.IGNORECASE)
PARALLEL_LABEL_RE = re.compile(r"\b(?:parallel|replicate|replicates)\b|平行|重复", re.IGNORECASE)
RANGE_SEP_RE = re.compile(r"\d\s*(?:-|~|～|–|—|至|到)\s*[-+]?\d")
RANGE_PAIR_RE = re.compile(
    r"([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*(?:-|~|～|–|—|至|到)\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))"
)
PLUS_MINUS_PAIR_RE = re.compile(
    r"([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*(?:±|\+/-|\+-|�{1,2})\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))"
)


@dataclass
class ParsedMeasurementValue:
    value: float
    role: str = "single"
    replicate_index: Optional[int] = None


@dataclass
class ParsedMeasurement:
    raw_value: str
    values: List[ParsedMeasurementValue] = field(default_factory=list)
    reported_average: Optional[float] = None
    computed_mean: Optional[float] = None
    value_min: Optional[float] = None
    value_max: Optional[float] = None
    value_std: Optional[float] = None
    value_uncertainty: Optional[float] = None
    value_count: int = 0
    numeric_for_ranking: Optional[float] = None
    aggregation_policy: str = "no_numeric_value"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_value": self.raw_value,
            "values": [
                {
                    "value": item.value,
                    "role": item.role,
                    "replicate_index": item.replicate_index,
                }
                for item in self.values
            ],
            "reported_average": self.reported_average,
            "computed_mean": self.computed_mean,
            "value_min": self.value_min,
            "value_max": self.value_max,
            "value_std": self.value_std,
            "value_uncertainty": self.value_uncertainty,
            "value_count": self.value_count,
            "numeric_for_ranking": self.numeric_for_ranking,
            "aggregation_policy": self.aggregation_policy,
        }


def parse_measurement_cell(value: Any) -> ParsedMeasurement:
    """Parse a measurement cell into structured numbers and summary statistics."""
    raw = _to_text(value)
    parsed = ParsedMeasurement(raw_value=raw)
    text = _normalize_numeric_text(raw.strip())
    if not text or SOURCE_ONLY_RE.match(text):
        return parsed

    segments = _split_segments(text)
    if not segments:
        segments = [text]

    has_global_parallel_label = PARALLEL_LABEL_RE.search(text) is not None
    replicate_values: List[float] = []
    unlabeled_values: List[float] = []
    average_values: List[float] = []
    range_values: List[float] = []
    uncertainty_values: List[float] = []

    for segment in segments:
        plus_minus = _extract_plus_minus(segment)
        if plus_minus:
            value_number, uncertainty = plus_minus
            unlabeled_values.append(value_number)
            uncertainty_values.append(uncertainty)
            continue
        if RANGE_SEP_RE.search(segment) and not _contains_scientific_notation(segment):
            range_numbers = _extract_range_numbers(segment)
            if range_numbers:
                range_values.extend(range_numbers)
                continue
        numbers = _extract_numbers(segment)
        if not numbers:
            continue
        if AVERAGE_LABEL_RE.search(segment):
            average_values.extend(numbers)
        elif PARALLEL_LABEL_RE.search(segment):
            replicate_values.extend(numbers)
        else:
            unlabeled_values.extend(numbers)

    single_values: List[float] = []
    if has_global_parallel_label and replicate_values:
        replicate_values.extend(unlabeled_values)
    else:
        single_values = unlabeled_values

    if replicate_values:
        for index, number in enumerate(replicate_values, start=1):
            parsed.values.append(ParsedMeasurementValue(number, "replicate", index))
    if average_values:
        for number in average_values:
            parsed.values.append(ParsedMeasurementValue(number, "average"))
        parsed.reported_average = average_values[-1]
    if range_values:
        for number in range_values:
            parsed.values.append(ParsedMeasurementValue(number, "range_bound"))
    if single_values:
        role = "single"
        if not replicate_values and not average_values and len(single_values) > 1:
            role = "unlabeled"
        for index, number in enumerate(single_values, start=1):
            parsed.values.append(
                ParsedMeasurementValue(
                    number,
                    role,
                    None,
                )
            )

    summary_values = replicate_values or single_values or range_values
    if summary_values:
        parsed.value_count = len(summary_values)
        parsed.computed_mean = sum(summary_values) / len(summary_values)
        parsed.value_min = min(summary_values)
        parsed.value_max = max(summary_values)
        parsed.value_std = _sample_std(summary_values)

    if parsed.reported_average is not None:
        parsed.numeric_for_ranking = parsed.reported_average
        parsed.aggregation_policy = "reported_average"
    elif replicate_values:
        parsed.numeric_for_ranking = parsed.computed_mean
        parsed.aggregation_policy = "mean_of_parallel_values"
    elif single_values:
        parsed.numeric_for_ranking = single_values[0] if len(single_values) == 1 else parsed.computed_mean
        parsed.aggregation_policy = "single_value" if len(single_values) == 1 else "mean_of_unlabeled_values"
    elif range_values:
        parsed.numeric_for_ranking = parsed.computed_mean
        parsed.aggregation_policy = "midpoint_of_range"

    if uncertainty_values:
        parsed.value_uncertainty = uncertainty_values[-1]
        if parsed.aggregation_policy == "single_value":
            parsed.aggregation_policy = "value_with_uncertainty"

    return parsed


def numeric_value_for_ranking(value: Any) -> Optional[float]:
    """Return the default numeric value to use for sorting/filtering a cell."""
    return parse_measurement_cell(value).numeric_for_ranking


def _split_segments(text: str) -> List[str]:
    normalized = (
        text.replace("；", ";")
        .replace("，", ",")
        .replace("、", ",")
        .replace("\n", ";")
    )
    return [part.strip() for part in re.split(r";|\bor\b|或者", normalized, flags=re.IGNORECASE) if part.strip()]


def _extract_numbers(text: str) -> List[float]:
    return [_parse_number(match.group(0)) for match in NUMBER_RE.finditer(text)]


def _contains_scientific_notation(text: str) -> bool:
    return re.search(r"(?:[eE]|[×xX]\s*10)", text) is not None


def _extract_range_numbers(text: str) -> List[float]:
    match = RANGE_PAIR_RE.search(text)
    if not match:
        return []
    return [float(match.group(1)), float(match.group(2))]


def _extract_plus_minus(text: str) -> Optional[tuple[float, float]]:
    match = PLUS_MINUS_PAIR_RE.search(text)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def _parse_number(text: str) -> float:
    cleaned = text.strip().replace(" ", "")
    cleaned = cleaned.replace("×", "x").replace("X", "x")
    cleaned = cleaned.replace("{", "").replace("}", "")
    cleaned = re.sub(r"x10(?:\^|\*\*)?", "e", cleaned, flags=re.IGNORECASE)
    return float(cleaned)


def _sample_std(values: List[float]) -> Optional[float]:
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_numeric_text(text: str) -> str:
    superscripts = str.maketrans(
        {
            "⁰": "0",
            "¹": "1",
            "²": "2",
            "³": "3",
            "⁴": "4",
            "⁵": "5",
            "⁶": "6",
            "⁷": "7",
            "⁸": "8",
            "⁹": "9",
            "⁺": "+",
            "⁻": "-",
        }
    )
    return text.translate(superscripts)
