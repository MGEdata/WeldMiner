"""
Sample Fact Extraction Prompt
Full COT + Reflection architecture, symmetric with Chinese version.
"""

import json

from ..models.data_schemas import build_sample_user_goal_output_pattern


weld_param_sample1 = [
    {
        "root_pass": {
            "polarity": "DCEP",
            "current /A": "80~100",
            "voltage /V": "21~26",
            "travel_speed /(cm·min-1)": "6~8",
            "heat_input /(kJ·cm-1)": "16.2~20.1"
        },
        "hot_pass": {
            "polarity": "DCEP",
            "current /A": "80~100",
            "voltage /V": "21~26",
            "travel_speed /(cm·min-1)": "6~8",
            "heat_input /(kJ·cm-1)": "16.2~20.1"
        },
        "fill_pass": {
            "polarity": "DCEP",
            "current /A": "170~230",
            "voltage /V": "20~27",
            "travel_speed /(cm·min-1)": "15~20",
            "heat_input /(kJ·cm-1)": "13.7~18.5"
        },
        "cap_pass": {
            "polarity": "DCEP",
            "current /A": "170~230",
            "voltage /V": "20~27",
            "travel_speed /(cm·min-1)": "12~16",
            "heat_input /(kJ·cm-1)": "17.1~23.1"
        }
    }
]
weld_param_sample2 = [
  {"pre-weld conditions": {
      "groove type": "single-sided 30° V-groove",
      "number of layers": "6",
      "number of passes": "9",
      "preheat temperature /°C": "105~110",
      "interpass temperature (peak) /°C": "105~132",
      "ambient temperature /°C": "20"
    }},
  {
    "pass 1": {
      "current /A": "132~137",
      "voltage /V": "12.6~14.7"
    }
  },
  {
    "pass 2": {
      "current /A": "106",
      "voltage /V": "20.0"
    }
  },
  {
    "passes 3-6": {
      "current /A": "118",
      "voltage /V": "22.1"
    }
  },
]

weld_param_sample3 = [
  {"pre-weld conditions": 
  {"groove type": "X-groove", "groove angle /°": "45", "number of passes": "2","annealing temperature /°C": "560–575"}},
    {"Submerged Arc Welding": 
        {"voltage /V": "28–30",
        "current /A": "430~530",
        "heat_input /(kJ·cm-1)": "35",
        "welding_speed /(cm·min-1)": "33"
        }
    }
]
weld_param_sample4 = [
    {"rotation_rate_rpm": "100",
     "traverse_speed_mm_per_min": "100", 
     "tool_tilt_angle_deg": "3", 
     "axial_load_kN": "41.2", 
     "peak_temperature_C": "632"}
     ]
