PROMPT_TYPE = """Select only explicitly present welding property keys from these definitions:
{explanation}

You must follow these rules:
- Select all applicable keys, but list each key only once even when several specimens or values occur.
- Require an explicitly reported value for a measurement; qualitative claims alone do not qualify.
- Distinguish tensile strength from yield strength and elongation from tensile crosshead/strain rate.
- A Charpy test temperature belongs to charpy_impact_test_temperature; preheat and PWHT temperatures do not.
- Use welding_process for explicitly described processing settings, not for numerical test results.
- Use etc only for other explicitly measured welding-related properties, not for arbitrary numbers.
- Return [] when none of the defined targets is present. Do not copy example values or labels unless supported.
- Answer with a JSON list in a ```JSON code block, without explanations or a literal List: prefix.

Begin!

Paragraph: The welded joint S1 exhibited an ultimate tensile strength of 620 MPa and a yield strength of 450 MPa. Another joint, S2, showed a tensile strength of 680 MPa and a yield strength of 510 MPa.
List: ```JSON
["tensile_strength", "yield_strength"]
```

Paragraph: Microhardness measurements gave 240 HV0.5 in the heat-affected zone and 215 HV0.5 in the weld metal, while the base metal showed 190 HV0.5.
List: ```JSON
["hardness"]
```

Paragraph: The transverse tensile specimen showed an ultimate tensile strength of 620 MPa and an elongation after fracture of 18%.
List: ```JSON
["tensile_strength", "elongation"]
```

Paragraph: Tensile tests were carried out at a crosshead speed of 1 mm/min. The yield strength of the joint was 450 MPa.
List: ```JSON
["stretching_rate", "yield_strength"]
```

Paragraph: Charpy V-notch impact tests were performed at -40 °C. The absorbed energy of the weld-metal specimen was 85 J, compared with 62 J for the heat-affected-zone specimen.
List: ```JSON
["charpy_impact_test_temperature", "impact_energy"]
```

Paragraph: Charpy specimens were tested at -20 °C and -40 °C; absorbed energy values were not reported in this paragraph.
List: ```JSON
["charpy_impact_test_temperature"]
```

Paragraph: The plates were preheated to 110 °C and welded by GMAW at 200 A and 24 V. Post-weld heat treatment was performed at 630 °C for 1 h.
List: ```JSON
["welding_process"]
```

Paragraph: The joint was welded at a heat input of 20 kJ/cm. Its weld-metal tensile strength was 620 MPa and its elongation was 18%.
List: ```JSON
["welding_process", "tensile_strength", "elongation"]
```

Paragraph: The crack tip opening displacement of the welded specimen was 0.25 mm under the reported test conditions.
List: ```JSON
["etc"]
```

Paragraph: The modified welding procedure improved joint strength and toughness. Tensile and hardness tests were conducted, but no measured values are provided here.
List: ```JSON
[]
```

Paragraph: {paragraph}
List:
"""


PROMPT_EXT = """Use only explicitly reported welding experimental data, including base-material controls.
Preserve names, numerical strings, units, ranges and parallel measurements. Never invent data.
Keep different specimens, welding conditions, passes, test temperatures and WM/HAZ/BM regions separate.
Native meta.name is the reported specimen/material identifier with explicit distinguishing conditions;
meta.symbol is a reported specimen label, or an empty string.
Do not use a bare alloy grade to equate different welding conditions. Unknown fields use empty strings.
Output only a JSON-compatible Python literal (strings/numbers/lists/dicts; no null/true/false or prose).
Use the original L2M3 layout: each property name maps to a list of measurement
objects with value, unit, type and condition as shown in the supplied formats.
Use the exact property keys in the format (for example "tensile strength", not tensile_strength_value).
Retain source values, units, ranges and inequalities without averaging or conversion.
Never copy the prompt markers Paragraph: or List: into output strings, including condition/source fields. Use a reported source identifier without the prompt prefix.
Use type for the reported measurement name/subtype. Put specimen-specific test method,
region, temperature, standard, dimensions and source location in condition when stated.
Keep parallel measurements as separate list entries and keep distinct specimens in separate records.
Do not emit WeldMiner-style *_name, *_value or *_unit fields. Unknown fields use empty strings.
Include native meta in every complete record. Examples are property-level unless meta is shown.
The ellipsis in a format means repeat entries as needed; never output literal ellipses.
Extract these selected properties: {prop}.
Native format entries:
{structured_data}
Field guidance:
{information}
Property-level examples (never copy example values). These demonstrate selected fields only;
add the source-specific meta object to each complete extracted record:
{example}
Return a list of dictionaries, each with "meta", selected property lists.
Paragraph: {paragraph}
"""

FT_TYPE = """Select only explicitly present welding property keys from these definitions:
{explanation}
Require reported values for measurements, and explicit settings for welding_process.
Example: "S1 yielded at 450 MPa and fractured at 620 MPa" -> ["yield_strength", "tensile_strength"].
Return only a list of keys; [] when absent, no markdown or prefix.
Paragraph: {paragraph}
"""

FT_HUMAN = "{paragraph}"
