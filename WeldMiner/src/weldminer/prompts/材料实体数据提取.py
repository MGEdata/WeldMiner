"""
中文材料实体数据提取提示词
与英文版 material_dimension.py 的任务、步骤、示例和输出格式对齐。
"""

import json

from ..models.data_schemas import build_material_dimension_output_pattern, format_direct_goal_list, format_material_user_goal_list


SAMPLE_BASE_METAL = {
    "grade": "X80",
    "material_type": "base_metal",
    "composition_unit": "wt%",
    "chemical_composition": {
        "C": "0.052",
        "Si": "0.13",
        "Mn": "1.56",
        "P": "0.012",
        "S": "0.003",
        "Nb": "0.099",
        "Ti": "0.012",
        "Cr": "0.23",
        "Ni": "0.14",
        "Cu": "0.25",
        "Mo": "0.0006",
    },
    "material_size": "D1219 mm×22 mm",
    "tensile_strength_name": "Tensile Strength",
    "tensile_strength_value": "654",
    "tensile_strength_unit": "MPa",
    "yield_strength_name": "Yield Strength",
    "yield_strength_value": "616",
    "yield_strength_unit": "MPa",
    "elongation_name": "Elongation",
    "elongation_value": "35.5",
    "elongation_unit": "%",
}

SAMPLE_FILLER = {
    "grade": "ER70S-6",
    "material_type": "filler",
    "composition_unit": "wt%",
    "chemical_composition": {"C": "0.08", "Si": "0.85", "Mn": "1.45", "P": "0.015", "S": "0.012", "Cu": "0.35"},
    "material_size": "1mm",
    "tensile_strength_name": "Tensile Strength",
    "tensile_strength_value": "550",
    "tensile_strength_unit": "MPa",
    "yield_strength_name": "Yield Strength",
    "yield_strength_value": "480",
    "yield_strength_unit": "MPa",
    "elongation_name": "Elongation",
    "elongation_value": "28",
    "elongation_unit": "%",
    "hardness_name": "Hardness",
    "hardness_value": "232",
    "hardness_unit": "HV10",
    "impact_work_name": "Impact Energy",
    "impact_work_value": "300",
    "impact_work_unit": "J",
}


