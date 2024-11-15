simulations = [
  "Bent_Patch_Antenna",
  "CRLH_Extraction",
  "Circ_Waveguide",
  "Helical_Antenna",
  "MSL_NotchFilter",
  "Parallel_Plate_Waveguide",
  "RCS_Sphere",
  "Rect_Waveguide",
  "Simple_Patch_Antenna",
]

import os
from pathlib import Path

for p in simulations:
  os.system(f"python3 {p}/{p}.py")
