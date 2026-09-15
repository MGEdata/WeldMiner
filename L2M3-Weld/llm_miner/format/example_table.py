"""Fifteen source-table examples, deduplicated by extraction scenario.
See cross_evaluation/table_examples_sources/examples_manifest.json for provenance.
"""

paper_corsci_2025_113442_table_5 = {
    "contain": ['tensile strength', 'elongation', 'etc'],
    "content": """Input: DOI: 10.1016/j.corsci.2025.113442
Table 5. Mechanical properties and I RA of notched tensile specimens for X52 steel weldments produced by GMAW, CMT, and FCAW in N2 and 1 MPa H2 + 3 MPa N2 environments.
| Specimen | Environment | EL (mm) | NTS (MPa) | RA (%) | I RA |
| --- | --- | --- | --- | --- | --- |
| GMAW-WM | 4 MPa N2 | 1.19 | 1170 | 21.47 | 26.27 % |
| GMAW-WM | 1 MPa H2 | 1.18 | 1212 | 15.83 | 26.27 % |
| CMT-WM | 4 MPa N2 | 2.07 | 1423 | 21.27 | 22.66 % |
| CMT-WM | 1 MPa H2 | 1.85 | 1444 | 16.45 | 22.66 % |
| FCAW -WM | 4 MPa N2 | 1.11 | 1031 | 26.72 | 36.93 % |
| FCAW -WM | 1 MPa H2 | 0.99 | 1015 | 16.85 | 36.93 % |
Notes: Table 5
Requested properties: ["tensile_strength", "elongation", "etc"]
Output: ```JSON
[
  {
    "meta": {
      "name": "GMAW-WM; 4 MPa N2",
      "symbol": ""
    },
    "tensile strength": [
      {
        "value": "1170",
        "unit": "MPa",
        "type": "NTS (notched tensile strength)",
        "condition": "Table 5; notched specimen; 4 MPa N2"
      }
    ],
    "elongation": [
      {
        "value": "1.19",
        "unit": "mm",
        "type": "EL",
        "condition": "Table 5; notched specimen; 4 MPa N2"
      }
    ],
    "etc": [
      {
        "value": "21.47",
        "unit": "%",
        "type": "RA (reduction in area)",
        "condition": "Table 5; notched specimen; 4 MPa N2"
      }
    ]
  },
  {
    "meta": {
      "name": "GMAW-WM; 1 MPa H2",
      "symbol": ""
    },
    "tensile strength": [
      {
        "value": "1212",
        "unit": "MPa",
        "type": "NTS (notched tensile strength)",
        "condition": "Table 5; notched specimen; 1 MPa H2; caption specifies 1 MPa H2 + 3 MPa N2"
      }
    ],
    "elongation": [
      {
        "value": "1.18",
        "unit": "mm",
        "type": "EL",
        "condition": "Table 5; notched specimen; 1 MPa H2; caption specifies 1 MPa H2 + 3 MPa N2"
      }
    ],
    "etc": [
      {
        "value": "15.83",
        "unit": "%",
        "type": "RA (reduction in area)",
        "condition": "Table 5; notched specimen; 1 MPa H2; caption specifies 1 MPa H2 + 3 MPa N2"
      },
      {
        "value": "26.27",
        "unit": "%",
        "type": "I RA",
        "condition": "Table 5; GMAW-WM; comparison between N2 and H2 + N2 environments"
      }
    ]
  },
  {
    "meta": {
      "name": "CMT-WM; 4 MPa N2",
      "symbol": ""
    },
    "tensile strength": [
      {
        "value": "1423",
        "unit": "MPa",
        "type": "NTS (notched tensile strength)",
        "condition": "Table 5; notched specimen; 4 MPa N2"
      }
    ],
    "elongation": [
      {
        "value": "2.07",
        "unit": "mm",
        "type": "EL",
        "condition": "Table 5; notched specimen; 4 MPa N2"
      }
    ],
    "etc": [
      {
        "value": "21.27",
        "unit": "%",
        "type": "RA (reduction in area)",
        "condition": "Table 5; notched specimen; 4 MPa N2"
      }
    ]
  },
  {
    "meta": {
      "name": "CMT-WM; 1 MPa H2",
      "symbol": ""
    },
    "tensile strength": [
      {
        "value": "1444",
        "unit": "MPa",
        "type": "NTS (notched tensile strength)",
        "condition": "Table 5; notched specimen; 1 MPa H2; caption specifies 1 MPa H2 + 3 MPa N2"
      }
    ],
    "elongation": [
      {
        "value": "1.85",
        "unit": "mm",
        "type": "EL",
        "condition": "Table 5; notched specimen; 1 MPa H2; caption specifies 1 MPa H2 + 3 MPa N2"
      }
    ],
    "etc": [
      {
        "value": "16.45",
        "unit": "%",
        "type": "RA (reduction in area)",
        "condition": "Table 5; notched specimen; 1 MPa H2; caption specifies 1 MPa H2 + 3 MPa N2"
      },
      {
        "value": "22.66",
        "unit": "%",
        "type": "I RA",
        "condition": "Table 5; CMT-WM; comparison between N2 and H2 + N2 environments"
      }
    ]
  },
  {
    "meta": {
      "name": "FCAW -WM; 4 MPa N2",
      "symbol": ""
    },
    "tensile strength": [
      {
        "value": "1031",
        "unit": "MPa",
        "type": "NTS (notched tensile strength)",
        "condition": "Table 5; notched specimen; 4 MPa N2"
      }
    ],
    "elongation": [
      {
        "value": "1.11",
        "unit": "mm",
        "type": "EL",
        "condition": "Table 5; notched specimen; 4 MPa N2"
      }
    ],
    "etc": [
      {
        "value": "26.72",
        "unit": "%",
        "type": "RA (reduction in area)",
        "condition": "Table 5; notched specimen; 4 MPa N2"
      }
    ]
  },
  {
    "meta": {
      "name": "FCAW -WM; 1 MPa H2",
      "symbol": ""
    },
    "tensile strength": [
      {
        "value": "1015",
        "unit": "MPa",
        "type": "NTS (notched tensile strength)",
        "condition": "Table 5; notched specimen; 1 MPa H2; caption specifies 1 MPa H2 + 3 MPa N2"
      }
    ],
    "elongation": [
      {
        "value": "0.99",
        "unit": "mm",
        "type": "EL",
        "condition": "Table 5; notched specimen; 1 MPa H2; caption specifies 1 MPa H2 + 3 MPa N2"
      }
    ],
    "etc": [
      {
        "value": "16.85",
        "unit": "%",
        "type": "RA (reduction in area)",
        "condition": "Table 5; notched specimen; 1 MPa H2; caption specifies 1 MPa H2 + 3 MPa N2"
      },
      {
        "value": "36.93",
        "unit": "%",
        "type": "I RA",
        "condition": "Table 5; FCAW -WM; comparison between N2 and H2 + N2 environments"
      }
    ]
  }
]
```
""",
}

