"""
CSV/Excel Export Module
Export extraction results to CSV or Excel files
"""

import csv
import json
from typing import Dict, Any, List, Union
from pathlib import Path


def export_to_csv(result, output_dir: str = "output"):
    """
    Export extraction results to CSV files

    Args:
        result: Extraction workflow state result
        output_dir: Output directory

    Returns:
        List of exported file paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    exported_files = []

    if not result or not result.final_result:
        print("No data to export")
        return exported_files

    final_result = result.final_result

    skeleton_file = output_path / "skeleton_table.csv"
    _export_skeleton(result.skeleton if hasattr(result, 'skeleton') else [], skeleton_file)
    exported_files.append(str(skeleton_file))

    material_dim_file = output_path / "material_dimension.csv"
    _export_material_dimensions(result.material_dimensions if hasattr(result, 'material_dimensions') else [], material_dim_file)
    exported_files.append(str(material_dim_file))

    sample_facts_file = output_path / "sample_facts.csv"
    _export_sample_facts(result.sample_facts if hasattr(result, 'sample_facts') else [], sample_facts_file)
    exported_files.append(str(sample_facts_file))

    deep_result_file = output_path / "deep_results.csv"
    _export_deep_results(final_result, deep_result_file)
    exported_files.append(str(deep_result_file))

    return exported_files


def export_to_excel(result, output_file: str) -> str:
    """
    Export extraction results to a single Excel file with multiple sheets

    Args:
        result: Extraction workflow state result or dict with data
        output_file: Output Excel file path

    Returns:
        Path to exported file
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
    except ImportError:
        print("Error: openpyxl is required for Excel export. Install with: pip install openpyxl")
        return ""

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    default_sheet = wb.active
    default_sheet.title = "Temp"  # Rename default sheet

    # Prepare data
    if hasattr(result, 'final_result'):
        final_result = result.final_result
        skeleton = result.skeleton if hasattr(result, 'skeleton') else []
        material_dimensions = result.material_dimensions if hasattr(result, 'material_dimensions') else []
        sample_facts = result.sample_facts if hasattr(result, 'sample_facts') else []
    else:
        final_result = result.get('final_result', [])
        skeleton = result.get('skeleton', [])
        material_dimensions = result.get('material_dimensions', [])
        sample_facts = result.get('sample_facts', [])

    # Create sheets
    if final_result:
        _create_deep_results_sheet(wb, final_result)
    if skeleton:
        _create_skeleton_sheet(wb, skeleton)
    if material_dimensions:
        _create_material_dimensions_sheet(wb, material_dimensions)
    if sample_facts:
        _create_sample_facts_sheet(wb, sample_facts)

    # Remove temp sheet if we have actual data sheets
    if 'Temp' in wb.sheetnames and len(wb.sheetnames) > 1:
        wb.remove(wb['Temp'])

    wb.save(output_file)
    return output_file


def _create_skeleton_sheet(wb, skeleton):
    """Create skeleton table sheet"""
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

    ws = wb.create_sheet("骨架表")

    headers = [
        'specimen_id', 'base_material', 'filler_material', 'welding_method',
        'data_features', 'source_quote'
    ]

    # Header style
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    # Write headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # Write data
    for row_idx, item in enumerate(skeleton, 2):
        specimen_id = _get_value(item, 'specimen_id')
        base_material = _get_value(item, 'base_material')
        base_material_str = _format_base_material(base_material)
        welding_method = _get_value(item, 'welding_method')
        data_features = _get_value(item, 'data_features')

        filler_mat_list = _get_value(item, 'filler_material', [])
        filler_mat_str = _format_filler_material(filler_mat_list)

        source_quote = _get_value(item, 'source_quote', [])
        source_quote_str = _format_list_field(source_quote)

        row_data = [specimen_id, base_material_str, filler_mat_str, welding_method, data_features, source_quote_str]

        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = thin_border

    # Adjust column widths
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 40
    ws.column_dimensions['F'].width = 60  # source_quote needs more space


