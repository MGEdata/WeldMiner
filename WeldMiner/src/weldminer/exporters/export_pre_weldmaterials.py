"""
Export Deep Results with Base Metal + Filler Metal Data Flattened

功能：批量读取 result.json，导出 deep_results 数据，
同时平铺母材（base_metal）和焊材（filler_material）详细数据为多列。

母材规则（每个 specimen 恰好 2 条）：
- 0 条 → 两个空列
- 1 条 → 复制为 2 条
- 2 条 → 保留
- >2 条 → 保留前 2 条

焊材规则（每个 specimen 恰好 3 条）：
- 0 条 → 三个空列
- 1-2 条 → 保留 + 空列补齐
- 3 条 → 保留
- >3 条 → 保留前 3 条

材料数据来源于 material_dimensions 中对应 material_type 的记录。
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.data_schemas import get_material_user_goal_field_names


# ==================== Helper Functions (reused from csv_exporter.py) ====================

def _get_value(obj, field_name, default=''):
    """Safely get value from object or dict"""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(field_name, default)
    return getattr(obj, field_name, default)


def _format_base_material(base_material):
    """Format base_material (List[str]) for display."""
    if not base_material:
        return ''
    if isinstance(base_material, str):
        return base_material
    if isinstance(base_material, list):
        return ', '.join(str(m) for m in base_material if m)
    if hasattr(base_material, 'model_dump'):
        return str(base_material.model_dump())
    return str(base_material)


def _format_filler_material(filler_mat_list):
    """Format filler material list for display."""
    if not filler_mat_list or isinstance(filler_mat_list, str):
        return str(filler_mat_list) if filler_mat_list else ''
    if not hasattr(filler_mat_list, '__iter__'):
        return str(filler_mat_list)

    parts = []
    for item in filler_mat_list:
        if isinstance(item, dict):
            welding_name = item.get('welding_name') or item.get('welding_action') or ''
            grade = item.get('grade') or ''
            if welding_name or grade:
                parts.append(f"{welding_name}: {grade}".strip(': ').strip())
                continue
            if len(item) == 1:
                k, v = next(iter(item.items()))
                parts.append(f"{k}: {v}")
            else:
                parts.append('; '.join([f"{k}: {v}" for k, v in item.items()]))
        else:
            parts.append(str(item))

    return '; '.join([p for p in parts if p])


def _format_welding_params_for_excel(welding_params_list):
    """Convert welding_params list to JSON string."""
    if not welding_params_list:
        return ''
    if isinstance(welding_params_list, str):
        return welding_params_list
    try:
        return json.dumps(welding_params_list, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(welding_params_list)


def _format_chemical_composition(chem_comp):
    """Format chemical composition dict for display."""
    if not chem_comp:
        return ''
    if hasattr(chem_comp, 'model_dump'):
        chem_comp = chem_comp.model_dump()
    if isinstance(chem_comp, dict):
        return '; '.join([f"{k}: {v}" for k, v in chem_comp.items() if v])
    return str(chem_comp)


def _format_test_conditions(test_conditions):
    """Format test_conditions list for display."""
    if not test_conditions:
        return ''
    if isinstance(test_conditions, str):
        return test_conditions
    if isinstance(test_conditions, list):
        parts = []
        for item in test_conditions:
            if isinstance(item, dict):
                parts.append('; '.join(f"{k}: {v}" for k, v in item.items() if v))
            else:
                parts.append(str(item))
        return ' | '.join(parts)
    return str(test_conditions)


def _as_dict(obj):
    """Convert object to dict."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    return getattr(obj, "__dict__", {})


def _collect_output_headers(items, base_headers):
    """Build output headers from stable base columns plus actual dynamic columns."""
    headers = list(base_headers)
    seen = set(headers)
    for item in items or []:
        for key in _as_dict(item).keys():
            if key in seen:
                continue
            headers.append(key)
            seen.add(key)
    return headers