paper_ijpvp_2012_05_011_table_4 = {
    "contain": ['yield strength', 'tensile strength', 'elongation', 'etc'],
    "content": """Input: DOI: 10.1016/j.ijpvp.2012.05.011
Table 4. Measured mechanical properties of X65 pipeline in transverse direction and target values specified by API 5L.
| API grade | Dimensions / Outside diameter (D: mm) | Dimensions / Wall thickness (t: mm) | Dimensions / D/t | Tensile properties / YS (MPa) | Tensile properties / TS (MPa) | Tensile properties / Y/T | Tensile properties / Elongation in (2 in.) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| X65 | 1219 | 14.3 | 85 | 490 | 552 | 0.89 | 21 |
| Minimum | Minimum | Minimum | Minimum | 448 | 531 | – | – |
| Maximum | Maximum | Maximum | Maximum | 600 | 758 | 0.93 | – |
Notes: YS: yield strength, TS: tensile strength.
Requested properties: ["yield_strength", "tensile_strength", "elongation", "etc"]
Output: ```JSON
[
  {
    "meta": {
      "name": "X65; transverse; D=1219 mm; t=14.3 mm",
      "symbol": ""
    },
    "yield strength": [
      {
        "value": "490",
        "unit": "MPa",
        "type": "YS",
        "condition": "Table 4; measured X65 row; transverse; D=1219 mm; t=14.3 mm; D/t=85"
      }
    ],
    "tensile strength": [
      {
        "value": "552",
        "unit": "MPa",
        "type": "TS",
        "condition": "Table 4; measured X65 row; transverse; D=1219 mm; t=14.3 mm; D/t=85"
      }
    ],
    "elongation": [
      {
        "value": "21",
        "unit": "",
        "type": "Elongation in (2 in.)",
        "condition": "Table 4; measured X65 row; transverse; D=1219 mm; t=14.3 mm; D/t=85"
      }
    ],
    "etc": [
      {
        "value": "0.89",
        "unit": "",
        "type": "Y/T",
        "condition": "Table 4; measured X65 row; transverse; D=1219 mm; t=14.3 mm; D/t=85"
      }
    ]
  }
]
```
""",
}

paper_ijpvp_2012_05_011_table_6 = {
    "contain": ['hardness'],
    "content": """Input: DOI: 10.1016/j.ijpvp.2012.05.011
Table 6. Measured hardness data for X65 pipeline base material, fusion zone, and heat affected zone (HV10).
| Location | Base metal | Heat affected zone | Fusion zone |
| --- | --- | --- | --- |
| Max. hardness | 212 | 212 | 222 |
| Min. hardness | 210 | 206 | 207 |
| Ave. hardness | 211 | 208 | 218 |
Requested properties: ["hardness"]
Output: ```JSON
[
  {
    "meta": {
      "name": "X65 Base metal",
      "symbol": ""
    },
    "hardness": [
      {
        "value": "212",
        "unit": "HV10",
        "type": "Max. hardness",
        "condition": "Table 6; Base metal"
      },
      {
        "value": "210",
        "unit": "HV10",
        "type": "Min. hardness",
        "condition": "Table 6; Base metal"
      },
      {
        "value": "211",
        "unit": "HV10",
        "type": "Ave. hardness",
        "condition": "Table 6; Base metal"
      }
    ]
  },
  {
    "meta": {
      "name": "X65 Heat affected zone",
      "symbol": ""
    },
    "hardness": [
      {
        "value": "212",
        "unit": "HV10",
        "type": "Max. hardness",
        "condition": "Table 6; Heat affected zone"
      },
      {
        "value": "206",
        "unit": "HV10",
        "type": "Min. hardness",
        "condition": "Table 6; Heat affected zone"
      },
      {
        "value": "208",
        "unit": "HV10",
        "type": "Ave. hardness",
        "condition": "Table 6; Heat affected zone"
      }
    ]
  },
  {
    "meta": {
      "name": "X65 Fusion zone",
      "symbol": ""
    },
    "hardness": [
      {
        "value": "222",
        "unit": "HV10",
        "type": "Max. hardness",
        "condition": "Table 6; Fusion zone"
      },
      {
        "value": "207",
        "unit": "HV10",
        "type": "Min. hardness",
        "condition": "Table 6; Fusion zone"
      },
      {
        "value": "218",
        "unit": "HV10",
        "type": "Ave. hardness",
        "condition": "Table 6; Fusion zone"
      }
    ]
  }
]
```
""",
}

paper_ijpvp_2016_10_004_table_7 = {
    "contain": ['impact energy', 'charpy impact test temperature'],
    "content": """Input: DOI: 10.1016/j.ijpvp.2016.10.004
Table 7. Charpy impact toughness.
[Excerpt: body rows 1, 13, 16; all columns retained.]
| Temp (°C) | Sampling direction | Number | Sample size | AKV (J) |
| --- | --- | --- | --- | --- |
| 25 | Transverse direction of new pipe | 1-1-T | 10 × 10 × 55 | >179 |
| 25 | Weld | 1-3-R | 10 × 10 × 55 | 14 |
| 650 | Weld | 1-3-O | 10 × 10 × 55 | 72 |
Notes: Table 7
Requested properties: ["impact_energy", "charpy_impact_test_temperature"]
Output: ```JSON
[
  {
    "meta": {
      "name": "Transverse direction of new pipe; 1-1-T; 25 °C",
      "symbol": "1-1-T"
    },
    "impact energy": [
      {
        "value": ">179",
        "unit": "J",
        "type": "AKV",
        "condition": "Table 7; Transverse direction of new pipe; sample size 10 × 10 × 55 (unit not supplied in table); 25 °C"
      }
    ],
    "charpy impact test temperature": [
      {
        "value": "25",
        "unit": "°C",
        "type": "Charpy test temperature",
        "condition": "Table 7; Transverse direction of new pipe; sample size 10 × 10 × 55 (unit not supplied in table); 25 °C"
      }
    ]
  },
  {
    "meta": {
      "name": "Weld; 1-3-R; 25 °C",
      "symbol": "1-3-R"
    },
    "impact energy": [
      {
        "value": "14",
        "unit": "J",
        "type": "AKV",
        "condition": "Table 7; Weld; sample size 10 × 10 × 55 (unit not supplied in table); 25 °C"
      }
    ],
    "charpy impact test temperature": [
      {
        "value": "25",
        "unit": "°C",
        "type": "Charpy test temperature",
        "condition": "Table 7; Weld; sample size 10 × 10 × 55 (unit not supplied in table); 25 °C"
      }
    ]
  },
  {
    "meta": {
      "name": "Weld; 1-3-O; 650 °C",
      "symbol": "1-3-O"
    },
    "impact energy": [
      {
        "value": "72",
        "unit": "J",
        "type": "AKV",
        "condition": "Table 7; Weld; sample size 10 × 10 × 55 (unit not supplied in table); 650 °C"
      }
    ],
    "charpy impact test temperature": [
      {
        "value": "650",
        "unit": "°C",
        "type": "Charpy test temperature",
        "condition": "Table 7; Weld; sample size 10 × 10 × 55 (unit not supplied in table); 650 °C"
      }
    ]
  }
]
```
""",
}

