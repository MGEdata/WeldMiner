from typing import Any, Dict, List, Optional
from .skeleton_extraction import get_prompt as get_skeleton_prompt_en
from .material_dimension import get_prompt as get_material_dimension_prompt_en
from .sample_fact import get_prompt as get_sample_fact_prompt_en

# English skeleton check/correction
from .skeleton_check import get_skeleton_check_prompt as _get_skeleton_check_prompt_en
from .skeleton_check import get_skeleton_correction_prompt as _get_skeleton_correction_prompt_en

# Chinese prompts
from .骨架提取 import get_prompt as get_skeleton_prompt_zh
from .材料实体数据提取 import get_prompt as get_material_dimension_prompt_zh
from .样品性能提取 import get_prompt as get_sample_fact_prompt_zh
from .骨架检查 import get_skeleton_check_prompt as _get_skeleton_check_prompt_zh
from .骨架检查 import get_skeleton_correction_prompt as _get_skeleton_correction_prompt_zh


def get_skeleton_prompt(raw_text: str | None = None, lang: str = "en", sample_user_goal: Any = None, sample_direct_goal: Any = None):
    """Get skeleton extraction prompt in specified language."""
    if lang.lower() == "zh":
        return get_skeleton_prompt_zh(raw_text, sample_user_goal=sample_user_goal, sample_direct_goal=sample_direct_goal)
    return get_skeleton_prompt_en(raw_text, sample_user_goal=sample_user_goal, sample_direct_goal=sample_direct_goal)


def get_material_dimension_prompt(
    grade: str,
    material_type: str,
    differentiation_factors: str,
    raw_text: str | None = None,
    lang: str = "en",
    material_user_goal: Any = None,
    material_direct_goal: Any = None,
):
    """Get material dimension extraction prompt in specified language."""
    if lang.lower() == "zh":
        return get_material_dimension_prompt_zh(grade, material_type, differentiation_factors, raw_text, material_user_goal=material_user_goal, material_direct_goal=material_direct_goal)
    return get_material_dimension_prompt_en(grade, material_type, differentiation_factors, raw_text, material_user_goal=material_user_goal, material_direct_goal=material_direct_goal)


def get_sample_fact_prompt(
    base: str,
    filler_json: str,
    welding_method: str,
    factors: str,
    raw_text: str | None = None,
    lang: str = "en",
    sample_user_goal: Any = None,
    sample_direct_goal: Any = None,
):
    """Get sample fact extraction prompt in specified language."""
    if lang.lower() == "zh":
        return get_sample_fact_prompt_zh(base, filler_json, welding_method, factors, raw_text, sample_user_goal=sample_user_goal, sample_direct_goal=sample_direct_goal)
    return get_sample_fact_prompt_en(base, filler_json, welding_method, factors, raw_text, sample_user_goal=sample_user_goal, sample_direct_goal=sample_direct_goal)


def get_skeleton_check_prompt(
    skeleton_json: str,
    source_text: Optional[str] = None,
    diff_factors_example: str = "",
    skeleton_cot: str = "",
    lang: str = "en",
    sample_user_goal: Any = None,
    sample_direct_goal: Any = None,
) -> str:
    """Get skeleton check prompt in specified language."""
    if lang.lower() == "zh":
        return _get_skeleton_check_prompt_zh(
            skeleton_json, source_text, skeleton_cot, diff_factors_example, sample_user_goal=sample_user_goal, sample_direct_goal=sample_direct_goal
        )
    return _get_skeleton_check_prompt_en(
        skeleton_json, source_text, skeleton_cot, diff_factors_example, sample_user_goal=sample_user_goal, sample_direct_goal=sample_direct_goal
    )


def get_skeleton_correction_prompt(
    source_text: Optional[str] = None,
    false_items_data: Optional[List[Dict[str, Any]]] = None,
    problem_desc: str = "",
    skeleton_json: str = "",
    skeleton_cot: str = "",
    inspection_data: Optional[Dict[str, Any]] = None,
    lang: str = "en",
) -> str:
    """Get skeleton correction prompt in specified language."""
    if lang.lower() == "zh":
        return _get_skeleton_correction_prompt_zh(
            skeleton_json, skeleton_cot, source_text, inspection_data or {}, "", lang
        )
    return _get_skeleton_correction_prompt_en(
        skeleton_json, skeleton_cot, source_text, inspection_data or {}, "", lang
    )


__all__ = [
    "get_skeleton_prompt",
    "get_material_dimension_prompt",
    "get_skeleton_check_prompt",
    "get_skeleton_correction_prompt",
    "get_sample_fact_prompt",
]
