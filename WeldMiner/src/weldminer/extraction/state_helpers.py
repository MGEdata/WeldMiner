"""Adapters and empty records for extraction state."""
from typing import Any, Dict
from ..models.data_schemas import ExtractionWorkflowState, create_sample_fact_item_model, get_sample_user_goal_field_names


def _empty_sample_fact(sample_user_goal: Any = None, sample_direct_goal: Any = None):
    sample_model = create_sample_fact_item_model(sample_user_goal, sample_direct_goal=sample_direct_goal)
    empty_payload = {
        "welding_params": None,
        "test_method": None,
        "testing_area": None,
        "testing_standard": None,
        "testing_specimen_size": None,
    }
    for field_name in get_sample_user_goal_field_names(sample_user_goal, sample_direct_goal):
        empty_payload[field_name] = None
    return sample_model(**empty_payload)



def _get_sample_user_goal(state: ExtractionWorkflowState):
    return getattr(state, "sample_user_goal", None)



def _get_sample_direct_goal(state: ExtractionWorkflowState):
    return getattr(state, "sample_direct_goal", None)



def _get_material_user_goal(state: ExtractionWorkflowState):
    return getattr(state, "material_user_goal", None)



def _get_material_direct_goal(state: ExtractionWorkflowState):
    return getattr(state, "material_direct_goal", None)



def _item_to_dict(item: Any) -> Dict[str, Any]:
    if item is None:
        return {}
    if hasattr(item, "model_dump"):
        return item.model_dump(mode="json")
    if isinstance(item, dict):
        return item
    return dict(getattr(item, "__dict__", {}))



def _get_value(item: Any, field_name: str, default: Any = None) -> Any:
    if item is None:
        return default
    if isinstance(item, dict):
        return item.get(field_name, default)
    return getattr(item, field_name, default)