paper_ijpvp_2017_04_003_table_3 = {
    "contain": ['yield strength', 'tensile strength', 'elongation', 'hardness', 'impact energy', 'charpy impact test temperature'],
    "content": """Input: DOI: 10.1016/j.ijpvp.2017.04.003
Table 3. Examined mechanical properties of the utilized API X60 steel.
| Mechanical property | Value |
| --- | --- |
| Yield strength (MPa) | 430 |
| Ultimate tensile strength (MPa) | 535 |
| Elongation in 2″ gauge (%) | 36 |
| Hardness (Hv) | 172 |
| Impact energy at 0 °C (J) | 96 |
Notes: Table 3
Requested properties: ["yield_strength", "tensile_strength", "elongation", "hardness", "impact_energy", "charpy_impact_test_temperature"]
Output: ```JSON
[
  {
    "meta": {
      "name": "API X60",
      "symbol": ""
    },
    "yield strength": [
      {
        "value": "430",
        "unit": "MPa",
        "type": "Yield strength (MPa)",
        "condition": "Table 3; "
      }
    ],
    "tensile strength": [
      {
        "value": "535",
        "unit": "MPa",
        "type": "Ultimate tensile strength (MPa)",
        "condition": "Table 3; "
      }
    ],
    "elongation": [
      {
        "value": "36",
        "unit": "%",
        "type": "Elongation in 2″ gauge (%)",
        "condition": "Table 3; 2″ gauge"
      }
    ],
    "hardness": [
      {
        "value": "172",
        "unit": "Hv",
        "type": "Hardness (Hv)",
        "condition": "Table 3; "
      }
    ],
    "impact energy": [
      {
        "value": "96",
        "unit": "J",
        "type": "Impact energy at 0 °C (J)",
        "condition": "Table 3; 0 °C"
      }
    ],
    "charpy impact test temperature": [
      {
        "value": "0",
        "unit": "°C",
        "type": "Impact test temperature",
        "condition": "Table 3; Impact energy at 0 °C"
      }
    ]
  }
]
```
""",
}

paper_ijpvp_2017_04_003_table_4 = {
    "contain": ['welding process'],
    "content": """Input: DOI: 10.1016/j.ijpvp.2017.04.003
Table 4. Details of the applied PWHT cycles along with specimen types in the experiments.
| Series | Sample type | Sample type | Austenitizing temperature, time (°C, s) | Quenching media | Tempering temperature, time (°C, min) |
| --- | --- | --- | --- | --- | --- |
| 1 | A | Commercial | 950 °C, 12 s | Air to 350 °C and then water quench to room temperature | – |
| 2 | B | As-welded | – | Water | – |
| 3 | C | Water quenched | 950 °C, 12 s | Water | – |
| 4 | D | Normalized | 950 °C, 12 s | Air cooling to room temperature | – |
| 5 | E | 500–20 | 950 °C, 12 s | Water | 500 °C, 20 min |
| 6 | F | 500–30 | 950 °C, 12 s | Water | 500 °C, 30 min |
| 7 | G | 600–20 | 950 °C, 12 s | Water | 600 °C, 20 min |
| 8 | H | 600–30 | 950 °C, 12 s | Water | 600 °C, 30 min |
Notes: Table 4
Requested properties: ["welding_process"]
Output: ```JSON
[
  {
    "meta": {
      "name": "A; Commercial",
      "symbol": "A"
    },
    "welding process": [
      {
        "method": "",
        "filler": "",
        "parameters": "conditions=Table 4; PWHT cycles; Series 1; Commercial; Austenitizing temperature, time (°C, s)=950 °C, 12 s; Quenching media=Air to 350 °C and then water quench to room temperature"
      }
    ]
  },
  {
    "meta": {
      "name": "B; As-welded",
      "symbol": "B"
    },
    "welding process": [
      {
        "method": "",
        "filler": "",
        "parameters": "conditions=Table 4; PWHT cycles; Series 2; As-welded; Quenching media=Water"
      }
    ]
  },
  {
    "meta": {
      "name": "C; Water quenched",
      "symbol": "C"
    },
    "welding process": [
      {
        "method": "",
        "filler": "",
        "parameters": "conditions=Table 4; PWHT cycles; Series 3; Water quenched; Austenitizing temperature, time (°C, s)=950 °C, 12 s; Quenching media=Water"
      }
    ]
  },
  {
    "meta": {
      "name": "D; Normalized",
      "symbol": "D"
    },
    "welding process": [
      {
        "method": "",
        "filler": "",
        "parameters": "conditions=Table 4; PWHT cycles; Series 4; Normalized; Austenitizing temperature, time (°C, s)=950 °C, 12 s; Quenching media=Air cooling to room temperature"
      }
    ]
  },
  {
    "meta": {
      "name": "E; 500–20",
      "symbol": "E"
    },
    "welding process": [
      {
        "method": "",
        "filler": "",
        "parameters": "conditions=Table 4; PWHT cycles; Series 5; 500–20; Austenitizing temperature, time (°C, s)=950 °C, 12 s; Quenching media=Water; Tempering temperature, time (°C, min)=500 °C, 20 min"
      }
    ]
  },
  {
    "meta": {
      "name": "F; 500–30",
      "symbol": "F"
    },
    "welding process": [
      {
        "method": "",
        "filler": "",
        "parameters": "conditions=Table 4; PWHT cycles; Series 6; 500–30; Austenitizing temperature, time (°C, s)=950 °C, 12 s; Quenching media=Water; Tempering temperature, time (°C, min)=500 °C, 30 min"
      }
    ]
  },
  {
    "meta": {
      "name": "G; 600–20",
      "symbol": "G"
    },
    "welding process": [
      {
        "method": "",
        "filler": "",
        "parameters": "conditions=Table 4; PWHT cycles; Series 7; 600–20; Austenitizing temperature, time (°C, s)=950 °C, 12 s; Quenching media=Water; Tempering temperature, time (°C, min)=600 °C, 20 min"
      }
    ]
  },
  {
    "meta": {
      "name": "H; 600–30",
      "symbol": "H"
    },
    "welding process": [
      {
        "method": "",
        "filler": "",
        "parameters": "conditions=Table 4; PWHT cycles; Series 8; 600–30; Austenitizing temperature, time (°C, s)=950 °C, 12 s; Quenching media=Water; Tempering temperature, time (°C, min)=600 °C, 30 min"
      }
    ]
  }
]
```
""",
}

