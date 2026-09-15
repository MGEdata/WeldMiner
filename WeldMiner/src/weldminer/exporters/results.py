"""Public result persistence, independent of workflow invocation."""
import json
from pathlib import Path

def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)

def save_result(state, folder: Path, config):
    write_json(folder / 'result.json', state.model_dump(mode='json'))
    if state.final_result and config.export_csv:
        from .csv_exporter import export_to_csv
        export_to_csv(state, output_dir=str(folder))
    if state.final_result and config.export_excel:
        from .export_pre_weldmaterials import export_to_excel_with_base_metal
        export_to_excel_with_base_metal(state.final_result, state.material_dimensions,
            str(folder / 'deep_results_with_base_metal_filler.xlsx'),
            material_user_goal=config.material_user_goal,
            material_direct_goal=config.material_direct_goal)

