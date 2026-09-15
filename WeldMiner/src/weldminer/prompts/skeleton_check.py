from typing import Any, Dict, List, Optional
import json

from ..models.data_schemas import format_direct_goal_list, format_sample_user_goal_list


def _build_source_block(source_text: Optional[str]) -> str:
    if source_text:
        return f"SOURCE DOCUMENT TEXT:\n---\n{source_text}\n---"
    return (
        "SOURCE DOCUMENT:\n---\n"
        "The source document is provided as attached page images. "
        "Use those images as the primary source.\n---"
    )


OUTPUT_PATTERN = {
    "check_passed": bool,
    "problem_description": [],
    "corrected_results": [],
    "false_results": [],
    "missing_items": [],
    "missingitem_source": [],
}

CORRECTION_OUTPUT_PATTERN = [
    {
        "data_features": "",
        "base_material": "",
        "filler_material": [],
        "welding_method": "",
        "source_quote": []
    }
]


def get_skeleton_check_prompt(
    skeleton_json: str,
    source_text: Optional[str],
    COT: str,
    diff_factors_example: str = "",
    sample_user_goal=None,
    sample_direct_goal=None,
) -> str:
    source_block = _build_source_block(source_text)
    target_metrics = ", ".join(
        item for item in [format_sample_user_goal_list(sample_user_goal), format_direct_goal_list(sample_direct_goal)] if item
    )
    cot_block = (
        f"\n3. Model thinking process from the first extraction step: {COT}"
        if COT and COT.strip()
        else ""
    )
    return f"""You are a precise data extraction quality inspector. Your task is to perform **structured verification** on a completed welding data extraction result, NOT to re-extract data.

You will receive the following:
1. {source_block}
2. Skeleton data from the first extraction step: {skeleton_json}{cot_block}

You MUST follow these six steps strictly, outputting your reasoning in <think>. After reasoning, output the final verification report in the specified JSON format.
<think>
Step 1: For each data entry, locate the corresponding data position based on its source_quote field and determine whether the data content is logically valid.
Step 2: At the corresponding text position or source image where the data exists, verify whether the data matches the extracted data or whether the image source is consistent. If inconsistent or not found, record as an error item with the error reason. If uncertain, record as a suspected item with the reason.
Step 3: List ALL test methods and their corresponding data from the source document.
Step 4: For each test method's data, determine if it contains any user target metric: {target_metrics}. If none are present, do not retain that test method.
Step 5: Check whether the received data misses any test method or data that meets the requirements. Parallel specimens within the same welding process, test condition, and test region (for example specimen 1/specimen 2 or C-1/C-2) MUST be merged into one skeleton entry; downstream fact extraction stores all parallel values. Do not report parallel measurements as missing skeleton entries.
Step 6: Build the verification report:
check_passed: bool - Whether all test methods and data meet requirements. False if there are errors or omissions.
corrected_results: list[Dict[str, Any]] - Data entries verified as correct.
false_results: list[Dict[str, Any]] - Data entries verified as incorrect.
problem_description: list[str] - Detailed description of each error, one-to-one with false_results in order. Empty list if there are no errors.
missing_items: list[Dict[str, Any]] - Test methods or data found to be missing.
missingitem_source: list[str] - Source location of each missing item, must be a flat list of strings, one-to-one with missing_items in order.
Reflection & Self-Check Phase Before final output, strictly verify:
Self-Check 1: Is data localization accurate and consistent with the original text? Is the data content logically valid and free of contradiction? If localization errors exist, record as error items. If localization is ambiguous, mark in <think> and re-scan.
Self-Check 2: Do the correct data items meet requirements? If incorrect data exists, record as error items.
Self-Check 3: Did I miss any test method or data? If omission risk exists, mark in <think> and re-scan.
Self-Check 4: Did I only retain test methods and data that meet requirements? If error risk exists, mark in <think> and re-scan.
Self-Check 5: Does the received data miss any test method or data that meets requirements? If omission risk exists, mark in <think> and re-scan.
Self-Check 6: Does the generated verification report meet requirements? Are correct and incorrect data consistent with the received data? If errors exist, mark in <think> and re-scan.
Backtracking: If any self-check fails, return to Step 1 and re-process.
Output Format: Split your response into two parts: thinking process <think> and final JSON object <output>
</think> [Output your complete chain-of-thought reasoning here, including all step content and self-check results. This section is for traceability and debugging.]
<output> [Output ONLY the final JSON object here. No extra text.]
{{
  "check_passed": true/false,
  "problem_description": [],
  "corrected_results": [],
  "false_results": [],
  "missing_items": [],
  "missingitem_source": []
}}
</output> If no data, output an empty array [] in <output>.
"""