def _create_material_dimensions_sheet(wb, material_dims):
    """Create material dimensions sheet"""
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

    ws = wb.create_sheet("材料尺寸")

    base_headers = ['specimen_id', 'grade', 'material_type', 'composition_unit', 'chemical_composition', 'material_size']
    headers = _collect_output_headers(material_dims, base_headers)

    # Header style
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    # Write headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # Write data
    for row_idx, item in enumerate(material_dims, 2):
        chem_comp = _get_value(item, 'chemical_composition')
        chem_comp_str = _format_chemical_composition(chem_comp)

        row_data = _row_for_headers(
            item,
            headers,
            {"chemical_composition": lambda _: chem_comp_str},
        )

        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = thin_border

    # Adjust column widths
    for i in range(1, len(headers) + 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = 15
    ws.column_dimensions['E'].width = 40  # chemical_composition


def _create_sample_facts_sheet(wb, sample_facts):
    """Create sample facts sheet"""
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

    ws = wb.create_sheet("样品事实")

    base_headers = [
        'specimen_id', 'test_method', 'welding_params',
        'testing_area', 'testing_standard', 'testing_specimen_size',
        'performance_result_source'
    ]
    headers = _collect_output_headers(sample_facts, base_headers)

    # Header style
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    # Write headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # Write data
    for row_idx, item in enumerate(sample_facts, 2):
        welding_params_list = _get_value(item, 'welding_params', [])
        welding_params_str = _format_welding_params_for_excel(welding_params_list)

        row_data = _row_for_headers(
            item,
            headers,
            {"welding_params": lambda _: welding_params_str},
        )

        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = thin_border

    # Adjust column widths
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 30  # test_method
    ws.column_dimensions['C'].width = 60  # welding_params
    ws.column_dimensions['D'].width = 20  # testing_area
    ws.column_dimensions['E'].width = 25  # testing_standard
    ws.column_dimensions['F'].width = 20  # testing_specimen_size


def _create_deep_results_sheet(wb, deep_results):
    """Create deep results sheet with formatted welding_params"""
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

    ws = wb.create_sheet("深度结果")

    base_headers = [
        'specimen_id', 'data_features', 'welding_method', 'base_material', 'filler_material',
        'welding_params', 'test_method', 'testing_area', 'testing_standard',
        'testing_specimen_size', 'performance_result_source'
    ]
    headers = _collect_output_headers(deep_results, base_headers)

    # Header style
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    # Write headers
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # Write data
    for row_idx, item in enumerate(deep_results, 2):
        base_material = _get_value(item, 'base_material', [])
        base_material_str = _format_base_material(base_material)

        filler_mat_list = _get_value(item, 'filler_material', [])
        filler_mat_str = _format_filler_material(filler_mat_list)

        welding_params_list = _get_value(item, 'welding_params', [])
        welding_params_str = _format_welding_params_for_excel(welding_params_list)

        row_data = _row_for_headers(
            item,
            headers,
            {
                "base_material": lambda _: base_material_str,
                "filler_material": lambda _: filler_mat_str,
                "welding_params": lambda _: welding_params_str,
            },
        )

        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = thin_border

    # Adjust column widths
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 40
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 30
    ws.column_dimensions['F'].width = 80  # welding_params needs more space
    ws.column_dimensions['G'].width = 20  # testing_area
    ws.column_dimensions['H'].width = 25  # testing_standard


def _format_welding_params_for_excel(welding_params_list):
    """
    Convert welding_params list to string directly without formatting
    """
    if not welding_params_list:
        return ''

    if isinstance(welding_params_list, str):
        return welding_params_list

    # Convert list to string directly using json.dumps for proper serialization
    import json
    try:
        return json.dumps(welding_params_list, ensure_ascii=False)
    except (TypeError, ValueError):
        # Fallback to str() if json.dumps fails
        return str(welding_params_list)


def _format_chemical_composition(chem_comp):
    """Format chemical composition dict for display"""
    if not chem_comp:
        return ''

    if hasattr(chem_comp, 'model_dump'):
        chem_comp = chem_comp.model_dump()

    if isinstance(chem_comp, dict):
        return '; '.join([f"{k}: {v}" for k, v in chem_comp.items() if v])

    return str(chem_comp)


def _get_value(obj, field_name, default=''):
    """Safely get value from object or dict"""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(field_name, default)
    return getattr(obj, field_name, default)


def _as_dict(obj):
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    return getattr(obj, "__dict__", {})


def _collect_dynamic_goal_headers(items, fixed_headers):
    """Collect extra dynamic goal columns from exported items."""
    fixed = set(fixed_headers)
    headers = set()
    for item in items or []:
        for key in _as_dict(item).keys():
            if key not in fixed:
                headers.add(key)
    return sorted(headers)


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
    formatters = formatters or {}
    row = []
    for header in headers:
        if header in formatters:
            row.append(formatters[header](item))
        else:
            row.append(_get_value(item, header, ""))
    return row


def _export_skeleton(skeleton, output_file):
    """Export skeleton table - SkeletonItemHash"""
    if not skeleton:
        return

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)

        writer.writerow([
            'specimen_id',
            'base_material',
            'filler_material',
            'welding_method',
            'data_features',
            'source_quote'
        ])

        for item in skeleton:
            specimen_id = _get_value(item, 'specimen_id', '')

            base_material = _get_value(item, 'base_material', [])
            base_material_str = _format_base_material(base_material)

            filler_mat_list = _get_value(item, 'filler_material', [])
            filler_mat_str = _format_filler_material(filler_mat_list)

            source_quote = _get_value(item, 'source_quote', [])
            source_quote_str = _format_list_field(source_quote)

            writer.writerow([
                specimen_id,
                base_material_str,
                filler_mat_str,
                _get_value(item, 'welding_method', ''),
                _get_value(item, 'data_features', ''),
                source_quote_str
            ])