paper_jmapro_2020_01_014_table_4 = {
    "contain": ['hardness'],
    "content": """Input: DOI: 10.1016/j.jmapro.2020.01.014
Table 4. Hardness of welded joints.
| Hardness | BM | WM | CGHAZ | FGHAZ | ICHAZ | SCHAZ |
| --- | --- | --- | --- | --- | --- | --- |
| (HV) | 220-194 | 209-201 | 278-251 | 257-246 | 207-189 | 191-181 |
Notes: Table 4
Requested properties: ["hardness"]
Output: ```JSON
[
  {
    "meta": {
      "name": "BM",
      "symbol": ""
    },
    "hardness": [
      {
        "value": "220-194",
        "unit": "HV",
        "type": "Hardness",
        "condition": "Table 4; BM; source range order retained"
      }
    ]
  },
  {
    "meta": {
      "name": "WM",
      "symbol": ""
    },
    "hardness": [
      {
        "value": "209-201",
        "unit": "HV",
        "type": "Hardness",
        "condition": "Table 4; WM; source range order retained"
      }
    ]
  },
  {
    "meta": {
      "name": "CGHAZ",
      "symbol": ""
    },
    "hardness": [
      {
        "value": "278-251",
        "unit": "HV",
        "type": "Hardness",
        "condition": "Table 4; CGHAZ; source range order retained"
      }
    ]
  },
  {
    "meta": {
      "name": "FGHAZ",
      "symbol": ""
    },
    "hardness": [
      {
        "value": "257-246",
        "unit": "HV",
        "type": "Hardness",
        "condition": "Table 4; FGHAZ; source range order retained"
      }
    ]
  },
  {
    "meta": {
      "name": "ICHAZ",
      "symbol": ""
    },
    "hardness": [
      {
        "value": "207-189",
        "unit": "HV",
        "type": "Hardness",
        "condition": "Table 4; ICHAZ; source range order retained"
      }
    ]
  },
  {
    "meta": {
      "name": "SCHAZ",
      "symbol": ""
    },
    "hardness": [
      {
        "value": "191-181",
        "unit": "HV",
        "type": "Hardness",
        "condition": "Table 4; SCHAZ; source range order retained"
      }
    ]
  }
]
```
""",
}

paper_jmapro_2021_11_021_table_3 = {
    "contain": ['welding process'],
    "content": """Input: DOI: 10.1016/j.jmapro.2021.11.021
Table 3. Welding parameters for PA and PF welds.
| Welding position | Pass number | Welding current (A) | Welding voltage (V) | Wire speed (m/min) | Welding speed (mm/s) | Nominal heat input (kJ/mm) |
| --- | --- | --- | --- | --- | --- | --- |
| PA | 1 | 179.5 | 17.1 | 4.7 | 5 | 0.61 |
| PA | 2 | 310 | 28.9 | 8.3 | 5 | 1.79 |
| PA | 3 | 314 | 29 | 8.3 | 5 | 1.82 |
| PA | 4 | 298.5 | 29.1 | 8.3 | 4 | 2.17 |
| PA | 5 | 280 | 26 | 8 | 5 | 1.46 |
| PF | 1 | 153 | 16.7 | 3.7 | 1.3 | 1.97 |
| PF | 2 | 152.5 | 16.3 | 3.7 | 1.3 | 1.91 |
| PF | 3 | 155.5 | 16.3 | 3.7 | 1.2 | 2.11 |
| PF | 4 | 156 | 16.5 | 3.7 | 1.2 | 2.15 |
Notes: Table 3
Requested properties: ["welding_process"]
Output: ```JSON
[
  {
    "meta": {
      "name": "Position PA",
      "symbol": ""
    },
    "welding process": [
      {
        "method": "",
        "filler": "",
        "parameters": "pass=1; conditions=Table 3; Position PA; Welding current (A)=179.5; Welding voltage (V)=17.1; Wire speed (m/min)=4.7; Welding speed (mm/s)=5; Nominal heat input (kJ/mm)=0.61"
      },
      {
        "method": "",
        "filler": "",
        "parameters": "pass=2; conditions=Table 3; Position PA; Welding current (A)=310; Welding voltage (V)=28.9; Wire speed (m/min)=8.3; Welding speed (mm/s)=5; Nominal heat input (kJ/mm)=1.79"
      },
      {
        "method": "",
        "filler": "",
        "parameters": "pass=3; conditions=Table 3; Position PA; Welding current (A)=314; Welding voltage (V)=29; Wire speed (m/min)=8.3; Welding speed (mm/s)=5; Nominal heat input (kJ/mm)=1.82"
      },
      {
        "method": "",
        "filler": "",
        "parameters": "pass=4; conditions=Table 3; Position PA; Welding current (A)=298.5; Welding voltage (V)=29.1; Wire speed (m/min)=8.3; Welding speed (mm/s)=4; Nominal heat input (kJ/mm)=2.17"
      },
      {
        "method": "",
        "filler": "",
        "parameters": "pass=5; conditions=Table 3; Position PA; Welding current (A)=280; Welding voltage (V)=26; Wire speed (m/min)=8; Welding speed (mm/s)=5; Nominal heat input (kJ/mm)=1.46"
      }
    ]
  },
  {
    "meta": {
      "name": "Position PF",
      "symbol": ""
    },
    "welding process": [
      {
        "method": "",
        "filler": "",
        "parameters": "pass=1; conditions=Table 3; Position PF; Welding current (A)=153; Welding voltage (V)=16.7; Wire speed (m/min)=3.7; Welding speed (mm/s)=1.3; Nominal heat input (kJ/mm)=1.97"
      },
      {
        "method": "",
        "filler": "",
        "parameters": "pass=2; conditions=Table 3; Position PF; Welding current (A)=152.5; Welding voltage (V)=16.3; Wire speed (m/min)=3.7; Welding speed (mm/s)=1.3; Nominal heat input (kJ/mm)=1.91"
      },
      {
        "method": "",
        "filler": "",
        "parameters": "pass=3; conditions=Table 3; Position PF; Welding current (A)=155.5; Welding voltage (V)=16.3; Wire speed (m/min)=3.7; Welding speed (mm/s)=1.2; Nominal heat input (kJ/mm)=2.11"
      },
      {
        "method": "",
        "filler": "",
        "parameters": "pass=4; conditions=Table 3; Position PF; Welding current (A)=156; Welding voltage (V)=16.5; Wire speed (m/min)=3.7; Welding speed (mm/s)=1.2; Nominal heat input (kJ/mm)=2.15"
      }
    ]
  }
]
```
""",
}

