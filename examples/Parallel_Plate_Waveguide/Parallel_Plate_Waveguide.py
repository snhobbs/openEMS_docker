#
# Tutorial at https://wiki.openems.de/index.php/Tutorial:_Parallel_Plate_Waveguide.html
#
#
#

import os
import tempfile
import copy
from math import pi
from pathlib import Path
from dataclasses import dataclass

import numpy as np
from matplotlib import pyplot as plt

from CSXCAD  import ContinuousStructure, CSProperties
from openEMS import openEMS
from openEMS.physical_constants import C0, EPS0, Z0, MUE0


@dataclass
class Simulation:
    name: str
    geometry_file: Path
    sim_path: Path

### General parameter setup
dir_  = Path(__file__).parent
name  = Path(__file__).stem
sim = Simulation(
    name=name,
    geometry_file=dir_ / f'{name}.xml',
    sim_path=dir_ / "results")

### FDTD setup
## * Limit the simulation to 100 timesteps
## * Define a reduced end criteria of -40dB
FDTD = openEMS(CoordSystem=0, NrTS=100, EndCriteria=0, OverSampling=50)
f0 = 10e6

CSX = ContinuousStructure()
pset = CSX.GetParameterSet()

excitation = CSProperties.CSPropExcitation(pset, exc_type=0)  # Soft E-Field
# excitation.SetPropagationDir((1,0,0))
excitation.SetExcitation((0,1,0))
excitation.SetFrequency(f0)
excitation.SetName("excitation")

#air = CSProperties.CSPropMaterial(pset, 'air', epsilon=1)
#metal = CSProperties.CSPropMetal(pset, 'metal')
#CSX.AddProperty(air)
#CSX.AddProperty(metal)
CSX.AddProperty(excitation)

FDTD.SetSinusExcite(f0)
FDTD.SetBoundaryCond( ['PMC', 'PMC', 'PEC', 'PEC', 'MUR', 'MUR'] )
FDTD.SetCSX(CSX)
mesh = CSX.GetGrid()
mesh.SetDeltaUnit(1)

# size of the simulation box
SimBox = np.array([20, 20, 40])

excitation.AddBox(start=[-SimBox[0]/2,-SimBox[1]/2, 0], stop=[SimBox[0]/2,SimBox[1]/2,0])

mesh.AddLine('x', np.arange(-SimBox[0]/2, SimBox[0]/2))
mesh.AddLine('y', np.arange(-SimBox[1]/2, SimBox[1]/2))
mesh.AddLine('z', np.arange(-SimBox[2]/4, SimBox[2]*3/4))


Et = CSX.AddDump('Et')
Et.AddBox(start=[-SimBox[0]/2,0,-SimBox[2]/4], stop=[10,0,SimBox[2]*3/4]);

# os.mkdir(str(sim.sim_path))

CSX.Write2XML(str(sim.geometry_file))
FDTD.Run(str(sim.sim_path), cleanup=False)
