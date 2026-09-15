PROMPT_TYPE = """Identify which welding stages are explicitly present in the supplied text.
Allowed stage keys: {list_operation}. These are stages, NOT welding-method categories.
- pre_weld_conditions: initial material condition, groove/joint preparation, cleaning,
  pre-weld heat treatment, preheating, and specified layer/pass arrangement.
- welding_process: actual welding or thermal simulation, including each method,
  pass/layer, filler, shielding, electrical/beam/mechanical settings and interpass conditions.
- post_weld_treatment: explicitly performed treatment after welding, including PWHT,
  cooling, aging, straightening or surface treatment. Ordinary mechanical testing is not treatment.
A paragraph may contain any combination of stages; return all present keys once.
Do not require a complete procedure or a numerical value: explicit as-received conditions,
methods and statements such as "no PWHT" also count. Do not infer stages not reported.
Classify the operations actually performed or initial conditions explicitly described.
Planned pass counts belong to pre_weld_conditions; settings of actual passes and
interpass temperature control belong to welding_process. Cooling within a simulated
welding thermal cycle is welding_process, not a separate post-weld treatment.
An explicit absence of PWHT is post_weld_treatment information. Mechanical-test
preparation or test temperature alone is not a welding processing stage.
Continue the supplied answer prefix with only the stage list; do not repeat List: or Paragraph:, add explanations, or generate another example.
The examples below are illustrative, adapted from WeldMiner parameter examples;
never copy their values into extraction results. Return only the label list.

Begin!

Paragraph: Before welding, the plates were machined with a single-sided 30° V-groove. The planned joint consisted of six layers and nine passes. The plates were preheated to 105–110 °C at an ambient temperature of 20 °C.
List: ```JSON
["pre_weld_conditions"]
```

Paragraph: The root and hot passes were deposited with DCEP polarity at 80–100 A and 21–26 V. The filling and capping passes used 170–230 A and 20–27 V, with travel speeds of 15–20 and 12–16 cm/min, respectively. Interpass temperature was maintained at 105–132 °C.
List: ```JSON
["welding_process"]
```

Paragraph: After welding, the joint was heat treated using electric heating tape. The heating rate from 300 to 630 °C did not exceed 130 °C/h. The joint was held at 630 °C for 1 h, cooled to 300 °C at no more than 110 °C/h, and then allowed to cool freely to room temperature.
List: ```JSON
["post_weld_treatment"]
```

Paragraph: An X-groove with a 45° angle was prepared, and the plates were annealed at 560–575 °C before welding. Submerged arc welding was then carried out at 430–530 A and 28–30 V with a travel speed of 33 cm/min and a heat input of 35 kJ/cm.
List: ```JSON
["pre_weld_conditions", "welding_process"]
```

Paragraph: The groove was machined and cleaned to remove oil, rust and oxide scale within 20 mm of both edges. Flame preheating was applied. The root pass used DCEP at 150–160 A and 9–11 V; the filling pass used DCEN at 100–110 A and 20–24 V. After welding, the joint was held at 630 °C for 1 h and then cooled under controlled conditions.
List: ```JSON
["pre_weld_conditions", "welding_process", "post_weld_treatment"]
```

Paragraph: Laser-MAG hybrid welding was performed at a laser power of 3700 W and a MAG current of 150 A. The defocus distance was -1 mm, the laser-wire distance was 2 mm, and the welding speed was 1000 mm/min. ER80S-G wire of 1.2 mm diameter and 80% Ar + 20% CO2 shielding gas were used. No post-weld heat treatment was applied.
List: ```JSON
["welding_process", "post_weld_treatment"]
```

Paragraph: The Gleeble welding thermal simulation used a heating rate of 130 °C/s, a peak temperature of 1300 °C and a high-temperature residence time of 1 s. The simulated heat input was 20 kJ/cm and t8/5 was 7.57 s. In a separate double-cycle simulation, the first and second peak temperatures were 1350 and 1100 °C.
List: ```JSON
["welding_process"]
```

Paragraph: The plates used to manufacture the welded joints were supplied in the normalized condition. Their surfaces were degreased before assembly.
List: ```JSON
["pre_weld_conditions"]
```

Paragraph: The specimens were tested in the as-welded condition without any post-weld treatment.
List: ```JSON
["post_weld_treatment"]
```

Paragraph: The weld-metal tensile strength was 620 MPa and the HAZ hardness was 240 HV0.5. Charpy specimens were machined from the joint and tested at -40 °C, giving an absorbed energy of 85 J.
List: ```JSON
[]
```

Paragraph: Welding is widely used in engineering structures, and post-weld heat treatment can influence joint performance.
List: ```JSON
[]
```

Paragraph: {paragraph}
List: 
"""


