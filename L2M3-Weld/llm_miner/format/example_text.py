"""Original L2M3 Paragraph/JSON examples; doubled braces are unescaped at insertion."""

hardness = """
Paragraph: For specimen S1, HAZ hardness was 240 HV0.5.
JSON:```JSON
[{{"value":"240","unit":"HV0.5","type":"hardness","condition":"HAZ"}}]
```
"""

stretching_rate = """
Paragraph: For specimen S1, tensile crosshead speed was 1 mm/min.
JSON:```JSON
[{{"value":"1","unit":"mm/min","type":"tensile crosshead speed","condition":"tensile test"}}]
```
"""

tensile_strength = """
Paragraph: For specimen S1, weld-metal tensile strength was 620 MPa.
JSON:```JSON
[{{"value":"620","unit":"MPa","type":"tensile strength","condition":"tensile test; weld metal"}}]
```
"""

yield_strength = """
Paragraph: For specimen S1, weld-metal yield strength was 450 MPa.
JSON:```JSON
[{{"value":"450","unit":"MPa","type":"yield strength","condition":"tensile test; weld metal"}}]
```
"""

elongation = """
Paragraph: For specimen S1, elongation after fracture was 18%.
JSON:```JSON
[{{"value":"18","unit":"%","type":"elongation after fracture","condition":"tensile test"}}]
```
"""

charpy_impact_test_temperature = """
Paragraph: For specimen S1, Charpy testing was performed at -40 degC.
JSON:```JSON
[{{"value":"-40","unit":"degC","type":"Charpy test temperature","condition":"Charpy impact test"}}]
```
"""

impact_energy = """
Paragraph: For specimen S1, Charpy absorbed energy was 85 J at -40 degC.
JSON:```JSON
[{{"value":"85","unit":"J","type":"Charpy absorbed energy","condition":"Charpy impact test; test temperature -40 degC"}}]
```
"""

welding_process = """
Paragraph: For specimen S1, GMAW at 200 A with ER70S-6 filler.
JSON:```JSON
[{{"method":"GMAW","filler":"ER70S-6","parameters":"current 200 A"}}]
```
"""

etc = """
Paragraph: For specimen S1, CTOD was 0.25 mm.
JSON:```JSON
[{{"value":"0.25","unit":"mm","type":"CTOD","condition":""}}]
```
"""