def get_skeleton_correction_prompt(
    skeleton_json: str,
    COT: str,
    source_text: Optional[str],
    inspection_data: Dict[str, Any],
    diff_factors_example: str = "",
    lang: str = "en",
) -> str:
    inspection_json = json.dumps(inspection_data, ensure_ascii=False, indent=2)
    source_block = _build_source_block(source_text)
    cot_block = (
        f"\n3. Thinking process from the extraction step: {COT}"
        if COT and COT.strip()
        else ""
    )
    return f"""You are a precise data extraction correction specialist. Your task is to perform **targeted correction** on a completed welding data extraction result based on specific errors and omissions identified in the quality inspection report — NOT to re-extract data.

You will receive the following:
1. Source document: {source_block}
2. Skeleton data from the first extraction step: {skeleton_json}{cot_block}
4. Quality inspection report: {inspection_json} (contains false_results, problem_description, missing_items, missingitem_source)

You MUST follow these six steps strictly, outputting your reasoning in <think>. After reasoning, output the corrected complete skeleton data in the specified JSON format.
<think>
Step 1: Parse error items from the quality inspection report. Review each false_result and its problem_description. Clearly identify each error item and its corresponding error cause.
Step 2: Correct error items one by one. Return to the source document, re-locate the correct data position based on the error type identified in the report. Extract the correct value, ensuring there is a precise source quote as evidence. Directly replace the incorrect value with the correct value in the corresponding position of the first extraction skeleton data.
Step 3: Parse omission items from the quality inspection report. Review each missing_item and its missingitem_source. Create a "to be completed" checklist.
Step 4: Complete missing data item by item. For each item in the checklist, construct a new data entry following the output structure specification of the first extraction model.
Step 5: Handle the newly constructed data entries. Check whether any new entry duplicates existing skeleton data content. If duplicate, delete the new entry. Append remaining new data entries to the end of the skeleton data.
Step 6: Build the corrected complete skeleton data:
Return exactly one complete corrected snapshot, not a delta list. Each semantic specimen must occur once: do not retain both its pre-correction and post-correction versions, and do not append missing_items again after they have been incorporated into the complete snapshot.
data_features: str (MUST include: base material, filler material, welding method, test conditions, specimen zone, and specimen ID)
base_material: List[str] (list of base material grades)
filler_material: List[Dict(str,str)] (each dict key is the welding pass name, value is the filler material grade)
welding_method: str (welding method type for this specimen)
source_quote: List[str] (source statements for each element; for charts, use chart titles)
Note: This stage ONLY constructs specimen identification info (base_material, filler_material, welding_method, data_features, source_quote). Do NOT extract specific test values — those will be extracted by downstream steps.
Reflection & Self-Check Phase Before final output, strictly verify:
Self-Check 1: Have ALL error items been corrected? Verify each false_result entry has been processed (modified or deleted). If any errors remain unprocessed, correct immediately.
Self-Check 2: Do corrected values have source evidence? For each modified field, re-confirm: the new value has an exact reference in the source document. If source evidence cannot be found, mark as "correction failed" and retain original value.
Self-Check 3: Have ALL omission items been found according to the quality inspection report's missing_items and missingitem_source? Do the found items match their source locations?
Self-Check 4: Have ALL omission items been completed? Verify the quality inspection report's missing_items — each must have a corresponding entry in the corrected array. Is source_quote correctly mapped?
Self-Check 5: Check for duplicate entries in the corrected and completed data. Compare semantic identity (base material, filler material, welding method, test condition, and test region), ignoring wording or synthetic-ID changes. Keep only one skeleton entry for parallel measurements in the same region.
Self-Check 6: Output format compatibility — confirm the output is a pure JSON array with the same data structure as the first extraction skeleton data and meets all requirements.
Backtracking:
If Self-Check 1 or Self-Check 4 fails (unprocessed errors or omissions exist), return to Step 1 or Step 3 to re-process.
If Self-Check 2 or Self-Check 3 fails, immediately correct the corresponding fields in the reasoning chain and update Step 6 output; do not restart from the beginning.
If after one backtracking pass there are still unresolved issues (e.g., source ambiguity, missing data), do not loop indefinitely — add a `_verification_note` marker "requires manual review" to the corresponding entry and output.
Output Format: Split your response into two parts: thinking process <think> and final JSON array <output>
</think> [Output your complete chain-of-thought reasoning here, including processing details for each step, correction basis, and self-check results. This section is for traceability and debugging.]
<output> [Output ONLY the corrected complete JSON array here. The structure MUST be identical to the first extraction skeleton_json. No extra text.]
</output> If no data, output an empty array [] in <output>.
"""


def get_prompt(skeleton_json: str, raw_text: str | None, COT: str) -> str:
    """
    Compatibility entry point, equivalent to the English check prompt.
    """
    return get_skeleton_check_prompt(
        skeleton_json=skeleton_json,
        source_text=raw_text,
        COT=COT,
    )