PROMPT_STRUCT = """Use only explicitly reported welding experimental data, including base-material controls.
Return only one complete JSON-compatible list, starting with [ and ending with ].
Do not introduce the answer, explain it, or generate another example.
The literal markers Paragraph: and List: belong to the prompt, never to the output.
Do not copy these markers into source, condition, or any other JSON value.
When the supplied format includes source, its value MUST be a single JSON string,
never a list, dictionary, copied paragraph, explanation, or quotation of evidence.
Use only a section number, section heading, or table identifier explicitly present
in the supplied text. Do not invent a paragraph number or a generic source heading.
The source string must contain no colon, newline, prompt delimiter, or code fence.
If no suitable identifier is explicitly given, use "source": "".
Examples of source fields ONLY (not complete extraction records):
- Input explicitly identifies Table 3 -> "source": "Table 3"
- Input explicitly identifies section 2.1 -> "source": "2.1"
- Input heading is Experimental methods -> "source": "Experimental methods"
- Input contains only body text and the prompt's paragraph label -> "source": ""
Never copy these example identifiers unless they occur in the actual input.
Preserve names, numerical strings, units, ranges and parallel measurements. Never invent data.
Keep different specimens, welding conditions, passes, test temperatures and WM/HAZ/BM regions separate.
Native meta.name is the reported specimen/material identifier with explicit distinguishing conditions;
meta.symbol is a reported specimen label, or an empty string.
Do not use a bare alloy grade to equate different welding conditions. Unknown fields use empty strings.
Output only a JSON-compatible Python literal (strings/numbers/lists/dicts; no null/true/false or prose).
Extract welding stages {synthesis_type} following this guidance:
{format}
Return a list of native records with "meta" (name, symbol) and
"processes". Retain this outer envelope for the original L2M3 collector, but do not
impose a fixed JSON schema on the contents of processes.
Use a list of freely structured parameter dictionaries, as in WeldMiner's welding_params:
parameter names and reported units form keys, and original values form values.
Organize by actual pre-weld condition, welding action/pass or post-weld treatment only
when necessary. Flat parameters, multiple groups and nested substeps are all allowed.
The three classification keys select guidance; they are NOT mandatory output field names.
Do not require stage, steps, action, method, parameters, or name/value/unit containers.
Do not copy example labels or create empty fields. Only meta's missing identity fields
may use empty strings for compatibility; source also uses an empty string when no
explicit source identifier is available. Omit other unsupported process fields and stages.
Preserve differences between methods, passes and conditions, even when filler is identical.
Keep source order for sequential actions and attach shared parameters only to their stated scope.
Retain material identities and roles wherever explicitly linked to the procedure.
Do not treat tensile/impact test conditions as processing parameters.
Extract partial procedures without inventing missing stages or links to other paragraphs.
Each record describes one explicitly distinguishable specimen/condition. No synthesis yield field.
Before responding, silently check that every source value is a string containing only
an explicit source identifier or is empty, and that the complete JSON list is closed.
Paragraph: {paragraph}
JSON:
"""