paper_jmatprotec_2022_117621_table_4 = {
    "contain": ['yield strength', 'tensile strength', 'elongation', 'etc'],
    "content": """Input: DOI: 10.1016/j.jmatprotec.2022.117621
Table 4. Tensile data of the as-welded and as-annealed joints.
| Sample | Yield strength/MPa | Ultimate tensile strength/MPa | Elongation/% | Joint efficiency/% |
| --- | --- | --- | --- | --- |
| BM | 632.3 ± 5 | 755.7 ± 7 | 38 ± 1.5 | – |
| As-annealed BM | 616.3 ± 3 | 793.5 ± 5 | 37.8 ± 1.4 | – |
| As-welded joint | 706.6 ± 7 | 758.5 ± 4 | 22.5 ± 1.3 | 100.4 |
| As-annealed joint | 616.5 ± 2.5 | 782.5 ± 4.7 | 32.5 ± 1.7 | 103.5 |
Notes: Table 4
Requested properties: ["yield_strength", "tensile_strength", "elongation", "etc"]
Output: ```JSON
[
  {
    "meta": {
      "name": "BM",
      "symbol": ""
    },
    "yield strength": [
      {
        "value": "632.3 ± 5",
        "unit": "MPa",
        "type": "Yield strength/MPa",
        "condition": "Table 4; BM"
      }
    ],
    "tensile strength": [
      {
        "value": "755.7 ± 7",
        "unit": "MPa",
        "type": "Ultimate tensile strength/MPa",
        "condition": "Table 4; BM"
      }
    ],
    "elongation": [
      {
        "value": "38 ± 1.5",
        "unit": "%",
        "type": "Elongation/%",
        "condition": "Table 4; BM"
      }
    ]
  },
  {
    "meta": {
      "name": "As-annealed BM",
      "symbol": ""
    },
    "yield strength": [
      {
        "value": "616.3 ± 3",
        "unit": "MPa",
        "type": "Yield strength/MPa",
        "condition": "Table 4; As-annealed BM"
      }
    ],
    "tensile strength": [
      {
        "value": "793.5 ± 5",
        "unit": "MPa",
        "type": "Ultimate tensile strength/MPa",
        "condition": "Table 4; As-annealed BM"
      }
    ],
    "elongation": [
      {
        "value": "37.8 ± 1.4",
        "unit": "%",
        "type": "Elongation/%",
        "condition": "Table 4; As-annealed BM"
      }
    ]
  },
  {
    "meta": {
      "name": "As-welded joint",
      "symbol": ""
    },
    "yield strength": [
      {
        "value": "706.6 ± 7",
        "unit": "MPa",
        "type": "Yield strength/MPa",
        "condition": "Table 4; As-welded joint"
      }
    ],
    "tensile strength": [
      {
        "value": "758.5 ± 4",
        "unit": "MPa",
        "type": "Ultimate tensile strength/MPa",
        "condition": "Table 4; As-welded joint"
      }
    ],
    "elongation": [
      {
        "value": "22.5 ± 1.3",
        "unit": "%",
        "type": "Elongation/%",
        "condition": "Table 4; As-welded joint"
      }
    ],
    "etc": [
      {
        "value": "100.4",
        "unit": "%",
        "type": "Joint efficiency/%",
        "condition": "Table 4; As-welded joint"
      }
    ]
  },
  {
    "meta": {
      "name": "As-annealed joint",
      "symbol": ""
    },
    "yield strength": [
      {
        "value": "616.5 ± 2.5",
        "unit": "MPa",
        "type": "Yield strength/MPa",
        "condition": "Table 4; As-annealed joint"
      }
    ],
    "tensile strength": [
      {
        "value": "782.5 ± 4.7",
        "unit": "MPa",
        "type": "Ultimate tensile strength/MPa",
        "condition": "Table 4; As-annealed joint"
      }
    ],
    "elongation": [
      {
        "value": "32.5 ± 1.7",
        "unit": "%",
        "type": "Elongation/%",
        "condition": "Table 4; As-annealed joint"
      }
    ],
    "etc": [
      {
        "value": "103.5",
        "unit": "%",
        "type": "Joint efficiency/%",
        "condition": "Table 4; As-annealed joint"
      }
    ]
  }
]
```
""",
}

paper_jmatprotec_2022_117621_table_3 = {
    "contain": ['impact energy', 'charpy impact test temperature'],
    "content": """Input: DOI: 10.1016/j.jmatprotec.2022.117621
Table 3. Impact energy of the as-welded joint.
| V-shaped Notch locations | BM | HAZ | NZ |
| --- | --- | --- | --- |
| Impact energy at − 40 °C /J/cm<sup>2</sup> | 190 | 121.6 | 73.6 |
Notes: Table 3
Requested properties: ["impact_energy", "charpy_impact_test_temperature"]
Output: ```JSON
[
  {
    "meta": {
      "name": "As-welded joint; BM",
      "symbol": ""
    },
    "impact energy": [
      {
        "value": "190",
        "unit": "J/cm2",
        "type": "Impact energy per area",
        "condition": "Table 3; V-shaped notch at BM; −40 °C"
      }
    ],
    "charpy impact test temperature": [
      {
        "value": "−40",
        "unit": "°C",
        "type": "V-notch impact test temperature",
        "condition": "Table 3; V-shaped notch at BM; −40 °C"
      }
    ]
  },
  {
    "meta": {
      "name": "As-welded joint; HAZ",
      "symbol": ""
    },
    "impact energy": [
      {
        "value": "121.6",
        "unit": "J/cm2",
        "type": "Impact energy per area",
        "condition": "Table 3; V-shaped notch at HAZ; −40 °C"
      }
    ],
    "charpy impact test temperature": [
      {
        "value": "−40",
        "unit": "°C",
        "type": "V-notch impact test temperature",
        "condition": "Table 3; V-shaped notch at HAZ; −40 °C"
      }
    ]
  },
  {
    "meta": {
      "name": "As-welded joint; NZ",
      "symbol": ""
    },
    "impact energy": [
      {
        "value": "73.6",
        "unit": "J/cm2",
        "type": "Impact energy per area",
        "condition": "Table 3; V-shaped notch at NZ; −40 °C"
      }
    ],
    "charpy impact test temperature": [
      {
        "value": "−40",
        "unit": "°C",
        "type": "V-notch impact test temperature",
        "condition": "Table 3; V-shaped notch at NZ; −40 °C"
      }
    ]
  }
]
```
""",
}