def _row_for_headers(item, headers, formatters=None):
    """Build a row by looking up each header from item, with optional formatters."""
    formatters = formatters or {}
    row = []
    for header in headers:
        if header in formatters:
            row.append(formatters[header](item))
        else:
            row.append(_get_value(item, header, ""))
    return row


# ==================== Base Metal Processing ====================

_MATERIAL_BASE_FIELDS = [
    'grade',
    'composition_unit',
    'chemical_composition',
    'material_size',
]

_MATERIAL_EXCLUDED_FIELDS = {
    'specimen_id',
    'material_type',
}


def _collect_material_fields_from_data(material_dimensions: List[Dict]) -> List[str]:
    """Collect material fields that appear in extracted material_dimensions."""
    headers = list(_MATERIAL_BASE_FIELDS)
    seen = set(headers) | _MATERIAL_EXCLUDED_FIELDS
    for item in material_dimensions or []:
        for key in _as_dict(item).keys():
            if key in seen:
                continue
            headers.append(key)
            seen.add(key)
    return headers


def _material_fields(material_dimensions: List[Dict],
                     material_user_goal=None,
                     material_direct_goal=None) -> List[str]:
    """Build material export fields from explicit goals or discovered data."""
    if material_user_goal is not None or material_direct_goal is not None:
        goal_fields = get_material_user_goal_field_names(material_user_goal, material_direct_goal)
        return _MATERIAL_BASE_FIELDS + [
            field for field in goal_fields if field not in _MATERIAL_BASE_FIELDS
        ]
    return _collect_material_fields_from_data(material_dimensions)


def _build_material_map(material_dimensions: List[Dict], material_type: str) -> Dict[str, List[Dict]]:
    """
    从 material_dimensions 中筛选指定 material_type 记录，按 specimen_id 分组。
    返回: {specimen_id: [material_dict, ...]}
    """
    material_map: Dict[str, List[Dict]] = {}
    for item in material_dimensions:
        mat_type = _get_value(item, 'material_type', '')
        if mat_type != material_type:
            continue
        sid = _get_value(item, 'specimen_id', '')
        if not sid:
            continue
        if sid not in material_map:
            material_map[sid] = []
        material_map[sid].append(item)
    return material_map


def _normalize_base_metals(base_metals: List[Dict]) -> List[Dict]:
    """
    确保母材列表恰好为 2 条：
    - 0 条 → 返回两条空 dict
    - 1 条 → 复制为 2 条
    - 2 条 → 保留
    - >2 条 → 保留前 2 条
    """
    empty = {}
    if not base_metals:
        return [empty, empty]
    if len(base_metals) == 1:
        return [base_metals[0], base_metals[0]]
    if len(base_metals) >= 2:
        return base_metals[:2]
    return [empty, empty]


def _normalize_filler_materials(filler_materials: List[Dict]) -> List[Dict]:
    """
    确保焊材列表恰好为 3 条：
    - 0 条 → 返回三个空 dict
    - 1 条 → 保留 1 条 + 2 个空 dict
    - 2 条 → 保留 2 条 + 1 个空 dict
    - 3 条 → 保留
    - >3 条 → 保留前 3 条
    """
    empty = {}
    if not filler_materials:
        return [empty, empty, empty]
    n = len(filler_materials)
    if n >= 3:
        return filler_materials[:3]
    result = filler_materials[:]
    while len(result) < 3:
        result.append(empty)
    return result


def _get_material_value(material: Dict, field: str) -> str:
    """获取材料字段值，格式化 chemical_composition。"""
    value = _get_value(material, field, '')
    if field == 'chemical_composition':
        return _format_chemical_composition(value)
    if value is None:
        return ''
    return str(value)


# ==================== Export Functions ====================

_DEEP_RESULTS_BASE_HEADERS = [
    'specimen_id',
    'data_features',
    'welding_method',
    'base_material',
    'filler_material',
    'welding_params',
    'test_method',
    'testing_area',
    'testing_standard',
    'testing_specimen_size',
    'performance_result_source',
]


def _deep_results_headers(deep_results: List[Dict]) -> List[str]:
    """动态收集 deep_results 的表头，基础字段 + 自动发现的动态字段。"""
    return _collect_output_headers(deep_results, _DEEP_RESULTS_BASE_HEADERS)


