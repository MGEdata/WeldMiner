"""Welding-domain definitions used directly by the original L2M3 Formatter."""

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