FT_TYPE = """Identify which welding stages are explicitly present in the supplied text.
Allowed stage keys: {list_operation}. These are stages, NOT welding-method categories.
- pre_weld_conditions: initial material condition, groove/joint preparation, cleaning,
  pre-weld heat treatment, preheating, and specified layer/pass arrangement.
- welding_process: actual welding or thermal simulation, including each method,
  pass/layer, filler, shielding, electrical/beam/mechanical settings and interpass conditions.
- post_weld_treatment: explicitly performed treatment after welding, including PWHT,
  cooling, aging, straightening or surface treatment. Ordinary mechanical testing is not treatment.
A paragraph may contain any combination of stages; return all present keys once.
Do not require a complete procedure or a numerical value: explicit as-received conditions,
methods and statements such as "no PWHT" also count. Do not infer stages not reported.
Classify the operations actually performed or initial conditions explicitly described.
Planned pass counts belong to pre_weld_conditions; settings of actual passes and
interpass temperature control belong to welding_process. Cooling within a simulated
welding thermal cycle is welding_process, not a separate post-weld treatment.
An explicit absence of PWHT is post_weld_treatment information. Mechanical-test
preparation or test temperature alone is not a welding processing stage.
Continue the supplied answer prefix with only the stage list; do not repeat List: or Paragraph:, add explanations, or generate another example.
The examples below are illustrative, adapted from WeldMiner parameter examples;
never copy their values into extraction results. Return only the label list.

Begin!

Paragraph: Before welding, the plates were machined with a single-sided 30° V-groove. The planned joint consisted of six layers and nine passes. The plates were preheated to 105–110 °C at an ambient temperature of 20 °C.
List: ```JSON
["pre_weld_conditions"]
```

Paragraph: The root and hot passes were deposited with DCEP polarity at 80–100 A and 21–26 V. The filling and capping passes used 170–230 A and 20–27 V, with travel speeds of 15–20 and 12–16 cm/min, respectively. Interpass temperature was maintained at 105–132 °C.
List: ```JSON
["welding_process"]
```

Paragraph: After welding, the joint was heat treated using electric heating tape. The heating rate from 300 to 630 °C did not exceed 130 °C/h. The joint was held at 630 °C for 1 h, cooled to 300 °C at no more than 110 °C/h, and then allowed to cool freely to room temperature.
List: ```JSON
["post_weld_treatment"]
```

Paragraph: An X-groove with a 45° angle was prepared, and the plates were annealed at 560–575 °C before welding. Submerged arc welding was then carried out at 430–530 A and 28–30 V with a travel speed of 33 cm/min and a heat input of 35 kJ/cm.
List: ```JSON
["pre_weld_conditions", "welding_process"]
```

Paragraph: The groove was machined and cleaned to remove oil, rust and oxide scale within 20 mm of both edges. Flame preheating was applied. The root pass used DCEP at 150–160 A and 9–11 V; the filling pass used DCEN at 100–110 A and 20–24 V. After welding, the joint was held at 630 °C for 1 h and then cooled under controlled conditions.
List: ```JSON
["pre_weld_conditions", "welding_process", "post_weld_treatment"]
```

Paragraph: Laser-MAG hybrid welding was performed at a laser power of 3700 W and a MAG current of 150 A. The defocus distance was -1 mm, the laser-wire distance was 2 mm, and the welding speed was 1000 mm/min. ER80S-G wire of 1.2 mm diameter and 80% Ar + 20% CO2 shielding gas were used. No post-weld heat treatment was applied.
List: ```JSON
["welding_process", "post_weld_treatment"]
```

Paragraph: The Gleeble welding thermal simulation used a heating rate of 130 °C/s, a peak temperature of 1300 °C and a high-temperature residence time of 1 s. The simulated heat input was 20 kJ/cm and t8/5 was 7.57 s. In a separate double-cycle simulation, the first and second peak temperatures were 1350 and 1100 °C.
List: ```JSON
["welding_process"]
```

Paragraph: The plates used to manufacture the welded joints were supplied in the normalized condition. Their surfaces were degreased before assembly.
List: ```JSON
["pre_weld_conditions"]
```

Paragraph: The specimens were tested in the as-welded condition without any post-weld treatment.
List: ```JSON
["post_weld_treatment"]
```

Paragraph: The weld-metal tensile strength was 620 MPa and the HAZ hardness was 240 HV0.5. Charpy specimens were machined from the joint and tested at -40 °C, giving an absorbed energy of 85 J.
List: ```JSON
[]
```

Paragraph: Welding is widely used in engineering structures, and post-weld heat treatment can influence joint performance.
List: ```JSON
[]
```

Paragraph: {paragraph}
List: 
"""


FT_HUMAN = "{paragraph}"