def _base_metal_headers(material_fields: List[str]) -> List[str]:
    """母材平铺后的列名：base_metal_1_*, base_metal_2_*"""
    headers = []
    for i in (1, 2):
        for field in material_fields:
            headers.append(f"base_metal_{i}_{field}")
    return headers


def _filler_material_headers(material_fields: List[str]) -> List[str]:
    """焊材平铺后的列名：filler_material_1_*, filler_material_2_*, filler_material_3_*"""
    headers = []
    for i in (1, 2, 3):
        for field in material_fields:
            headers.append(f"filler_material_{i}_{field}")
    return headers


def _build_row(item: Dict, deep_headers: List[str],
               base_metal_1: Dict, base_metal_2: Dict,
               filler_1: Dict, filler_2: Dict, filler_3: Dict,
               material_fields: List[str]) -> List[str]:
    """构建一行数据：deep_results 字段 + 母材字段 + 焊材字段。"""
    row = []

    row.extend(_row_for_headers(item, deep_headers, {
        'base_material': lambda it: _format_base_material(_get_value(it, 'base_material', [])),
        'filler_material': lambda it: _format_filler_material(_get_value(it, 'filler_material', [])),
        'welding_params': lambda it: _format_welding_params_for_excel(_get_value(it, 'welding_params', [])),
        'test_conditions': lambda it: _format_test_conditions(_get_value(it, 'test_conditions', [])),
        'base_chemical_composition': lambda it: _format_chemical_composition(_get_value(it, 'base_chemical_composition', {})),
    }))

    # Base metal 1 fields
    for field in material_fields:
        row.append(_get_material_value(base_metal_1, field))

    # Base metal 2 fields
    for field in material_fields:
        row.append(_get_material_value(base_metal_2, field))

    # Filler material 1-3 fields
    for filler in (filler_1, filler_2, filler_3):
        for field in material_fields:
            row.append(_get_material_value(filler, field))

    return row


def export_to_csv_with_base_metal(deep_results: List[Dict],
                                   material_dimensions: List[Dict],
                                   output_file: str,
                                   material_user_goal=None,
                                   material_direct_goal=None):
    """Export deep_results with base_metal and filler_metal columns to CSV."""
    if not deep_results:
        print("No deep results to export")
        return

    base_metal_map = _build_material_map(material_dimensions, 'base_metal')
    filler_material_map = _build_material_map(material_dimensions, 'filler')

    deep_headers = _deep_results_headers(deep_results)
    material_fields = _material_fields(material_dimensions, material_user_goal, material_direct_goal)
    headers = deep_headers + _base_metal_headers(material_fields) + _filler_material_headers(material_fields)

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for item in deep_results:
            sid = _get_value(item, 'specimen_id', '')
            base_metals = base_metal_map.get(sid, [])
            bm1, bm2 = _normalize_base_metals(base_metals)
            fillers = filler_material_map.get(sid, [])
            f1, f2, f3 = _normalize_filler_materials(fillers)
            writer.writerow(_build_row(item, deep_headers, bm1, bm2, f1, f2, f3, material_fields))


def export_to_excel_with_base_metal(deep_results: List[Dict],
                                     material_dimensions: List[Dict],
                                     output_file: str,
                                     material_user_goal=None,
                                     material_direct_goal=None):
    """Export deep_results with base_metal and filler_metal columns to Excel."""
    try:
        from openpyxl import Workbook
    except ImportError:
        print("Error: openpyxl is required for Excel export. Install with: pip install openpyxl")
        return

    if not deep_results:
        print("No deep results to export")
        return

    base_metal_map = _build_material_map(material_dimensions, 'base_metal')
    filler_material_map = _build_material_map(material_dimensions, 'filler')

    wb = Workbook()
    ws = wb.active
    ws.title = "深度结果(含母材焊材)"

    deep_headers = _deep_results_headers(deep_results)
    material_fields = _material_fields(material_dimensions, material_user_goal, material_direct_goal)
    headers = deep_headers + _base_metal_headers(material_fields) + _filler_material_headers(material_fields)

    # Write headers
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)

    # Write data
    for row_idx, item in enumerate(deep_results, 2):
        sid = _get_value(item, 'specimen_id', '')
        base_metals = base_metal_map.get(sid, [])
        bm1, bm2 = _normalize_base_metals(base_metals)
        fillers = filler_material_map.get(sid, [])
        f1, f2, f3 = _normalize_filler_materials(fillers)
        row_data = _build_row(item, deep_headers, bm1, bm2, f1, f2, f3, material_fields)

        for col_idx, value in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=value)

    wb.save(output_file)