weld_param_sample5 =[
  {
    "Pre-weld Preparation": {
      "Groove Type": "V-groove",
      "Preparation Method": "Machining",
      "Cleaning Requirement": "Both sides of the groove, within 20 mm, free of oil, rust, oxide scale, and other contaminants",
      "Assembly Method": "Manual assembly, tack welding for fixation",
      "Preheating Method": "Flame heating"
    },
    "Root Pass": {
      "Polarity": "DCEP",
      "Welding Current /A": "150~160",
      "Arc Voltage /V": "9~11",
      "Gas Flow Rate /(L·min⁻¹)": "9~11",
      "Average Travel Speed /(cm·min⁻¹)": "5.5",
      "Heat Input /(kJ·mm⁻¹)": "1.47~1.75",
      "Preheat/Interpass Temperature /°C": "100~110",
      "Thickness Control": "2.5~3.5 mm"
    },
    "Filler Pass": {
      "Polarity": "DCEN",
      "Welding Current /A": "100~110",
      "Arc Voltage /V": "20~24",
      "Average Travel Speed /(cm·min⁻¹)": "11.2",
      "Heat Input /(kJ·mm⁻¹)": "1.07~1.42",
      "Preheat/Interpass Temperature /°C": "120~130"
    },
    "Cap Pass": {
      "Polarity": "DCEN",
      "Welding Current /A": "90~100",
      "Arc Voltage /V": "18~22",
      "Average Travel Speed /(cm·min⁻¹)": "6.7",
      "Heat Input /(kJ·mm⁻¹)": "1.45~1.97",
      "Preheat/Interpass Temperature /°C": "140~160"
    },
    "Post-weld Heat Treatment": {
      "Heating Method": "Electric heating tape",
      "Heating Process (300~630°C)": "Heating rate ≤ 130 °C/h",
      "Holding": "630 °C, hold for 1 h",
      "Cooling Process (630~300°C)": "Cooling rate ≤ 110 °C/h",
      "Final Cooling": "Free cooling to room temperature after power-off below 300°C"
    }
  }
]
weld_param_sample6 = [
  {
    "Laser-MAG hybrid welding": {
      "laser_power /W": "3700",
      "MAG_current /A": "150",
      "defocus_distance /mm": "-1",
      "laser_wire_distance /mm": "2",
      "welding_speed /(mm·min⁻¹)": "1000",
      "root_face /mm": "3",
      "upper_groove_angle /°": "30",
      "lower_groove_angle /°": "20",
      "shielding_gas": "80% Ar + 20% CO₂",
      "gas_flow_rate /(L/min)": "20",
      "welding_wire_type": "ER80S-G",
      "wire_diameter /mm": "1.2"
    }
  }
]
weld_param_sample7 = [
  {"thermal_simulation": {"first_peak_temperature_degC": "1350", "second_peak_temperature_degC": "1100"}}
]
weld_param_sample8 = [
{"Thermal Simulation": {"heat_input /(kJ·cm⁻¹)": "20", "heating_rate /(°C·s⁻¹)": "130", "peak_temperature /°C": "1300", "residence_time_at_high_temperature /s": "1", "t8/5 /s": "7.57"}}
]
def get_prompt(
    base: str,
    filler_json: str,
    welding_method: str,
    factors: str,
    raw_text: str | None = None,
    sample_user_goal=None,
    sample_direct_goal=None,
) -> str:
    """Generate the prompt with variables"""
    output_pattern = json.dumps(build_sample_user_goal_output_pattern(sample_user_goal, sample_direct_goal), ensure_ascii=False, indent=2)
    if raw_text:
        source_block = f"Source text: {raw_text}"
    else:
        source_block = (
            "Source text: The source document is attached as page images. "
            "Extract content from those images."
        )

    return f"""You are a professional post-weld specimen data extraction assistant. Please extract welding parameters and performance data for the specified sample from the source document.

## Task Goal
Strictly extract welding parameters and performance data for the post-weld test specimen identified by `{factors}` from the source document. Ensure **single-specimen isolation** — only extract data for THIS specimen, do NOT mix in data from other batches or other specimens.

## Input Information
- Base material: {base}
- Filler material: {filler_json}
- Welding method: {welding_method}
- Sample identifier: {factors}
- {source_block}

Sample fact extraction target template:
{output_pattern}
Treat this as one unified output template. Extract only the fields shown in this template. For target fields that use the `<goal>_name`, `<goal>_value`, and `<goal>_unit` pattern, keep the original performance name, value, and unit separately. For target fields without that suffix pattern, fill the field with the exact source content as one string.
For `performance_result_source`, fill the section number, figure number, or table number that contains the performance results for this exact test method and sample condition, such as "Fig. 3b" or "Supplementary Fig. S4a"; if multiple result sources apply, separate them with semicolons.
Mandatory consistency rule: figure numbers are valid `<goal>_value` values when the requested data is not available in text but may exist in an image. If the data exists in a table, extract the actual table data directly; do not fill a table number as the value. If there is no explicit data and the data may exist in an image listed in `performance_result_source`, copy the most specific relevant figure number into that `<goal>_value` field. For tensile or SSRT specimens, stress-strain/tensile-curve figure sources must be copied to `tensile_strength_value` and `yield_strength_value`; elongation or SCC-index figure sources must be copied to `elongation_value`; reduction-of-area figure sources must be copied to `reduction_of_area_value`. Do not omit these value fields merely because no numerical value is available.

Welding parameter reference examples:
- Multi-layered examples: {weld_param_sample1}{weld_param_sample2}{weld_param_sample5}
- Single-layered examples: {weld_param_sample3}{weld_param_sample4}{weld_param_sample6}
- Thermal simulation examples: {weld_param_sample7}{weld_param_sample8}
---

Chain-of-Thought Reasoning (follow these steps strictly, output fully in <think>)
<think>
Step 1: Data Localization - Record the source location of each data value generated from the performance test conducted on the sample identifier `{factors}` (e.g., ["Table 3, row 2", "Section 4.1"]). Welding parameter source location: ___________; Performance data source location: ___________.
Step 2: Sample Filtering & Isolation - Clearly state: "Currently extracting data for sample `{factors}`". For tensile or SSRT specimens, it is not necessary to separate the replicate data based on the fracture zone as the test area for the same specimen. Instead, 'entire welded joint' should be uniformly entered in the test area field.Other sample identifiers already excluded: ___________; Exclusion rationale: ___________. Ensure you exclude any data related to base material or filler material that is NOT from this specific welding process specimen. 
Step 3: Welding Parameter Extraction Extract all welding parameter data or thermal simulation and other processing data that were performed to produce the specimen: {factors},If the document does not explicitly provide a corresponding welding specimen number, then look for welding test parameters that are semantically associated with it. For example, welding specimen number GMAW01 corresponds to welding sample 1 in the document. If there are multiple steps of different processes or parameter differences within the same process, hierarchical extraction shall be performed. Identify the parameter differences between each process action and determine whether hierarchical extraction is necessary based on the specific parameter differences. Do not overlook differences in specific process parameters simply because certain process elements (such as filler metal) are the same; similarity does not allow merging; only identical parameters can be merged. Extract not only welding parameters from tables but also welding-related process parameters described in the text,Welding parameters need to include "pre-weld conditions" (groove shape and angle, number of welding layers and passes,pre-weld heat treatment parameters etc.) and "post-weld treatment" (heat treatment parameters such as post-weld heat treatment temperature and time, or other post-weld treatments). The regions referred to in the sample identification are all constituent zones of the welded joint after welding. Therefore, even the base metal is part of the post-weld specimen, and the processing parameters of this welded sample should be extracted. If relevant welding parameters are present in the text, they must be extracted and output; otherwise, output a null value for this field. Welding parameter extraction result: ___________.
Step 4: Performance Data Extraction - If there are multiple parallel experiments under the same sample identifier (e.g., C-1, C-2, etc.), extract the data of all parallel samples. If there are multiple parallel sample data, fill in the data in string form as follows: 'parallel:518.42,519.79,517.13'. If there are multiple parallel sample data with the average value in the text, additional annotations should be made, such as 'parallel:80.93,80.80,81.13;average:80.95'. If the data does not exist in the text but may be present in an image, the figure number of the image must be filled in and cannot be left blank. Note: do not fill in table numbers as data values; if data exists in a table, extract the actual data directly. If there is no data and the data cannot exist in an image either, leave it empty. For example, if a stress-strain curve exists and the tensile properties are not found in the text, then for any tensile specimen, regardless of the specimen region, the figure number of the stress-strain curve must be entered in place of the specific numerical values for yield strength, tensile strength, and elongation. Do NOT extract performance data unrelated to the test method in this sample identifier — leave such fields empty. Retain the EXACT original name (e.g., "specified plastic extension strength Rp0.2"), do NOT simplify. Extracted performance data list: ___________; Uncertain items (e.g., unit might be kJ/mm or kJ/cm): ___________.
Step 5: consistency check: First fill `performance_result_source`, then verify every relevant `<goal>_value`. If it has no explicit data, the data may exist in an image, and that source is listed in `performance_result_source`, the value field must contain that figure number, not null, empty, or omitted.
Step 6: Null Value Removal & Final Cleanup - Which fields are NOT mentioned in the source and must be deleted? Are unmentioned fields already removed from the output? Ensure final JSON has no empty-value keys.
Reflection & Verification Phase (Self-Check) Before final output, strictly verify the following:
Checkpoint 1 (maps to Step 1 - Data Localization): Is the source location of EVERY value recorded? Are there any values without source annotation? If omission risk exists, mark in <think> and re-scan!
Checkpoint 2 (maps to Step 2 - Sample Filtering & Isolation): Is the extraction strictly filtered by `{factors}`? Have ALL other sample identifiers been excluded? Ensure the data ONLY contains data related to this welded specimen, without any data related to base material or filler material entities themselves. If other sample data was mixed in, mark in <think> and correct!
Checkpoint 3 (maps to Step 3 - Welding Parameter Extraction): Are parameters for each welding pass correctly separated by differences? Are there any missed welding passes? Are there any welding parameters described in text paragraphs that were not extracted? Does this sample have welding parameters that were available but not extracted? Does the output result include filler metal information? If omissions or layering errors exist, mark in <think> and correct!
Checkpoint 4 (maps to Step 4 - Performance Data Extraction): Do performance data names retain the EXACT original expression? Do values and units strictly match the original? Is there any unit confusion (e.g., kJ/mm vs kJ/cm)? Does the extracted data include data from ALL parallel experiments? Did I incorrectly extract parallel specimen data from other samples?Is there an average value in the parallel experiment data that has not been retained and annotated separately? Is there any data that only exists in the image without filling in the image number? If issues found, mark in <think> and correct!
Checkpoint 5 (maps to Step 5 - Consistency Check): Is the performance result source filled in for every relevant `<goal>_value`? If not, mark in <think> and correct!
Checkpointer 6 (maps to Step 6 - Null Value Removal & Final Cleanup): Have ALL unmentioned fields been removed? Is the output free of empty-value keys? If issues found, mark in <think> and correct!
Backtracking: Checkpoint 1 failed → return to Step 1 re-localize; Checkpoint 2 failed → return to Step 2 re-filter; Checkpoint 3 failed → return to Step 3 re-extract welding parameters; Checkpoint 4 failed → return to Step 4 re-extract performance data; Checkpoint 5 failed → return to Step 5 re-clean. Proceed to next checkpoint only after current one passes.
Output Format: Split your response into two parts: think process <think> and final JSON object <output>
</think> [Output your complete chain-of-thought reasoning here, including all step content and checkpoint results. This section is for traceability and debugging.]
<output> [Output ONLY the final single JSON object here. No extra text.]
{output_pattern}
</output> If no data, output an empty object {{}} in <output>.
"""
