"""Normalize material identifiers returned by extraction models."""
from typing import Any, List, Optional


def _normalize_grade_text(value: Any) -> Optional[str]:
    """Normalize possible material-grade text and filter obvious non-grade noise."""
    if not isinstance(value, str):
        return None
    grade = value.strip()
    if not grade:
        return None
    lower_grade = grade.lower()
    if lower_grade in {
        "none",
        "null",
        "n/a",
        "na",
        "unknown",
        "not mentioned",
        "not provided",
    }:
        return None
    return grade



def _normalize_grade_texts(values: Any) -> List[str]:
    """Normalize a list (or single string) of material grades.
    Returns a deduplicated list of valid grade strings.
    """
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []

    seen = set()
    results = []
    for v in values:
        normalized = _normalize_grade_text(v)
        if normalized and normalized not in seen:
            seen.add(normalized)
            results.append(normalized)
    return results



def _extract_filler_grades(filler_material: Any) -> List[str]:
    """
    Extract filler material grades from heterogeneous filler structures.

    Supported common patterns:
    1) [{"grade": "ER50-6", "welding_action": "root pass"}]
    2) [{"root pass": "ER50-6"}]
    """
    grades: List[str] = []
    seen = set()

    if not isinstance(filler_material, list):
        return grades

    for item in filler_material:
        candidate_values: List[Any] = []
        if isinstance(item, dict):
            ignore_single_keys = {"welding_action", "action", "pass", "name", "type"}
            if "grade" in item:
                candidate_values.append(item.get("grade"))
            elif len(item) == 1:
                only_key = str(next(iter(item.keys()))).lower()
                if only_key not in ignore_single_keys:
                    candidate_values.extend(item.values())
            else:
                # Fallback: only keep keys that are semantically likely to carry grades.
                for k, v in item.items():
                    key_lower = str(k).lower()
                    if any(token in key_lower for token in ("grade", "material", "filler")):
                        candidate_values.append(v)

        for raw_value in candidate_values:
            grade = _normalize_grade_text(raw_value)
            if grade and grade not in seen:
                grades.append(grade)
                seen.add(grade)

    return grades