def _export_material_dimensions(material_dims, output_file):
    """Export material dimension table - MaterialDimensionItemHash"""
    if not material_dims:
        return

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)

        base_headers = [
            'specimen_id',
            'grade',
            'material_type',
            'composition_unit',
            'chemical_composition',
            'material_size',
        ]
        headers = _collect_output_headers(material_dims, base_headers)
        writer.writerow(headers)

        for item in material_dims:
            chem_comp = _get_value(item, 'chemical_composition', None)
            chem_comp_str = _format_chemical_composition(chem_comp)

            writer.writerow(_row_for_headers(
                item,
                headers,
                {"chemical_composition": lambda _: chem_comp_str},
            ))


def _export_sample_facts(sample_facts, output_file):
    """Export sample facts table - SampleFactItemHash"""
    if not sample_facts:
        return

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)

        base_headers = [
            'specimen_id',
            'test_method',
            'welding_params',
            'testing_area',
            'testing_standard',
            'testing_specimen_size',
            'performance_result_source',
        ]
        headers = _collect_output_headers(sample_facts, base_headers)
        writer.writerow(headers)

        for item in sample_facts:
            welding_params_list = _get_value(item, 'welding_params', [])
            welding_params_str = _format_welding_params_for_excel(welding_params_list)

            writer.writerow(_row_for_headers(
                item,
                headers,
                {"welding_params": lambda _: welding_params_str},
            ))