def get_prompt(
    grade: str,
    material_type: str,
    distinguishing_factor: str,
    raw_text: str | None = None,
    material_user_goal=None,
    material_direct_goal=None,
) -> str:
    """Generate Chinese prompt with optional source text."""
    output_pattern = json.dumps(
        build_material_dimension_output_pattern(material_user_goal, material_direct_goal),
        ensure_ascii=False,
        indent=2,
    )
    material_user_goal_text = format_material_user_goal_list(material_user_goal)
    material_direct_goal_text = format_direct_goal_list(material_direct_goal) or "None"
    source_block = (
        f"\n## 原始文本\n{raw_text}\n"
        if raw_text
        else "\n## 数据来源\n源文档以页面图片形式提供，请基于附图完成提取。\n"
    )
    material_desc = "母材 (base metal)" if material_type == "base_metal" else "焊材/填充材料 (filler)"
    sample = output_pattern

    return f"""你是一名材料数据抽取专家，具备严格的材料隔离意识，并且对虚构数据零容忍。请从以下文本中抽取：焊接或热模拟前，原始母材与焊材（即未受热循环影响的材料）的实体数据。
---
## 任务目标
抽取焊接或热模拟加工前目标材料 "{grade}"（类型: {material_desc}）的化学成分和力学性能数据。
材料实体结构化抽取目标: {material_user_goal_text}。每个结构化目标必须由三个输出字段表示：<goal>_name、<goal>_value、<goal>_unit。
材料实体直接抽取目标: {material_direct_goal_text}。每个直接目标必须由一个名为 <goal> 的字段表示，值为从源文档复制出的一个完整字符串。
{source_block}
输出示例: {sample}
---
思维链推理过程（请严格按以下步骤执行，并完整输出在 <think> 中）
<think>
步骤1：精确锚定。扫描源文本中目标材料 "{grade}" 的所有出现位置。如果 "{grade}" 没有精确出现，则进行语义等价匹配，寻找与 "{grade}" 关联的材料名称或者对应的标准数据。例如："Lab-Developed Electrode #5" 后面的数字5对应5号焊材；焊材S2MO无明确成分信息，但是其符合EA2标准焊丝且文中存在标准的成分范围。若既无精确匹配，也无合理语义等价证据 -> 标记 TARGET_NOT_FOUND，跳过后续步骤，并直接输出空字典 {{}}。确认包含该材料牌号的表格/段落边界，并标记同一区域内的其他材料牌号（潜在干扰项）。
步骤2：材料隔离与污染检查。列出源文本中所有其他材料牌号（例如 X70、E5015 等），并确认其数据已被排除。识别与 "{grade}" 相似的牌号（例如 X80 vs X80 Nb53），确认没有混淆。每个待抽取值必须与 "{grade}" 标识位于同一行/同一单元格；不要误抽表头或相邻行数据。如果 {material_type}=filler，必须确认来源明确标注为“熔敷金属”“焊丝”“焊材”等，而不是母材数据。识别该材料数据是否为原始材料实体数据，而不是特殊试验条件下生成的试样数据。列出 OUTPUT_PATTERN 中未在源文档找到的字段（最终 JSON 中需要删除）。
步骤3：纯数据抽取。化学成分：元素符号 -> 数值（例如 "C": "0.052"），保留原文格式（范围保持范围，单值保持单值），如同时存在实验值和标准值范围，优先提取实验值。力学性能：name 字段必须使用原文精确表达（例如 "specified plastic extension strength Rp0.2"），不要简化为“屈服强度”。数值应为纯数字字符串，单位必须与原文严格一致（MPa vs GPa，% vs J）。material_size：抽取尺寸规格（例如 "D1219 mm×22 mm"、"φ1.2mm"）。grade 字段必须严格使用输入值 "{grade}"，不要改变大小写或缩写,如果同一样品标识下存在多个平行实验（例如 C-1、C-2），抽取所有平行样数据。若存在多个平行样数据，以字符串形式填写，例如 'parallel:518.42,519.79,517.13'。若正文同时给出多条平行样数据及平均值，需要额外标注，例如 'parallel:80.93,80.80,81.13;average:80.95'。。
步骤4：最终清理。删除所有值为 "" 或未找到的键值对。确认没有 "not provided"、"null" 等占位文本。重新扫描已抽取值，确认没有来自步骤2所列其他材料的数据污染。确认结构符合 OUTPUT_PATTERN。若步骤1标记 TARGET_NOT_FOUND，则输出空字典 {{}}。
反思验证阶段（自检）：最终输出前，请严格验证以下内容。
检查点1（对应步骤1-精确锚定）：是否遗漏 "{grade}" 的任何出现位置？是否遗漏表格、段落或图表？若存在遗漏风险，请在 <think> 中标记并重新扫描。
检查点2（对应步骤2-材料隔离）：是否排除了所有其他牌号的数据？是否存在相似牌号混淆？每个数值是否严格位于目标牌号的同一行/同一单元格？是否错误抽取了焊后试样数据，而不是焊接过程中的材料实体（母材、焊材）数据？若存在污染风险，请修正。
检查点3（对应步骤3-纯数据抽取）：化学成分和力学性能数据是否完整？name 字段是否使用原文精确表达（无简化）？数值和单位是否严格匹配原文？grade 是否严格等于 "{grade}"？若发现问题，请修正。
检查点4（对应步骤4-最终清理）：是否删除了所有空值？是否仍有其他材料污染？结构是否符合 OUTPUT_PATTERN？若发现问题，请修正。
回溯要求：检查点1失败 -> 回到步骤1；检查点2失败 -> 回到步骤2；检查点3失败 -> 回到步骤3；检查点4失败 -> 回到步骤4。当前检查点通过后才能进入下一检查点。
输出格式：回复必须分为两部分：思考过程 <think> 和最终 JSON 对象 <output>
</think> [在此完整输出思维链推理过程，包括所有步骤内容和检查点结果。该部分用于可追溯性和调试。]
<output> [这里只输出最终 JSON 对象，不要包含任何额外文本。]
{output_pattern}
</output> 若无数据，请在 <output> 中输出空字典 {{}}。
"""
