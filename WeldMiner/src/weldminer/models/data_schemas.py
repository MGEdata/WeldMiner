"""
Welding Data Extraction - Layered Async Workflow
English variable names and prompts
"""

from typing import Dict, Any, List, Optional, Literal, Union
from pydantic import BaseModel, Field, ConfigDict, TypeAdapter, create_model, field_validator
import json
import re

# Global config
BaseModel.model_config = ConfigDict(
    arbitrary_types_allowed=True,
    validate_default=True,
    extra='ignore'
)

# ==================== Skeleton Table ====================

class SkeletonItem(BaseModel):
    """Skeleton table - specimen list"""
    base_material: List[str] = Field(default_factory=list, description="Base material grade")
    filler_material: List[Dict[str, Any]] = Field(default_factory=list, description="Filler material list, e.g., [{\"welding_name\": \"root pass\", \"grade\": \"ER50-6\"}]")
    welding_method: str = Field(default=..., description="Welding method")
    data_features: str = Field(default=..., description="Differentiation conditions")
    source_quote: List[str] = Field(default_factory=list, description="Source quote list")

class SkeletonItemHash(BaseModel):
    """Skeleton table - hash key"""
    specimen_id: str = Field(default=..., description="Specimen ID")
    base_material: List[str] = Field(default_factory=list, description="Base material grade")
    filler_material: List[Dict[str, Any]] = Field(default_factory=list, description="Filler material list, e.g., [{\"welding_name\": \"root pass\", \"grade\": \"ER50-6\"}]")
    welding_method: str = Field(default=..., description="Welding method")
    data_features: str = Field(default=..., description="Differentiation conditions")
    source_quote: List[str] = Field(default_factory=list, description="Source quote list")
SkeletonTable = TypeAdapter(List[SkeletonItem])
SkeletonItemHashTable = TypeAdapter(List[SkeletonItemHash])

# ==================== skeleton check Table ====================
class SkeletonCheckItem(BaseModel):
    """Skeleton check table - check result"""
    check_passed: bool = Field(default=..., description="Check passed or not")
    problem_description: Optional[List[str]] = Field(default=None, description="Problem description if check failed")
    corrected_results: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Corrected results if check failed")
    false_results: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="False results if check failed")
    missing_items: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Items found in source but missing from skeleton data")
    missingitem_source: Optional[List[str]] = Field(default_factory=list, description="Source locations for missing items")
    duplicate_items: Optional[List[str]] = Field(default_factory=list, description="List of data_features values that appear to be duplicates")
    correction_summary: Optional[str] = Field(default=None, description="Summary of corrections made, including error types and source references")


# ==================== User Goal Schema Helpers ====================

class DynamicSampleFactBase(BaseModel):
    """Common sample-fact fields; performance fields are added from sample_user_goal."""
    model_config = ConfigDict(extra='ignore')

    @field_validator("*", mode='before')
    @classmethod
    def _coerce_numbers_to_str(cls, v):
        if v is None:
            return None
        if isinstance(v, (list, dict)):
            return v
        return str(v)

    welding_params: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Welding parameters list")
    test_method: Optional[str] = Field(default=None, description="Test method")
    testing_area: Optional[str] = Field(default=None, description="Test area")
    testing_standard: Optional[str] = Field(default=None, description="Test standard")
    testing_specimen_size: Optional[str] = Field(default=None, description="Specimen size")
    performance_result_source: Optional[str] = Field(default=None, description="Source figure or table for performance results")


class DynamicSampleFactHashBase(DynamicSampleFactBase):
    """Common sample-fact fields plus specimen id."""
    specimen_id: str = Field(default=..., description="Specimen ID")


class DynamicDeepNestedResultBase(DynamicSampleFactHashBase):
    """Common final-result fields; performance fields are added from sample_user_goal."""
    data_features: Optional[str] = Field(default=None, description="Differentiation features list")
    welding_method: Optional[str] = Field(default=None, description="Welding method")
    base_material: Optional[List[str]] = Field(default_factory=list, description="Base material grade")
    filler_material: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Filler material list")


class DynamicMaterialDimensionBase(BaseModel):
    """Common material-entity fields; mechanical properties are added from material_user_goal."""
    model_config = ConfigDict(extra='ignore')

    @field_validator("*", mode='before')
    @classmethod
    def _coerce_numbers_to_str(cls, v):
        if v is None:
            return None
        if isinstance(v, (list, dict)):
            return v
        return str(v)

    grade: Optional[str] = Field(default=None, description="Material grade")
    material_type: Optional[Literal["base_metal", "filler"]] = Field(default=None, description="Material type")
    composition_unit: Optional[str] = Field(default=None, description="Composition unit")
    chemical_composition: Optional[Dict[str, str]] = Field(default_factory=dict, description="Chemical composition")
    material_size: Optional[str] = Field(default=None, description="Material size")