def _col_index_to_letter(index: int) -> str:
    """Convert 1-based column index to Excel column letter."""
    result = []
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result.append(chr(65 + remainder))
    return ''.join(reversed(result))


# ==================== Batch Processing ====================

def process_all_with_base_metal(root_dir: str = "output_md",
                                 output_dir: str = None,
                                 use_excel: bool = True):
    """
    批量处理 output_md 目录下所有子目录中的 result.json 文件，
    导出 deep_results 并平铺母材、焊材数据。

    Args:
        root_dir: 根目录路径，默认为 output_md
        output_dir: 输出目录，默认为每个子目录本身
        use_excel: 是否使用 Excel 格式输出（默认 True），否则使用 CSV
    """
    root_path = Path(root_dir)

    if not root_path.exists():
        print(f"根目录不存在: {root_dir}")
        return

    processed_count = 0
    error_count = 0

    for subdir in root_path.iterdir():
        if not subdir.is_dir():
            continue

        deep_result_path = subdir / "05_deep_result" / "result.json"
        material_dim_path = subdir / "03_material_dimension" / "result.json"

        if not deep_result_path.exists():
            print(f"跳过: {subdir.name} (未找到 05_deep_result/result.json)")
            continue

        try:
            print(f"处理: {subdir.name}")

            # 读取 deep_results
            with open(deep_result_path, 'r', encoding='utf-8') as f:
                deep_data = json.load(f)
            deep_results = deep_data.get('final_result', [])

            # 读取 material_dimensions
            material_dimensions = []
            if material_dim_path.exists():
                with open(material_dim_path, 'r', encoding='utf-8') as f:
                    mat_data = json.load(f)
                material_dimensions = mat_data.get('material_dimensions', [])
            else:
                print(f"  警告: 未找到 03_material_dimension/result.json，母材列将为空")

            if output_dir:
                output_path = Path(output_dir) / subdir.name
                output_path.mkdir(parents=True, exist_ok=True)
            else:
                output_path = subdir

            if use_excel:
                excel_file = output_path / "extra_data_with_base_metal_filler.xlsx"
                export_to_excel_with_base_metal(
                    deep_results, material_dimensions, str(excel_file)
                )
                print(f"  成功导出: {excel_file}")
            else:
                csv_file = output_path / "deep_results_with_base_metal_filler.csv"
                export_to_csv_with_base_metal(
                    deep_results, material_dimensions, str(csv_file)
                )
                print(f"  成功导出: {csv_file}")

            processed_count += 1

        except Exception as e:
            print(f"  处理失败: {e}")
            import traceback
            traceback.print_exc()
            error_count += 1

    print(f"\n处理完成: 成功 {processed_count} 个, 失败 {error_count} 个")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Export deep results with base metal data flattened to columns'
    )
    parser.add_argument(
        'root_dir', nargs='?', default=str(Path.cwd() / 'output'),
        help='Root directory containing subdirectories with result.json files (default: ../output)'
    )
    parser.add_argument(
        'output_dir', nargs='?', default=None,
        help='Output directory (default: same as input subdirectories)'
    )
    parser.add_argument(
        '--csv', action='store_true',
        help='Use CSV format instead of Excel'
    )

    args = parser.parse_args()

    process_all_with_base_metal(
        args.root_dir, args.output_dir, use_excel=not args.csv
    )