paper_jmrt_2022_05_141_table_5 = {
    "contain": ['etc'],
    "content": """Input: DOI: 10.1016/j.jmrt.2022.05.141
Table 5. Fracture toughness (crack tip opening displacement, CTOD) of the CGHAZ at various investigated interpass temperatures (ITs). Where CTODm is at maximum load and CTODu before maximum load or first pop-in.
| CTOD [mm] | Interpass temperature [°C] / 300 | Interpass temperature [°C] / 360 | Interpass temperature [°C] / 400 |
| --- | --- | --- | --- |
| CTODm | 2.13 | 2.08 | 2.30 |
| CTODm | 2.25 | 1.91 | 1.47 |
| CTODm | 2.01 | – | – |
| CTODu | – | 1.72 | 1.14 |
| CTODu | – | – | 1.97 |
| CTODu | – | – | 1.17 |
Notes: Table 5
Requested properties: ["etc"]
Output: ```JSON
[
  {
    "meta": {
      "name": "CGHAZ; interpass temperature 300 °C",
      "symbol": ""
    },
    "etc": [
      {
        "value": "2.13",
        "unit": "mm",
        "type": "CTODm",
        "condition": "Table 5; CGHAZ; interpass temperature 300 °C; source body row 1"
      },
      {
        "value": "2.25",
        "unit": "mm",
        "type": "CTODm",
        "condition": "Table 5; CGHAZ; interpass temperature 300 °C; source body row 2"
      },
      {
        "value": "2.01",
        "unit": "mm",
        "type": "CTODm",
        "condition": "Table 5; CGHAZ; interpass temperature 300 °C; source body row 3"
      }
    ]
  },
  {
    "meta": {
      "name": "CGHAZ; interpass temperature 360 °C",
      "symbol": ""
    },
    "etc": [
      {
        "value": "2.08",
        "unit": "mm",
        "type": "CTODm",
        "condition": "Table 5; CGHAZ; interpass temperature 360 °C; source body row 1"
      },
      {
        "value": "1.91",
        "unit": "mm",
        "type": "CTODm",
        "condition": "Table 5; CGHAZ; interpass temperature 360 °C; source body row 2"
      },
      {
        "value": "1.72",
        "unit": "mm",
        "type": "CTODu",
        "condition": "Table 5; CGHAZ; interpass temperature 360 °C; source body row 4"
      }
    ]
  },
  {
    "meta": {
      "name": "CGHAZ; interpass temperature 400 °C",
      "symbol": ""
    },
    "etc": [
      {
        "value": "2.30",
        "unit": "mm",
        "type": "CTODm",
        "condition": "Table 5; CGHAZ; interpass temperature 400 °C; source body row 1"
      },
      {
        "value": "1.47",
        "unit": "mm",
        "type": "CTODm",
        "condition": "Table 5; CGHAZ; interpass temperature 400 °C; source body row 2"
      },
      {
        "value": "1.14",
        "unit": "mm",
        "type": "CTODu",
        "condition": "Table 5; CGHAZ; interpass temperature 400 °C; source body row 4"
      },
      {
        "value": "1.97",
        "unit": "mm",
        "type": "CTODu",
        "condition": "Table 5; CGHAZ; interpass temperature 400 °C; source body row 5"
      },
      {
        "value": "1.17",
        "unit": "mm",
        "type": "CTODu",
        "condition": "Table 5; CGHAZ; interpass temperature 400 °C; source body row 6"
      }
    ]
  }
]
```
""",
}

