"""Welding-domain definitions used directly by the original L2M3 Formatter."""

meta = ('Use only explicitly reported welding experimental data, including base-material controls.\n'
 'Preserve names, numerical strings, units, ranges and parallel measurements. Never invent data.\n'
 'Keep different specimens, welding conditions, passes, test temperatures and WM/HAZ/BM regions '
 'separate.\n'
 'Native meta.name is the reported specimen/material identifier with explicit distinguishing '
 'conditions;\n'
 'meta.symbol is a reported specimen label, or an empty string.\n'
 'Do not use a bare alloy grade to equate different welding conditions. Unknown fields use empty '
 'strings.\n'
 'Output only a JSON-compatible Python literal (strings/numbers/lists/dicts; no null/true/false or '
 'prose).\n')

hardness = 'Reported hardness, including HV/HB/HRC; keep load and tested region.'

stretching_rate = 'Tensile crosshead speed or strain rate; retain original units.'

tensile_strength = 'Ultimate tensile strength; do not confuse with yield strength.'

yield_strength = 'Yield/proof strength, including the stated offset criterion.'

elongation = 'Reported elongation or reduction in elongation; preserve its definition.'

charpy_impact_test_temperature = 'Temperature of the Charpy impact test, not a welding temperature.'

impact_energy = 'Absorbed Charpy impact energy; keep temperature, notch and region.'

welding_process = ('Explicit welding method, pass, filler, current, voltage, speed, heat input, shielding, '
 'preheat/interpass/PWHT or thermal simulation settings.')

etc = 'Other explicitly measured welding-related properties; name each property.'
