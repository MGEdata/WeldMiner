"""
Skeleton Extraction Prompt
Aligned with the Chinese skeleton extraction prompt in task, steps, examples, and output format.
"""

from ..models.data_schemas import format_direct_goal_list, format_sample_user_goal_list

# Output pattern as a string that will be formatted at runtime
OUTPUT_PATTERN = [
    {
        "data_features": "",
        "base_material": [],
        "filler_material": [],
        "welding_method": "",
        "source_quote": []
    }
]

SAMPLE = [
    {
        "data_features": "Base material: [X80M], Filler material: [ER70S, ER80S], Welding method: automatic welding, welding_specimen_number:801101:(Original text), Test method and conditions: transverse tensile, test zone: entire welded joint",
        "base_material": ["X80M"],
        "filler_material": [
            {"Pass 1": "ER70S"},
            {"Pass 2-3": "ER80S"},
            {"Pass 4": "ER80S"},
            {"Pass 5": "ER80S"}
        ],
        "welding_method": "SMAW",
        "source_quote": ["Welding process see Table 2", "Tensile properties see Table 3"]
    },
    {
        "data_features": "Base material: [X80M], Filler material: [Kobe Steel LB52U, Böhler E10018, Böhler E10018], Welding method: SMAW, welding_specimen_number:801101:(Original text), Test method and conditions: -40°C low-temperature impact, flat welding position weld center",
        "base_material": ["X80M"],
        "filler_material": [
            {"Root pass": "Kobe Steel LB52U"},
            {"Hot pass": "Böhler E10018"},
            {"Fill and cap pass": "Böhler E10018"}
        ],
        "welding_method": "SMAW",
        "source_quote": [
            "From the base material, heat-affected zone, and weld of the X80 pipeline steel welded joint, square specimens of size $10 , mm \\times 10 , mm \\times 5 , mm$ were cut by wire cutting.",
            "Using MX-0580 microcomputer-controlled electronic universal material testing machine, the room-temperature tensile properties of pipeline steel and its welded joint specimens with and without electrolytic hydrogen permeation were tested."
        ]
    }
]
SAMPLE1 = [{
      "base_material": [
        "X80"
      ],
      "filler_material": [],
      "welding_method": "Submerged Arc Welding",
      "data_features": "Base material: [X80], Filler material: [], Welding method: Submerged Arc Welding,welding_specimen_number:SAW001, Test conditions and method: slow strain rate tensile testing, strain rate 5e-7 s-1, SRB-inoculated medium, open-circuit potential (no applied CP), temperature 32±2°C (fracture area: HAZ), test zone: the entire welded joint",
      "source_quote": [
        "The welded joints used in this study were sourced from a decommissioned submerged arc welded pipeline in China.",
        "Most of the SSRT samples fractured within WZ",
        "A constant-temperature water bath was used to maintain the experimental temperature at 32 ± 2 °C",
        "The strain rate was set at 5 × 10−7 s−1"
      ]
    },
]
SAMPLE2 = [
  {
    "data_features": "base_material:[L450M], filler_material:[E6010,E81T8-Ni2JH8], welding_method:SMAW+FCAW-S, welding_specimen_number:SMAWFCAW-S001 , test_method_and_conditions:transverse tensile test (GB/T 228.1-2021), specimen_area:entire welded joint",
    "base_material": ["L450M"],
    "filler_material": [{"Pass 1": "E6010"}, {"Passes 2-8": "E81T8-Ni2JH8"}],
    "welding_method": "SMAW+FCAW-S",
    "source_quote": ["Table 3 Hybrid welding process adopted", "Table 4 Welding consumables used in welding test", "Table 7 Transverse tensile test results"]
  },
  {
    "data_features": "base_material:[L450M], filler_material:[ER70S-6,E8018-C3H4R], welding_method:GTAW+SMAW,welding_specimen_number:02, test_method_and_conditions:-10℃ Charpy impact test (GB/T 229-2020), specimen_area:fusion line",
    "base_material": ["L450M"],
    "filler_material": [{"Pass 1": "ER70S-6"}, {"Passes 2-10": "E8018-C3H4R"}],
    "welding_method": "GTAW+SMAW",
    "source_quote": ["Table 3 Hybrid welding process adopted", "Table 4 Welding consumables used in welding test", "Table 10 Impact test results"]
  }
]
SAMPLE3 = [
    {
    "data_features": "Base material: [X80 Nb58], Filler material: [], Welding method: Submerged Arc Welding, welding_specimen_number:SAW001:(Nb58), Test method and conditions: Charpy V-notch impact test at -40°C per ASTM E2298, specimen dimensions 55 mm × 10 mm × 10 mm, notched at fusion line, Test zone: CGHAZ",
    "base_material": ["X80 Nb58"],
    "filler_material": [],
    "welding_method": "Submerged Arc Welding",
    "source_quote": [
        "To investigate the effect of Nb content on the low-temperature impact toughness of the CGHAZs, the low-temperature impact toughness was measured at −40℃ and −60℃ using the standard Charpy V-notch (CVN) test, following ASTM E2298.",
        "The equivalent notching positions in the welded joints of the three X80 pipeline steels are specifically located at the equivalent FL, as shown in Fig. 1.",
        "At FL notching positions, the impact energies are 66 J, 133 J, and 194 J at −40°C",
        "Fig. 6. Impact toughness of three studied samples (Nb58, Nb76 and Nb91)."]
    },
    {
    "data_features": "Base material: [X80 Nb76], Filler material: [], Welding method: Submerged Arc Welding, welding_specimen_number:SAW002:(Nb76), Test method and conditions: Charpy V-notch impact test at -40°C per ASTM E2298, specimen dimensions 55 mm × 10 mm × 10 mm, notched at fusion line, Test zone: CGHAZ",
    "base_material": ["X80 Nb76"],
    "filler_material": [],
    "welding_method": "Submerged Arc Welding",
    "source_quote": [
        "To investigate the effect of Nb content on the low-temperature impact toughness of the CGHAZs, the low-temperature impact toughness was measured at −40℃ and −60℃ using the standard Charpy V-notch (CVN) test, following ASTM E2298.",
        "The equivalent notching positions in the welded joints of the three X80 pipeline steels are specifically located at the equivalent FL, as shown in Fig. 1.",
        "At FL notching positions, the impact energies are 66 J, 133 J, and 194 J at −40°C",
        "Fig. 6. Impact toughness of three studied samples (Nb58, Nb76 and Nb91)."]
    }
]
def get_prompt(raw_text: str | None = None, sample_user_goal=None, sample_direct_goal=None) -> str:
    """Generate the prompt with variables"""
    target_metrics = ", ".join(
        item for item in [format_sample_user_goal_list(sample_user_goal), format_direct_goal_list(sample_direct_goal)] if item
    )
    source_block = ""
    if raw_text:
        source_block = f"\n## Original Text\n{raw_text}\n"
    else:
        source_block = (
            "\n## Source\nThe source document is provided as attached page images. "
            "Extract content from those images.\n"
        )

    return f"""You are a professional data extraction assistant. Please extract ALL welding or thermal simulation specimens skeleton information from the following text.

## Task Goal
Extract all weld specimen skeleton information from the text, ensuring **zero omission** — any region under any welding process, any testing method, and any testing condition must be extracted.

{source_block}
Output sample: {SAMPLE}{SAMPLE1}{SAMPLE2}{SAMPLE3}
---
Chain-of-Thought Reasoning (follow these steps strictly, output fully in <think>)
<think>
Step 1: Identify all distinct welding or thermal simulation processes and post-weld specimens. Different welding parameters of the same welding method constitute multiple welding processes. List all weld passes or welding steps corresponding to each welding process. Welding process includes: base material, filler material(if there is no detailed name for the welding materials in the text, the method of representing the welding materials in the text, such as WM, will be used directly), welding parameters, and welding specimen number (prioritize using the welding test numbers from the document; if none exist, customize the numbers. The welding specimen number format is welding method + serial number + reason for numbering, e.g., SMAW001:(Nb58), BOP001:(laboratory-developed electrode 1), TIG001:(Type A, JA), etc.). Each data item must have only one identifier; do not use expressions containing multiple identifiers such as Y1/Y2, Y1,Y2, etc. If the original text contains multiple identifiers, they must be separated. List all source information locations here. If no welding process is found, output an empty list directly and do not proceed with subsequent steps.
Step 2: Identify ALL test methods applied to post-weld or thermal simulation specimens. List all source information locations here.
Step 3: List the data produced by each test method and determine whether it is intended to produce any user target metric: {target_metrics}. Retain the test method if it measures, plots, compares, or discusses a target metric, even when no numerical value is provided in the text/table and the result only appears in a figure.Discard a test method only if it is unrelated to all target metrics or appears only as background/literature discussion rather than an experiment in this paper.Do NOT discard a test method because the target metric is figure-only, qualitative, or non-numeric at this stage. 
Step 4: Identify the test conditions corresponding to each data entry,the testing conditions need to be separated, and each data can only correspond to one testing condition. For example, multiple testing temperatures, pressures, etc. must not appear simultaneously,and calculate the number of specimens under each test condition, without omitting any welding process, including welding testing or welding screening processes — such as surfacing tests, fillet weld tests, cruciform joint tests, and other welding tests.
Step 5: Determine whether each performance test includes multiple specimen regions (e.g., base metal, HAZ, weld metal, upper part of weld, etc.). If multiple test regions are included, identify all regions and distinguish them one by one; each region must be processed independently. For hardness testing, if the text mentions more specific location details than the conventional regions (WM/BM/HAZ) (e.g., upper surface of base metal, lower surface of HAZ, 2 mm from the fusion line, etc.), further refine and annotate the specific test regions.  If there are multiple parallel specimens for each region (e.g., C-1, C-2), still combine these parallel specimens into one specimen entry.
Step 6: Associate welding processes, test methods, test conditions, and test zones. Calculate the expected specimen count ("actual generated specimen count").
Step 7: Construct an independent skeleton entry for each specimen. For each welding process, each condition combination, and each zone, create an independent identification entry — all content must follow the original text.
data_features: str MUST include: base material, filler material, welding method, welding specimen number, test method and conditions, specimen zone
base_material: list(str) The base material names mentioned in this welding process,if the same grade but differ in elements,list the symptom (e.g., "X80 Nb76" vs "X80 Nb58").
filler_material: List[dict(str,str)] The key of each dict is the welding method or weld bead/step name (specific weld bead or welding step must not be omitted), and the value is the name of the welding material used for that method/step. Each value can only contain one welding material name. If there are multiple welding material names, multiple key value pairs will be generated.
welding_method: str The welding method type for this specimen. If the specimen has not been welded, fill in "None".
source_quote: List[str] Source statements for each element of this welding process (for charts, use chart titles only)
Note: This stage ONLY constructs specimen identification info (base_material, filler_material, welding_method, data_features). Do NOT extract specific test values for the user target metrics ({target_metrics}); those values will be extracted by downstream steps.
Reflection & Verification Phase (Self-Check) Before final output, verify the following checkpoints against Steps 1-7 one by one, ensuring each step's results are correctly passed to the next:
Checkpoint 1 (maps to Step 1 - Welding Processes): Did I miss any welding or thermal simulation process? Do the extracted base material, filler material, welding parameters, and welding specimen number actually participate in this welding process, and are any of them missing or wrong? Did I check all possible welding test IDs? Is each welding specimen number unique?  If omission risk exists, mark in <think> and re-scan!
Checkpoint 2 (maps to Step 2 - Test Methods): Did I miss any test method? Did I exhaustively list all test types in the text that may contain the user target metrics ({target_metrics})? If omission risk exists, mark in <think> and re-scan!
Checkpoint 3 (maps to Step 3 - Data Validity): Does each test method's data contain user target metrics ({target_metrics})? Have test methods without target metrics been correctly discarded? If data contains multiple parallel specimens, have they been correctly merged? Is the valid specimen count correct? If errors exist, mark in <think> and correct!
Checkpoint 4 (maps to Step 4 - Test Conditions): Are test conditions complete for each data point? Did I miss temperature, loading rate, specimen dimensions, or other critical conditions? If omission risk exists, mark in <think> and re-scan!
Checkpoint 5 (maps to Step 5 - Specimen Zones): Are specimen zones correctly identified? Are multiple specimen zones processed independently? Has the data from multiple parallel specimens in each zone been correctly merged? If omission risk exists, mark in <think> and re-scan!
Checkpoint 6 (maps to Step 6 - Associations): Are the associations between welding processes, test methods, test conditions, and test zones correct? Is there any misassignment (e.g., process A's data assigned to process B)? If misassignment found, mark in <think> and correct!
Checkpoint 7 (maps to Step 7 - Skeleton Entries): Does the count match? Does the actual number of generated specimens equal the expected count from Step 6? Is each skeleton entry's data_features complete (base material, filler material, welding method, test conditions, specimen zone)? Is the matching of welding consumables with each welding step correct?If count mismatch or field missing, list gaps in <think> and supplement!
Counterfactual Verification (Deep Anti-Omission Check): "If I extracted N specimens but expected M, where in the source document might the missing (M-N) specimens be hiding?" "Are there references like 'see Table X', 'as shown in Figure Y' pointing to data I haven't examined?" "Are there multiple test data sets for the same specimen where I wrongly treated each parallel specimen as a separate entry?" "Are there additional specimen data hidden in table footnotes, supplementary materials, or chart annotations?" Explicitly answer these questions in <think>.
Backtracking: Checkpoint 1 failed → return to Step 1 re-scan welding processes; Checkpoint 2 failed → return to Step 2 re-scan test methods; Checkpoint 3 failed → return to Step 3 re-screen valid data; Checkpoint 4 failed → return to Step 4 re-identify test conditions; Checkpoint 5 failed → return to Step 5 re-identify specimen zones; Checkpoint 6 failed → return to Step 6 re-associate; Checkpoint 7 failed → return to Step 7 re-construct skeleton entries; Counterfactual failed → return to Step 1 full re-scan. Proceed to next checkpoint only after current one passes.
Output Format: Split your response into two parts: think process <think> and final JSON array <output>
</think> [Output your complete chain-of-thought reasoning here, including all step content and checkpoint results. This section is for traceability and debugging.]
<output> [Output ONLY the final JSON array here. No extra text.]
{OUTPUT_PATTERN}
</output> If no data, output an empty array [] in <output>.
"""