paper_jmrt_2025_02_128_table_3 = {
    "contain": ['welding process'],
    "content": """Input: DOI: 10.1016/j.jmrt.2025.02.128
Table 3. Welding process parameters of API X52 pipeline steel.
| Weld bead | Welding method | Welding material | Welding material specification(mm) | Polarity | Current (A) | Voltage (V) | Welding speed(cm·min<sup>−1</sup>) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | GTAW | ER70S-G | 2.5 | DCEN | 132∼137 | 12.6–14.7 | 7∼9 |
| 2 | SMAW | E4314-P | 3.2 | DCEP | 106∼118 | 20.3–23.0 | 9∼10 |
| 3 | SMAW | E4314-P | 3.2 | DCEP | 122∼132 | 21.3–25.4 | 8∼9 |
| 4 | SMAW | E4314-P | 3.2 | DCEP | 118∼130 | 20.2–24.5 | 7∼8 |
| 5 | SMAW | E4314-P | 3.2 | DCEP | 116∼138 | 20.9–25.5 | 8∼9 |
| 6 | SMAW | E4314-P | 3.2 | DCEP | 115∼140 | 21.4–25.3 | 8∼9 |
| 7 | SMAW | E4314-P | 3.2 | DCEP | 107∼125 | 20.9–23.7 | 8∼9 |
| 8 | SMAW | E4314-P | 3.2 | DCEP | 106∼120 | 20.0–24.1 | 8∼9 |
| 9 | SMAW | E4314-P | 3.2 | DCEP | 111∼130 | 20.7–25.2 | 8∼9 |
Notes: Table 3
Requested properties: ["welding_process"]
Output: ```JSON
[
  {
    "meta": {
      "name": "API X52 welded joint; GTAW + SMAW",
      "symbol": ""
    },
    "welding process": [
      {
        "method": "GTAW",
        "filler": "ER70S-G",
        "parameters": "pass=1; base material=API X52; conditions=Table 3; sequential weld beads of the same joint; Welding material specification(mm)=2.5; Polarity=DCEN; Current (A)=132∼137; Voltage (V)=12.6–14.7; Welding speed(cm·min<sup>−1</sup>)=7∼9"
      },
      {
        "method": "SMAW",
        "filler": "E4314-P",
        "parameters": "pass=2; base material=API X52; conditions=Table 3; sequential weld beads of the same joint; Welding material specification(mm)=3.2; Polarity=DCEP; Current (A)=106∼118; Voltage (V)=20.3–23.0; Welding speed(cm·min<sup>−1</sup>)=9∼10"
      },
      {
        "method": "SMAW",
        "filler": "E4314-P",
        "parameters": "pass=3; base material=API X52; conditions=Table 3; sequential weld beads of the same joint; Welding material specification(mm)=3.2; Polarity=DCEP; Current (A)=122∼132; Voltage (V)=21.3–25.4; Welding speed(cm·min<sup>−1</sup>)=8∼9"
      },
      {
        "method": "SMAW",
        "filler": "E4314-P",
        "parameters": "pass=4; base material=API X52; conditions=Table 3; sequential weld beads of the same joint; Welding material specification(mm)=3.2; Polarity=DCEP; Current (A)=118∼130; Voltage (V)=20.2–24.5; Welding speed(cm·min<sup>−1</sup>)=7∼8"
      },
      {
        "method": "SMAW",
        "filler": "E4314-P",
        "parameters": "pass=5; base material=API X52; conditions=Table 3; sequential weld beads of the same joint; Welding material specification(mm)=3.2; Polarity=DCEP; Current (A)=116∼138; Voltage (V)=20.9–25.5; Welding speed(cm·min<sup>−1</sup>)=8∼9"
      },
      {
        "method": "SMAW",
        "filler": "E4314-P",
        "parameters": "pass=6; base material=API X52; conditions=Table 3; sequential weld beads of the same joint; Welding material specification(mm)=3.2; Polarity=DCEP; Current (A)=115∼140; Voltage (V)=21.4–25.3; Welding speed(cm·min<sup>−1</sup>)=8∼9"
      },
      {
        "method": "SMAW",
        "filler": "E4314-P",
        "parameters": "pass=7; base material=API X52; conditions=Table 3; sequential weld beads of the same joint; Welding material specification(mm)=3.2; Polarity=DCEP; Current (A)=107∼125; Voltage (V)=20.9–23.7; Welding speed(cm·min<sup>−1</sup>)=8∼9"
      },
      {
        "method": "SMAW",
        "filler": "E4314-P",
        "parameters": "pass=8; base material=API X52; conditions=Table 3; sequential weld beads of the same joint; Welding material specification(mm)=3.2; Polarity=DCEP; Current (A)=106∼120; Voltage (V)=20.0–24.1; Welding speed(cm·min<sup>−1</sup>)=8∼9"
      },
      {
        "method": "SMAW",
        "filler": "E4314-P",
        "parameters": "pass=9; base material=API X52; conditions=Table 3; sequential weld beads of the same joint; Welding material specification(mm)=3.2; Polarity=DCEP; Current (A)=111∼130; Voltage (V)=20.7–25.2; Welding speed(cm·min<sup>−1</sup>)=8∼9"
      }
    ]
  }
]
```
""",
}

paper_msea_2016_07_045_table_2 = {
    "contain": ['yield strength', 'tensile strength', 'elongation', 'welding process', 'etc'],
    "content": """Input: DOI: 10.1016/j.msea.2016.07.045
Table 2. Mechanical properties and average of the FSW parameters. T: Temperature, YS: Yield strength, TS: Tensile strength, EL: elongation.
| Mechanical properties | Mechanical properties | Mechanical properties | Mechanical properties | Welding parameters | Welding parameters | Welding parameters | Welding parameters |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T (°C) | 25 | −20 | −40 | Pass number sequence | Tool pin length (mm) | Downward force (kN) | *Heat input (kJmm <sup> −1 </sup> ) |
| YS (MPa) | 593±21 | 626±45 | 609±5 | Pass number sequence | Tool pin length (mm) | Downward force (kN) | *Heat input (kJmm <sup> −1 </sup> ) |
| TS (MPa) | 658±34 | 691±1 | 695±1 | P/1 | 9.5 | 34 | 2.1 |
| YS/TS (%) | 90 | 91 | 88 | P/2 | 6.1 | 29 | 1.8 |
| % EL | 17±1 | 14±3 | 16±1 |  |  |  |  |
Notes: Table 2:
Requested properties: ["yield_strength", "tensile_strength", "elongation", "welding_process", "etc"]
Output: ```JSON
[
  {
    "meta": {
      "name": "FSW; mechanical test at 25 °C",
      "symbol": ""
    },
    "yield strength": [
      {
        "value": "593±21",
        "unit": "MPa",
        "type": "YS",
        "condition": "Table 2; mechanical-properties block; test temperature 25 °C"
      }
    ],
    "tensile strength": [
      {
        "value": "658±34",
        "unit": "MPa",
        "type": "TS",
        "condition": "Table 2; mechanical-properties block; test temperature 25 °C"
      }
    ],
    "etc": [
      {
        "value": "90",
        "unit": "%",
        "type": "YS/TS",
        "condition": "Table 2; mechanical-properties block; test temperature 25 °C"
      }
    ],
    "elongation": [
      {
        "value": "17±1",
        "unit": "%",
        "type": "EL",
        "condition": "Table 2; mechanical-properties block; test temperature 25 °C"
      }
    ]
  },
  {
    "meta": {
      "name": "FSW; mechanical test at −20 °C",
      "symbol": ""
    },
    "yield strength": [
      {
        "value": "626±45",
        "unit": "MPa",
        "type": "YS",
        "condition": "Table 2; mechanical-properties block; test temperature −20 °C"
      }
    ],
    "tensile strength": [
      {
        "value": "691±1",
        "unit": "MPa",
        "type": "TS",
        "condition": "Table 2; mechanical-properties block; test temperature −20 °C"
      }
    ],
    "etc": [
      {
        "value": "91",
        "unit": "%",
        "type": "YS/TS",
        "condition": "Table 2; mechanical-properties block; test temperature −20 °C"
      }
    ],
    "elongation": [
      {
        "value": "14±3",
        "unit": "%",
        "type": "EL",
        "condition": "Table 2; mechanical-properties block; test temperature −20 °C"
      }
    ]
  },
  {
    "meta": {
      "name": "FSW; mechanical test at −40 °C",
      "symbol": ""
    },
    "yield strength": [
      {
        "value": "609±5",
        "unit": "MPa",
        "type": "YS",
        "condition": "Table 2; mechanical-properties block; test temperature −40 °C"
      }
    ],
    "tensile strength": [
      {
        "value": "695±1",
        "unit": "MPa",
        "type": "TS",
        "condition": "Table 2; mechanical-properties block; test temperature −40 °C"
      }
    ],
    "etc": [
      {
        "value": "88",
        "unit": "%",
        "type": "YS/TS",
        "condition": "Table 2; mechanical-properties block; test temperature −40 °C"
      }
    ],
    "elongation": [
      {
        "value": "16±1",
        "unit": "%",
        "type": "EL",
        "condition": "Table 2; mechanical-properties block; test temperature −40 °C"
      }
    ]
  },
  {
    "meta": {
      "name": "FSW; welding-parameter block",
      "symbol": ""
    },
    "welding process": [
      {
        "method": "FSW",
        "filler": "",
        "parameters": "pass=P/1; conditions=Table 2; average FSW parameters; adjacent mechanical and welding blocks are independent, not paired row by row; Tool pin length (mm)=9.5; Downward force (kN)=34; Heat input (kJmm−1)=2.1"
      },
      {
        "method": "FSW",
        "filler": "",
        "parameters": "pass=P/2; conditions=Table 2; average FSW parameters; adjacent mechanical and welding blocks are independent, not paired row by row; Tool pin length (mm)=6.1; Downward force (kN)=29; Heat input (kJmm−1)=1.8"
      }
    ]
  }
]
```
""",
}

