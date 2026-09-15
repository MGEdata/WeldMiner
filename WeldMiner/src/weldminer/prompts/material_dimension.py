"""
Material Dimension Extraction Prompt
Aligned with the Chinese material entity extraction prompt.
"""

import json

from ..models.data_schemas import build_material_dimension_output_pattern, format_direct_goal_list, format_material_user_goal_list

SAMPLE_BASE_METAL = {
    "grade": "X80",
    "material_type": "base_metal",
    "composition_unit": "wt%",
    "chemical_composition": {"C": "0.052", "Si": "0.13", "Mn": "1.56", "P": "0.012", "S": "0.003", "Nb": "0.099", "Ti": "0.012", "Cr": "0.23", "Ni": "0.14", "Cu": "0.25", "Mo": "0.0006"},
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
    """Generate the prompt with variables"""
    output_pattern = json.dumps(build_material_dimension_output_pattern(material_user_goal, material_direct_goal), ensure_ascii=False, indent=2)
    material_user_goal_text = format_material_user_goal_list(material_user_goal)
    material_direct_goal_text = format_direct_goal_list(material_direct_goal) or "None"
    raw_text_block = ""
    if raw_text:
        raw_text_block = f"\n## Raw Text\n{raw_text}\n"
    else:
        raw_text_block = (
            "\n## Source\nThe source document is provided as attached page images. "
            "Extract content from those images.\n"
        )

    sample = output_pattern

    # Material type description
    material_desc = "base metal (母材)" if material_type == "base_metal" else "filler/welding material (焊材/填充材料)"

    return f"""You are a material data extraction expert with strict material isolation awareness and zero tolerance for fabricated data. Please extract entity data of the raw materials (base metal or filler metal) prior to welding or heat simulation from the following text.
---
## Task Goal
Extract chemical composition and mechanical property data for the target material "{grade}" (type: {material_desc}) prior to welding or heat treatment.
Structured material entity extraction goals: {material_user_goal_text}. Each structured goal must be represented by three output fields: <goal>_name, <goal>_value, and <goal>_unit.
Direct material entity extraction goals: {material_direct_goal_text}. Each direct goal must be represented by exactly one output field named <goal>, with the value copied from the source as one string.
{raw_text_block}
Output sample: {SAMPLE_BASE_METAL}{SAMPLE_FILLER}
---
Chain-of-Thought Reasoning (follow these steps strictly, output fully in <think>)
<think>
Step 1: Scan the source text for all occurrences of the target material "{grade}". If "{grade}" does not appear exactly, perform semantic equivalence matching to find material names associated with "{grade}" or corresponding standard data. For example: the number 5 in "Lab-Developed Electrode #5" corresponds to welding material No. 5; the welding material S2MO has no explicit composition information, but it complies with the EA2 standard wire and the standard composition range exists in the text. If there is neither an exact match nor reasonable semantic equivalence evidence → mark TARGET_NOT_FOUND, skip subsequent steps, and directly output an empty dictionary {{}}. Confirm the table/paragraph boundaries containing this material grade, and mark other material grades within the same region (potential interfering items).
Step 2: Material Isolation & Contamination Check - List ALL other material grades in the source text (e.g., X70, E5015, etc.) and confirm their data has been excluded. Identify similar grades to "{grade}" (e.g., X80 vs X80 Nb53) and confirm no confusion. Each value to be extracted MUST be in the same row/cell as the "{grade}" identifier — do NOT accidentally extract headers or adjacent row data. If {material_type}=filler, confirm the source explicitly labels "deposited metal", "welding wire", "welding consumable", or similar wording, NOT base metal data. Identify whether the source of this material data is original material entity data, rather than sample data generated under special test conditions. List any OUTPUT_PATTERN fields not found in the source (to be deleted from final JSON).
Step 3: Pure Data Extraction - Chemical composition: element symbol → value (e.g., "C": "0.052"), preserve original format (ranges stay as ranges, single values stay as single values),If there are experimental and standard value ranges at the same time, prioritize extracting experimental values. Mechanical properties: name field MUST use the EXACT original expression (e.g., "specified plastic extension strength Rp0.2"), do NOT simplify to "yield strength". Values as pure numeric strings, units strictly match the original (MPa vs GPa, % vs J). material_size: extract dimension specs (e.g., "D1219 mm×22 mm", "φ1.2mm"). grade field: strictly use input value "{grade}" — no case conversion or abbreviation. If there are multiple parallel experiments under the same sample identifier (e.g., C-1, C-2, etc.), extract the data of all parallel samples. If there are multiple parallel sample data, fill in the data in string form as follows: 'parallel:518.42,519.79,517.13'. If there are multiple parallel sample data with the average value in the text, additional annotations should be made, such as 'parallel:80.93,80.80,81.13;average:80.95'.
Step 4: Final Cleanup - Delete all key-value pairs where value is "" or not found. Confirm no placeholder text like "not provided" or "null". Re-scan extracted values to confirm no contamination from materials listed in Step 2. Confirm structure matches OUTPUT_PATTERN. If Step 1 marked TARGET_NOT_FOUND, output empty dict {{}}.
Reflection & Verification Phase (Self-Check) Before final output, strictly verify the following:
Checkpoint 1 (maps to Step 1 - Precise Anchoring): Did I miss any occurrence of "{grade}"? Are there overlooked tables/paragraphs/charts? If omission risk exists, mark in <think> and re-scan!
Checkpoint 2 (maps to Step 2 - Material Isolation): Have ALL other grade data been excluded? Is there any similar-grade confusion? Is each value strictly in the same row/cell as the target grade? Has the data of the test samples generated after welding been extracted instead of the material entity (base metal, welding material) data during the welding process? If contamination risk exists, mark in <think> and correct!
Checkpoint 3 (maps to Step 3 - Pure Data Extraction): Is the chemical composition and mechanical property data complete? Does the name field use the EXACT original expression (no simplification)? Do values and units strictly match the original? Does grade strictly equal "{grade}"? If issues found, mark in <think> and correct!
Checkpoint 4 (maps to Step 4 - Final Cleanup): Have ALL empty values been removed? Is there any residual contamination from other materials? Does the structure match OUTPUT_PATTERN? If issues found, mark in <think> and correct!
Backtracking: Checkpoint 1 failed → return to Step 1; Checkpoint 2 failed → return to Step 2; Checkpoint 3 failed → return to Step 3; Checkpoint 4 failed → return to Step 4. Proceed to next checkpoint only after current one passes.
Output Format: Split your response into two parts: thinking process <think> and final JSON object <output>
</think> [Output your complete chain-of-thought reasoning here, including all step content and checkpoint results. This section is for traceability and debugging.]
<output> [Output ONLY the final JSON object here. No extra text.]
{output_pattern}
</output> If no data, output an empty dict {{}} in <output>.
"""
