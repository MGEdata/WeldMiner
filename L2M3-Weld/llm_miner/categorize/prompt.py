PROMPT_CATEGORIZE = """First, you must decide the type of the welding paragraph; it should be one or more of ["synthesis condition", "property", "else"].

You must follow the rules below:
- Output only the final JSON list. Do not include explanations, reasoning, a List: prefix, or code fences.
- The answer prefix is already supplied after the final paragraph. Continue it with the list itself: the first character you generate must be [ and the last must be ]. Stop after that list. Never repeat the answer prefix or generate another example. Decide the labels silently.
- Return ["synthesis condition"] only when the paragraph describes how the welded joints or specimens were made or processed: e.g. welding method (GMAW/GTAW/SAW/FCAW/laser/FSW...), base or filler material, joint geometry, welding parameters (current, voltage, wire feed speed, travel speed, heat input), preheat or interpass temperature, shielding gas, post-weld heat treatment, or Gleeble thermal simulation. Numerical values with units here are process settings, not measured properties. ex) "GMAW at 200 A and 24 V with ER70S-6 filler, followed by PWHT at 600 degC for 2 h."
- Return ["property"] only when the paragraph includes the property type, a specific numerical value of the property and its unit, together with context such as the test method, the tested region (BM/WM/HAZ) or the test temperature. ex) "the weld-metal tensile strength was 620 MPa", "the HAZ hardness was 240 HV0.5", "the absorbed energy was 85 J at -40 degC". Qualitative statements without a specific value are not property.
- If there are both "synthesis condition" and "property", return ["property", "synthesis condition"].
- When the paragraph does not include either synthesis condition or property, it means that there is no information. In this case, you must return ["else"].
- Only possible answer is ["property"], ["synthesis condition"], ["property", "synthesis condition"] or ["else"].
- A heat-treatment or preheat temperature (e.g. PWHT at 600 degC) is always a "synthesis condition", not a "property". A test temperature alone without a measured value (e.g. Charpy tests at -40 degC) is not a "property" paragraph.

Begin!

Paragraph: The welded joints were made in the flat position by GMAW using 1.2 mm ER70S-6 filler wire and 80%Ar-20%CO2 shielding gas at 200 A and 24 V with a travel speed of 30 cm/min; the interpass temperature was kept below 150 degC and the joints were post-weld heat treated at 600 degC for 2 h.
List: ["synthesis condition"]

Paragraph: Transverse tensile tests on the welded specimens gave an ultimate tensile strength of 620 MPa, a yield strength of 450 MPa and an elongation of 18%; all specimens fractured in the base metal.
List: ["property"]

Paragraph: Charpy V-notch impact tests were performed at -40 degC on specimens taken from the weld metal, and the absorbed energy of the WM specimens was 85 J.
List: ["property"]

Paragraph: The joints were welded with the parameters described above and then tested; the weld-metal tensile strength reached 620 MPa while the HAZ hardness was measured as 240 HV0.5.
List: ["property", "synthesis condition"]

Paragraph: Welding is one of the most widely used joining methods in steel structures, and its quality strongly affects the service safety of the component.
List: ["else"]

Paragraph: {paragraph}
List:
"""


FT_CATEGORIZE = (
    "Categorize the given welding paragraph. "
    "Return only the final JSON list, without explanations, prefixes or code fences. "
    "Select one or more categories from \"synthesis condition\" and \"property\". "
    "\"synthesis condition\" means welding, heat-treatment or thermal-simulation conditions or parameters. "
    "\"property\" means a reported experimental property with a specific numerical value and its unit. "
    "If the paragraph does not fit into either of these categories, choose \"else\". "
    "ex) \"GMAW at 200 A and 24 V\" -> [\"synthesis condition\"]; "
    "\"HAZ hardness was 240 HV0.5\" -> [\"property\"]"
)

FT_HUMAN = "{paragraph}"