paper_msea_2016_09_103_table_4 = {
    "contain": ['impact energy'],
    "content": """Input: DOI: 10.1016/j.msea.2016.09.103
Table 4. Results of impact energy test on charged and uncharged E7018 and E7010-G weld metals.
| Electrode | Impact energy (Joule) / No hydrogen precharging | Impact energy (Joule) / 14h hydrogen Precharging |
| --- | --- | --- |
| E7010-G (WM) | 93±16 | 93±20 |
| E7018 (WM) | 185±6 | 180±11 |
Notes: Table 4
Requested properties: ["impact_energy"]
Output: ```JSON
[
  {
    "meta": {
      "name": "E7010-G (WM)",
      "symbol": ""
    },
    "impact energy": [
      {
        "value": "93±16",
        "unit": "Joule",
        "type": "Impact energy",
        "condition": "Table 4; No hydrogen precharging"
      },
      {
        "value": "93±20",
        "unit": "Joule",
        "type": "Impact energy",
        "condition": "Table 4; 14h hydrogen Precharging"
      }
    ]
  },
  {
    "meta": {
      "name": "E7018 (WM)",
      "symbol": ""
    },
    "impact energy": [
      {
        "value": "185±6",
        "unit": "Joule",
        "type": "Impact energy",
        "condition": "Table 4; No hydrogen precharging"
      },
      {
        "value": "180±11",
        "unit": "Joule",
        "type": "Impact energy",
        "condition": "Table 4; 14h hydrogen Precharging"
      }
    ]
  }
]
```
""",
}

paper_msea_2018_01_101_table_5 = {
    "contain": ['yield strength', 'tensile strength', 'elongation', 'etc'],
    "content": """Input: DOI: 10.1016/j.msea.2018.01.101
Table 5. Results of stress-strain curves of HAZ samples in the presence and absence of hydrogen.
[Excerpt: body rows 1, 2; all columns retained.]
| Sample | Yield stress | Tensile stress | Yield ratio | Elongation | Reduction of area | Ln(A0/A) | Ductile fracture percentage | Fracture place |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2HAZ700 (Ref) | 579 | 744 | 0.8 | 23% | 0.6 | 0.9 | 36% | Notch |
| 2HAZ700 (Charged) | 615 | 720 | 0.9 | 9% | 0.2 | 0.3 | 18% | Notch |
Notes: Table 5
Requested properties: ["yield_strength", "tensile_strength", "elongation", "etc"]
Output: ```JSON
[
  {
    "meta": {
      "name": "2HAZ700 (Ref)",
      "symbol": "2HAZ700 (Ref)"
    },
    "yield strength": [
      {
        "value": "579",
        "unit": "",
        "type": "Yield stress",
        "condition": "Table 5; HAZ; 2HAZ700 (Ref); Fracture place=Notch"
      }
    ],
    "tensile strength": [
      {
        "value": "744",
        "unit": "",
        "type": "Tensile stress",
        "condition": "Table 5; HAZ; 2HAZ700 (Ref); Fracture place=Notch"
      }
    ],
    "etc": [
      {
        "value": "0.8",
        "unit": "",
        "type": "Yield ratio",
        "condition": "Table 5; HAZ; 2HAZ700 (Ref); Fracture place=Notch"
      },
      {
        "value": "0.6",
        "unit": "",
        "type": "Reduction of area",
        "condition": "Table 5; HAZ; 2HAZ700 (Ref); Fracture place=Notch"
      },
      {
        "value": "0.9",
        "unit": "",
        "type": "Ln(A0/A)",
        "condition": "Table 5; HAZ; 2HAZ700 (Ref); Fracture place=Notch"
      },
      {
        "value": "36",
        "unit": "%",
        "type": "Ductile fracture percentage",
        "condition": "Table 5; HAZ; 2HAZ700 (Ref); Fracture place=Notch"
      }
    ],
    "elongation": [
      {
        "value": "23",
        "unit": "%",
        "type": "Elongation",
        "condition": "Table 5; HAZ; 2HAZ700 (Ref); Fracture place=Notch"
      }
    ]
  },
  {
    "meta": {
      "name": "2HAZ700 (Charged)",
      "symbol": "2HAZ700 (Charged)"
    },
    "yield strength": [
      {
        "value": "615",
        "unit": "",
        "type": "Yield stress",
        "condition": "Table 5; HAZ; 2HAZ700 (Charged); Fracture place=Notch"
      }
    ],
    "tensile strength": [
      {
        "value": "720",
        "unit": "",
        "type": "Tensile stress",
        "condition": "Table 5; HAZ; 2HAZ700 (Charged); Fracture place=Notch"
      }
    ],
    "etc": [
      {
        "value": "0.9",
        "unit": "",
        "type": "Yield ratio",
        "condition": "Table 5; HAZ; 2HAZ700 (Charged); Fracture place=Notch"
      },
      {
        "value": "0.2",
        "unit": "",
        "type": "Reduction of area",
        "condition": "Table 5; HAZ; 2HAZ700 (Charged); Fracture place=Notch"
      },
      {
        "value": "0.3",
        "unit": "",
        "type": "Ln(A0/A)",
        "condition": "Table 5; HAZ; 2HAZ700 (Charged); Fracture place=Notch"
      },
      {
        "value": "18",
        "unit": "%",
        "type": "Ductile fracture percentage",
        "condition": "Table 5; HAZ; 2HAZ700 (Charged); Fracture place=Notch"
      }
    ],
    "elongation": [
      {
        "value": "9",
        "unit": "%",
        "type": "Elongation",
        "condition": "Table 5; HAZ; 2HAZ700 (Charged); Fracture place=Notch"
      }
    ]
  }
]
```
""",
}
