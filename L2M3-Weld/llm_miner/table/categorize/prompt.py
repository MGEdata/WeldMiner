PROMPT_CATEGORIZE = """Classify this welding table. Return only one label with no quotes:
Property: measured material properties, including mechanical, impact, hardness, fracture-toughness and hydrogen-related measurements; no welding-process settings.
Welding Process: welding parameters, pass sequences, pre-weld conditions, PWHT or thermal-treatment settings; no measured material properties.
Mixed: both welding-process settings and measured material properties in the same table. Keep the whole table together.
Test temperature, hydrogen charging conditions and specimen dimensions accompanying measurements do not by themselves make a table Mixed.
Elemental Composition: only chemical composition.
Coordinate: unrelated tables, bibliographies or nonexperimental summaries.
Do not use Crystal for welding process or mechanical-property tables.

Representative welding-table examples:

Input: DOI: 10.1016/j.corsci.2025.113442
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
Output: "Property"

Input: DOI: 10.1016/j.ijpvp.2012.05.011
Table 4. Measured mechanical properties of X65 pipeline in transverse direction and target values specified by API 5L.
| API grade | Dimensions / Outside diameter (D: mm) | Dimensions / Wall thickness (t: mm) | Dimensions / D/t | Tensile properties / YS (MPa) | Tensile properties / TS (MPa) | Tensile properties / Y/T | Tensile properties / Elongation in (2 in.) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| X65 | 1219 | 14.3 | 85 | 490 | 552 | 0.89 | 21 |
| Minimum | Minimum | Minimum | Minimum | 448 | 531 | – | – |
| Maximum | Maximum | Maximum | Maximum | 600 | 758 | 0.93 | – |
Notes: YS: yield strength, TS: tensile strength.
Output: "Property"

Input: DOI: 10.1016/j.ijpvp.2012.05.011
Table 6. Measured hardness data for X65 pipeline base material, fusion zone, and heat affected zone (HV10).
| Location | Base metal | Heat affected zone | Fusion zone |
| --- | --- | --- | --- |
| Max. hardness | 212 | 212 | 222 |
| Min. hardness | 210 | 206 | 207 |
| Ave. hardness | 211 | 208 | 218 |
Output: "Property"

Input: DOI: 10.1016/j.ijpvp.2016.10.004
Table 7. Charpy impact toughness.
[Excerpt: body rows 1, 13, 16; all columns retained.]
| Temp (°C) | Sampling direction | Number | Sample size | AKV (J) |
| --- | --- | --- | --- | --- |
| 25 | Transverse direction of new pipe | 1-1-T | 10 × 10 × 55 | >179 |
| 25 | Weld | 1-3-R | 10 × 10 × 55 | 14 |
| 650 | Weld | 1-3-O | 10 × 10 × 55 | 72 |
Notes: Table 7
Output: "Property"

Input: DOI: 10.1016/j.ijpvp.2017.04.003
Table 3. Examined mechanical properties of the utilized API X60 steel.
| Mechanical property | Value |
| --- | --- |
| Yield strength (MPa) | 430 |
| Ultimate tensile strength (MPa) | 535 |
| Elongation in 2″ gauge (%) | 36 |
| Hardness (Hv) | 172 |
| Impact energy at 0 °C (J) | 96 |
Notes: Table 3
Output: "Property"

Input: DOI: 10.1016/j.ijpvp.2017.04.003
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
Output: "Welding Process"

Input: DOI: 10.1016/j.jmapro.2020.01.014
Table 4. Hardness of welded joints.
| Hardness | BM | WM | CGHAZ | FGHAZ | ICHAZ | SCHAZ |
| --- | --- | --- | --- | --- | --- | --- |
| (HV) | 220-194 | 209-201 | 278-251 | 257-246 | 207-189 | 191-181 |
Notes: Table 4
Output: "Property"

Input: DOI: 10.1016/j.jmapro.2021.11.021
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
Output: "Welding Process"

Input: DOI: 10.1016/j.jmatprotec.2022.117621
Table 4. Tensile data of the as-welded and as-annealed joints.
| Sample | Yield strength/MPa | Ultimate tensile strength/MPa | Elongation/% | Joint efficiency/% |
| --- | --- | --- | --- | --- |
| BM | 632.3 ± 5 | 755.7 ± 7 | 38 ± 1.5 | – |
| As-annealed BM | 616.3 ± 3 | 793.5 ± 5 | 37.8 ± 1.4 | – |
| As-welded joint | 706.6 ± 7 | 758.5 ± 4 | 22.5 ± 1.3 | 100.4 |
| As-annealed joint | 616.5 ± 2.5 | 782.5 ± 4.7 | 32.5 ± 1.7 | 103.5 |
Notes: Table 4
Output: "Property"

Input: DOI: 10.1016/j.jmatprotec.2022.117621
Table 3. Impact energy of the as-welded joint.
| V-shaped Notch locations | BM | HAZ | NZ |
| --- | --- | --- | --- |
| Impact energy at − 40 °C /J/cm<sup>2</sup> | 190 | 121.6 | 73.6 |
Notes: Table 3
Output: "Property"

Input: DOI: 10.1016/j.jmrt.2022.05.141
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
Output: "Property"

Input: DOI: 10.1016/j.jmrt.2025.02.128
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
Output: "Welding Process"

Input: DOI: 10.1016/j.msea.2016.07.045
Table 2. Mechanical properties and average of the FSW parameters. T: Temperature, YS: Yield strength, TS: Tensile strength, EL: elongation.
| Mechanical properties | Mechanical properties | Mechanical properties | Mechanical properties | Welding parameters | Welding parameters | Welding parameters | Welding parameters |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T (°C) | 25 | −20 | −40 | Pass number sequence | Tool pin length (mm) | Downward force (kN) | *Heat input (kJmm <sup> −1 </sup> ) |
| YS (MPa) | 593±21 | 626±45 | 609±5 | Pass number sequence | Tool pin length (mm) | Downward force (kN) | *Heat input (kJmm <sup> −1 </sup> ) |
| TS (MPa) | 658±34 | 691±1 | 695±1 | P/1 | 9.5 | 34 | 2.1 |
| YS/TS (%) | 90 | 91 | 88 | P/2 | 6.1 | 29 | 1.8 |
| % EL | 17±1 | 14±3 | 16±1 |  |  |  |  |
Notes: Table 2:
Output: "Mixed"

Input: DOI: 10.1016/j.msea.2016.09.103
Table 4. Results of impact energy test on charged and uncharged E7018 and E7010-G weld metals.
| Electrode | Impact energy (Joule) / No hydrogen precharging | Impact energy (Joule) / 14h hydrogen Precharging |
| --- | --- | --- |
| E7010-G (WM) | 93±16 | 93±20 |
| E7018 (WM) | 185±6 | 180±11 |
Notes: Table 4
Output: "Property"

Input: DOI: 10.1016/j.msea.2018.01.101
Table 5. Results of stress-strain curves of HAZ samples in the presence and absence of hydrogen.
[Excerpt: body rows 1, 2; all columns retained.]
| Sample | Yield stress | Tensile stress | Yield ratio | Elongation | Reduction of area | Ln(A0/A) | Ductile fracture percentage | Fracture place |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2HAZ700 (Ref) | 579 | 744 | 0.8 | 23% | 0.6 | 0.9 | 36% | Notch |
| 2HAZ700 (Charged) | 615 | 720 | 0.9 | 9% | 0.2 | 0.3 | 18% | Notch |
Notes: Table 5
Output: "Property"

Input: {paragraph}
"""


FT_CATEGORIZE = """Classify this welding table. Return only one label with no quotes:
Property: measured material properties, including mechanical, impact, hardness, fracture-toughness and hydrogen-related measurements; no welding-process settings.
Welding Process: welding parameters, pass sequences, pre-weld conditions, PWHT or thermal-treatment settings; no measured material properties.
Mixed: both welding-process settings and measured material properties in the same table. Keep the whole table together.
Test temperature, hydrogen charging conditions and specimen dimensions accompanying measurements do not by themselves make a table Mixed.
Elemental Composition: only chemical composition.
Coordinate: unrelated tables, bibliographies or nonexperimental summaries.
Do not use Crystal for welding process or mechanical-property tables.

Input: {paragraph}
"""


FT_HUMAN = "{paragraph}"
