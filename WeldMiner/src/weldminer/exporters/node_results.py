"""Persistence for intermediate workflow node results."""
from typing import Any
from pathlib import Path
import json

_json_output_dir = None


def set_json_output_dir(output_dir: str):
    """Set the output directory for JSON files"""
    global _json_output_dir
    _json_output_dir = output_dir
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)



def _save_node_result(node_name: str, data: Any):
    """Save node result to JSON file in node-specific subfolder"""
    global _json_output_dir
    if not _json_output_dir:
        return

    try:
        # Convert Pydantic models to dict
        if hasattr(data, 'model_dump'):
            data_dict = data.model_dump(mode='json')
        elif hasattr(data, 'model_dump_json'):
            data_dict = json.loads(data.model_dump_json())
        else:
            data_dict = data

        # Debug: check skeleton length before saving
        if node_name == "01_skeleton" and 'skeleton' in data_dict:
            print(f"[DEBUG] _save_node_result: skeleton list length = {len(data_dict['skeleton'])}")

        # Create node-specific subfolder
        node_dir = Path(_json_output_dir) / node_name
        node_dir.mkdir(parents=True, exist_ok=True)

        # Save to JSON file
        output_file = node_dir / "result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=2)
        print(f"  [JSON] Saved {node_name} result to {output_file}")
    except Exception as e:
        print(f"  [JSON] Failed to save {node_name} result: {str(e)}")