def _export_deep_results(deep_results, output_file):
    """Export deep results table - DeepNestedResultItem"""
    if not deep_results:
        return

    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)

        base_headers = [
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
        headers = _collect_output_headers(deep_results, base_headers)
        writer.writerow(headers)

        for item in deep_results:
            base_material = _get_value(item, 'base_material', [])
            base_material_str = _format_base_material(base_material)

            filler_mat_list = _get_value(item, 'filler_material', [])
            filler_mat_str = _format_filler_material(filler_mat_list)

            welding_params_list = _get_value(item, 'welding_params', [])
            welding_params_str = _format_welding_params_for_excel(welding_params_list)

            writer.writerow(_row_for_headers(
                item,
                headers,
                {
                    "base_material": lambda _: base_material_str,
                    "filler_material": lambda _: filler_mat_str,
                    "welding_params": lambda _: welding_params_str,
                },
            ))


def _format_list_field(value):
    """
    Format list field with backward compatibility for different structures:
    1) [{"key1": "value1"}, {"key2": "value2"}] -> "value1; value2"
    2) [{"name": "key1", "value": "value1"}] -> "key1: value1"
    3) ["item1", "item2"] -> "item1; item2"
    """
    if not value:
        return ''
    if isinstance(value, str):
        return value
    if not hasattr(value, '__iter__') or isinstance(value, (dict,)):
        return str(value)

    parts = []
    for item in value:
        if isinstance(item, dict):
            if len(item) == 1:
                parts.append(next(iter(item.values())))
            elif 'value' in item:
                key = item.get('name', '')
                parts.append(f"{key}: {item['value']}" if key else item['value'])
            else:
                parts.append('; '.join([f"{k}: {v}" for k, v in item.items()]))
        else:
            parts.append(str(item))

    return '; '.join([str(p) for p in parts if p])


def _get_field(obj, field_name):
    """Safely get object attribute, handling multiple possible key names"""
    if obj is None:
        return ''
    if isinstance(obj, dict):
        if field_name in obj:
            return obj[field_name]
        alt_names = {
            'welding_name': ['welding_action', '焊接动作', '焊接动作1', '焊接动作2', 'welding_name'],
            'current': ['current', '电流', '电流 /A'],
            'voltage': ['voltage', '电压', '电压 /V'],
            'heat_input': ['heat_input', '热输入', '热输入量'],
        }
        if field_name in alt_names:
            for alt in alt_names[field_name]:
                if alt in obj:
                    return obj[alt]
        return ''
    return getattr(obj, field_name, '')


def _format_base_material(base_material):
    """
    Format base_material (List[str]) for display.
    Joins list items with ', '. Falls back to str() for unexpected types.
    """
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
    """
    Format filler material with backward compatibility for different structures:
    1) {"welding_name": "...", "grade": "..."}
    2) {"welding_action1": "..."}
    3) {"root pass": "ER50-6"}
    """
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


def process_all_deep_results(root_dir: str = "output_md", output_dir: str = None, use_excel: bool = True):
    """
    处理output_md目录下所有子目录中的deep_result文件夹中的result.json文件

    Args:
        root_dir: 根目录路径，默认为output_md
        output_dir: 输出目录，默认为每个子目录本身
        use_excel: 是否使用Excel格式输出（默认True），否则使用CSV
    """
    root_path = Path(root_dir)

    if not root_path.exists():
        print(f"根目录不存在: {root_dir}")
        return

    processed_count = 0
    error_count = 0

    for subdir in root_path.iterdir():
        if subdir.is_dir():
            deep_result_path = subdir / "05_deep_result" / "result.json"

            if deep_result_path.exists():
                try:
                    print(f"处理: {subdir.name}")

                    with open(deep_result_path, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)

                    if output_dir:
                        output_path = Path(output_dir) / subdir.name
                        output_path.mkdir(parents=True, exist_ok=True)
                    else:
                        output_path = subdir

                    if use_excel:
                        # Export to Excel
                        excel_file = output_path / "extra_data.xlsx"
                        export_to_excel(result_data, str(excel_file))
                        print(f"  成功导出: {excel_file}")
                    else:
                        # Export to CSV
                        class ResultWrapper:
                            def __init__(self, data):
                                self.final_result = data.get('final_result', [])
                                self.skeleton = data.get('skeleton', [])
                                self.material_dimensions = data.get('material_dimensions', [])
                                self.sample_facts = data.get('sample_facts', [])

                        result_wrapper = ResultWrapper(result_data)
                        exported_files = export_to_csv(result_wrapper, str(output_path))
                        print(f"  成功导出 {len(exported_files)} 个CSV文件")

                    processed_count += 1

                except Exception as e:
                    print(f"  处理失败: {e}")
                    import traceback
                    traceback.print_exc()
                    error_count += 1
            else:
                print(f"跳过: {subdir.name} (未找到result.json)")

    print(f"\n处理完成: 成功 {processed_count} 个, 失败 {error_count} 个")


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Export extraction results from result.json files to Excel/CSV')
    parser.add_argument('root_dir', nargs='?', default='output_test', help='Root directory containing subdirectories with result.json files (default: output_test)')
    parser.add_argument('output_dir', nargs='?', default=None, help='Output directory (default: same as input subdirectories)')
    parser.add_argument('--csv', action='store_true', help='Use CSV format instead of Excel')

    args = parser.parse_args()

    process_all_deep_results(args.root_dir, args.output_dir, use_excel=not args.csv)