class DynamicMaterialDimensionHashBase(DynamicMaterialDimensionBase):
    """Common material-entity fields plus specimen id."""
    specimen_id: str = Field(default=..., description="Specimen ID")


DEFAULT_USER_GOALS = [
    {"key": "hardness", "label": "hardness"},
    {"key": "stretching_rate", "label": "stretching rate"},
    {"key": "tensile_strength", "label": "tensile strength"},
    {"key": "yield_strength", "label": "yield strength"},
    {"key": "elongation", "label": "elongation"},
    {"key": "reduction_of_area", "label": "reduction of area"},
    {"key": "Charpy_impact_test_temperature", "label": "Charpy impact test temperature"},
    {"key": "impact_energy", "label": "impact energy"},
]

DEFAULT_SAMPLE_USER_GOALS = DEFAULT_USER_GOALS

DEFAULT_MATERIAL_USER_GOALS = [
    {"key": "tensile_strength", "label": "tensile strength"},
    {"key": "yield_strength", "label": "yield strength"},
    {"key": "elongation", "label": "elongation"},
]



def _safe_goal_key(value: Any) -> str:
    key = str(value or "").strip()
    key = re.sub(r"\s+", "_", key)
    key = re.sub(r"[^0-9A-Za-z_\u4e00-\u9fff]", "_", key)
    key = re.sub(r"_+", "_", key).strip("_")
    if not key:
        key = "custom_goal"
    if key[0].isdigit():
        key = f"goal_{key}"
    return key




def normalize_goal_items(goal_items: Any = None, default_goals: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
    """Normalize simple strings or dicts into [{'key': field_prefix, 'label': display_name}, ...]."""
    fallback_goals = default_goals or DEFAULT_SAMPLE_USER_GOALS
    if goal_items is None:
        return [dict(item) for item in fallback_goals]

    if isinstance(goal_items, str):
        raw_items = [item.strip() for item in re.split(r"[,;，；\n]+", goal_items) if item.strip()]
    elif isinstance(goal_items, (list, tuple)):
        raw_items = list(goal_items)
    else:
        raw_items = [goal_items]

    goals: List[Dict[str, str]] = []
    seen = set()
    for item in raw_items:
        if isinstance(item, dict):
            raw_key = item.get("key") or item.get("field") or item.get("name") or item.get("label") or item.get("goal")
            label = str(item.get("label") or item.get("name") or item.get("goal") or raw_key or "").strip()
            if not raw_key and not label:
                continue
            key = _safe_goal_key(raw_key)
        else:
            raw_key = item
            label = str(item).strip()
            if not label:
                continue
            key = _safe_goal_key(raw_key)

        if key in seen:
            continue
        seen.add(key)
        goals.append({"key": key, "label": label or key})

    return goals


def normalize_direct_goal_items(goal_items: Any = None) -> List[Dict[str, str]]:
    """Normalize direct extraction targets without applying default goals."""
    if not goal_items:
        return []
    if isinstance(goal_items, str):
        raw_items = [item.strip() for item in re.split(r"[,;，；\n]+", goal_items) if item.strip()]
    elif isinstance(goal_items, (list, tuple)):
        raw_items = list(goal_items)
    else:
        raw_items = [goal_items]

    goals: List[Dict[str, str]] = []
    seen = set()
    for item in raw_items:
        if isinstance(item, dict):
            raw_key = item.get("key") or item.get("field") or item.get("name") or item.get("label") or item.get("goal")
            label = str(item.get("label") or item.get("name") or item.get("goal") or raw_key or "").strip()
        else:
            raw_key = item
            label = str(item).strip()
        key = _safe_goal_key(raw_key)
        if key in seen:
            continue
        seen.add(key)
        goals.append({"key": key, "label": label or key})
    return goals


def normalize_sample_user_goals(sample_user_goal: Any = None) -> List[Dict[str, str]]:
    """Normalize sample-fact extraction targets."""
    return normalize_goal_items(sample_user_goal, DEFAULT_SAMPLE_USER_GOALS)


def normalize_material_user_goals(material_user_goal: Any = None) -> List[Dict[str, str]]:
    """Normalize material-entity extraction targets."""
    return normalize_goal_items(material_user_goal, DEFAULT_MATERIAL_USER_GOALS)


def build_sample_user_goal_output_pattern(sample_user_goal: Any = None, sample_direct_goal: Any = None) -> Dict[str, Any]:
    """Build the sample-fact output template with structured and direct target fields."""
    output_pattern: Dict[str, Any] = {
        "welding_params": [{"": "", "": ""}],
        "test_method": "",
        "testing_area": "",
        "testing_standard": "",
        "testing_specimen_size": "",
        "performance_result_source": "",
    }
    for goal in normalize_sample_user_goals(sample_user_goal):
        key = goal["key"]
        output_pattern[f"{key}_name"] = ""
        output_pattern[f"{key}_value"] = ""
        output_pattern[f"{key}_unit"] = ""
    for goal in normalize_direct_goal_items(sample_direct_goal):
        output_pattern[goal["key"]] = ""
    return output_pattern


def build_material_dimension_output_pattern(material_user_goal: Any = None, material_direct_goal: Any = None) -> Dict[str, Any]:
    """Build material-dimension output template with structured and direct target fields."""
    output_pattern: Dict[str, Any] = {
        "grade": "",
        "material_type": "",
        "composition_unit": "",
        "chemical_composition": {},
        "material_size": "",
    }
    for goal in normalize_material_user_goals(material_user_goal):
        key = goal["key"]
        output_pattern[f"{key}_name"] = ""
        output_pattern[f"{key}_value"] = ""
        output_pattern[f"{key}_unit"] = ""
    for goal in normalize_direct_goal_items(material_direct_goal):
        output_pattern[goal["key"]] = ""
    return output_pattern


def get_sample_user_goal_field_names(sample_user_goal: Any = None, sample_direct_goal: Any = None) -> List[str]:
    """Return dynamic field names derived from user goals."""
    field_names: List[str] = []
    for goal in normalize_sample_user_goals(sample_user_goal):
        key = goal["key"]
        field_names.extend([f"{key}_name", f"{key}_value", f"{key}_unit"])
    field_names.extend(goal["key"] for goal in normalize_direct_goal_items(sample_direct_goal))
    return field_names


def get_material_user_goal_field_names(material_user_goal: Any = None, material_direct_goal: Any = None) -> List[str]:
    """Return dynamic material-entity field names derived from material_user_goal."""
    field_names: List[str] = []
    for goal in normalize_material_user_goals(material_user_goal):
        key = goal["key"]
        field_names.extend([f"{key}_name", f"{key}_value", f"{key}_unit"])
    field_names.extend(goal["key"] for goal in normalize_direct_goal_items(material_direct_goal))
    return field_names


def format_sample_user_goal_list(sample_user_goal: Any = None) -> str:
    """Human-readable sample goal list for prompts."""
    return ", ".join(goal["label"] for goal in normalize_sample_user_goals(sample_user_goal))


def format_material_user_goal_list(material_user_goal: Any = None) -> str:
    """Human-readable material goal list for prompts."""
    return ", ".join(goal["label"] for goal in normalize_material_user_goals(material_user_goal))


def format_direct_goal_list(direct_goal: Any = None) -> str:
    """Human-readable direct goal list for prompts."""
    return ", ".join(goal["label"] for goal in normalize_direct_goal_items(direct_goal))


def _goal_model_fields(
    goal_items: Any = None,
    default_goals: Optional[List[Dict[str, str]]] = None,
    direct_goal_items: Any = None,
) -> Dict[str, tuple]:
    fields = {}
    for goal in normalize_goal_items(goal_items, default_goals):
        key = goal["key"]
        for field_name in (f"{key}_name", f"{key}_value", f"{key}_unit"):
            fields[field_name] = (Optional[str], Field(default=None, description=f"{goal['label']} extracted from structured target goals"))
    for goal in normalize_direct_goal_items(direct_goal_items):
        fields[goal["key"]] = (Optional[str], Field(default=None, description=f"{goal['label']} extracted from direct target goals"))
    return fields


def create_sample_fact_item_model(sample_user_goal: Any = None, include_specimen_id: bool = False, sample_direct_goal: Any = None):
    """Create a Pydantic model whose performance fields come only from sample_user_goal."""
    if include_specimen_id:
        base_model = DynamicSampleFactHashBase
        model_name = "DynamicSampleFactItemHash"
    else:
        base_model = DynamicSampleFactBase
        model_name = "DynamicSampleFactItem"
    return create_model(model_name, __base__=base_model, **_goal_model_fields(sample_user_goal, DEFAULT_SAMPLE_USER_GOALS, sample_direct_goal))


def create_deep_result_item_model(sample_user_goal: Any = None, sample_direct_goal: Any = None):
    """Create a DeepNestedResultItem-compatible model for the requested goals."""
    return create_model("DynamicDeepNestedResultItem", __base__=DynamicDeepNestedResultBase, **_goal_model_fields(sample_user_goal, DEFAULT_SAMPLE_USER_GOALS, sample_direct_goal))


def create_material_dimension_item_model(material_user_goal: Any = None, include_specimen_id: bool = False, material_direct_goal: Any = None):
    """Create a material-dimension model whose mechanical property fields come from material_user_goal."""
    if include_specimen_id:
        base_model = DynamicMaterialDimensionHashBase
        model_name = "DynamicMaterialDimensionItemHash"
    else:
        base_model = DynamicMaterialDimensionBase
        model_name = "DynamicMaterialDimensionItem"
    return create_model(model_name, __base__=base_model, **_goal_model_fields(material_user_goal, DEFAULT_MATERIAL_USER_GOALS, material_direct_goal))

# Default dynamic model aliases. For custom targets, use the create_*_item_model(...)
# factory functions with material_user_goal or sample_user_goal.
MaterialDimensionItem = create_material_dimension_item_model()
MaterialDimensionItemHash = create_material_dimension_item_model(include_specimen_id=True)
SampleFactItem = create_sample_fact_item_model()
SampleFactItemHash = create_sample_fact_item_model(include_specimen_id=True)
DeepNestedResultItem = create_deep_result_item_model()

MaterialDimensionTable = TypeAdapter(List[MaterialDimensionItem])
SampleFactTable = TypeAdapter(List[SampleFactItem])
DeepNestedResult = TypeAdapter(List[DeepNestedResultItem])

# ==================== Workflow State ====================

class ExtractionWorkflowState(BaseModel):
    """Layered async workflow state - 适配 TypeAdapter 后的状态类"""
    # 允许任意类型（因为 TypeAdapter 实例本身不是基本类型）
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Input
    raw_text: Union[str, List[str]] = Field(
        default=...,
        description="Raw input source. Plain text for text workflows, or a list of base64-encoded page images for PDF workflows.",
    )

    # Language setting
    lang: str = Field(default="en", description="Language for prompts: 'en' or 'zh'")
    material_user_goal: Any = Field(
        default=None,
        description="Structured material-entity extraction targets. Each goal becomes <goal>_name/value/unit fields.",
    )
    material_direct_goal: Any = Field(
        default=None,
        description="Direct material-entity extraction targets. Each goal becomes one field exactly.",
    )
    sample_user_goal: Any = Field(
        default=None,
        description="Structured sample-fact extraction targets. Each goal becomes <goal>_name/value/unit fields.",
    )
    sample_direct_goal: Any = Field(
        default=None,
        description="Direct sample-fact extraction targets. Each goal becomes one field exactly.",
    )

    # Intermediate results 
    # 注意：这里直接使用 List[ItemModel]，因为 TypeAdapter 校验后的产物就是列表
    skeleton: List[SkeletonItemHash] = Field(default_factory=list, description="Skeleton data list")
    skeleton_cot: Optional[str] = Field(default=None, description="Skeleton COT content")
    
    # 建议将基材和焊材合并为一个材料维度列表，或者保持两个列表
    material_dimensions: List[Dict[str, Any]] = Field(default_factory=list, description="Global material dimensions (base & filler)")
    
    sample_facts: List[Dict[str, Any]] = Field(default_factory=list, description="Sample fact data list")


    # Final result
    final_result: List[Dict[str, Any]] = Field(default_factory=list, description="Deep nested final result list")

    # Metadata
    error_message: Optional[str] = Field(default=None, description="Error message")
    extraction_completed: bool = Field(default=False, description="Whether extraction completed")

# Export all models
__all__ = [
    "SkeletonTable",
    "SkeletonItem",
    "MaterialDimensionItem",
    "MaterialDimensionItemHash",
    "MaterialDimensionTable",
    "SampleFactTable",
    "SampleFactItem",
    "SampleFactItemHash",
    "DeepNestedResult",
    "DeepNestedResultItem",
    "ExtractionWorkflowState",
    "build_sample_user_goal_output_pattern",
    "build_material_dimension_output_pattern",
    "create_sample_fact_item_model",
    "create_material_dimension_item_model",
    "create_deep_result_item_model",
    "normalize_goal_items",
    "normalize_direct_goal_items",
    "normalize_sample_user_goals",
    "normalize_material_user_goals",
    "get_sample_user_goal_field_names",
    "get_material_user_goal_field_names",
    "format_sample_user_goal_list",
    "format_material_user_goal_list",
    "format_direct_goal_list",
]
