# -*- coding: utf-8 -*-
"""
 Tutorials / radar cross section of a metal sphere

 Tested with
  - python 3.10
  - openEMS v0.0.35+

 (c) 2016-2023 Thorsten Liebig <thorsten.liebig@gmx.de>
"""

### Import Libraries
import os
import tempfile
from matplotlib import pyplot as plt
from math import pi, floor, ceil
import numpy as np
from numpy import linspace, imag, real, sqrt, array, log10, cos, sin, arange, squeeze
from numpy.linalg import norm
from dataclasses import dataclass

from pathlib import Path

from CSXCAD import CSXCAD, ContinuousStructure
from openEMS.openEMS import openEMS
from openEMS.physical_constants import C0, EPS0, Z0, MUE0
from openEMS.ports  import UI_data

from mpl_toolkits.mplot3d import Axes3D


@dataclass
class Simulation:
    name: str
    geometry_file: Path
    sim_path: Path

### General parameter setup
dir_  = Path(__file__).parent
name = Path(__file__).stem
sim = Simulation(
    name=name,
    geometry_file= dir_ / f"{name}.xml",
    sim_path=dir_ / "results")


### Setup the simulation
post_proc_only = False

unit = 1e-3 # all length in mm

sphere_rad = 200

inc_angle = 0 #incident angle (to x-axis) in deg

# size of the simulation box
SimBox = 1200
PW_Box = 750

### Setup FDTD parameters & excitation function
FDTD = openEMS(EndCriteria=1e-5)

f_start =  50e6 # start frequency
f_stop  = 1000e6 # stop  frequency
f0      = 500e6
FDTD.SetGaussExcite(  0.5*(f_start+f_stop), 0.5*(f_stop-f_start) )

FDTD.SetBoundaryCond( ['PML_8', 'PML_8', 'PML_8', 'PML_8', 'PML_8', 'PML_8'] )

### Setup Geometry & Mesh
CSX = ContinuousStructure()
FDTD.SetCSX(CSX)
mesh = CSX.GetGrid()
mesh.SetDeltaUnit(unit)

#create mesh
mesh.SetLines('x', [-SimBox/2, 0, SimBox/2])
mesh.SmoothMeshLines('x', C0 / f_stop / unit / 20) # cell size: lambda/20
mesh.SetLines('y', mesh.GetLines('x'))
mesh.SetLines('z', mesh.GetLines('x'))

### Create a metal sphere and plane wave source
sphere_metal = CSX.AddMetal( 'sphere' ) # create a perfect electric conductor (PEC)
sphere_metal.AddSphere(priority=10, center=[0, 0, 0], radius=sphere_rad)

# plane wave excitation
k_dir = [cos(np.deg2rad(inc_angle)), sin(np.deg2rad(inc_angle)), 0] # plane wave direction
E_dir = [0, 0, 1] # plane wave polarization --> E_z

pw_exc = CSX.AddExcitation('plane_wave', exc_type=10, exc_val=E_dir)
pw_exc.SetPropagationDir(k_dir)
pw_exc.SetFrequency(f0)

start = np.array([-PW_Box/2, -PW_Box/2, -PW_Box/2])
stop  = -start
pw_exc.AddBox(start, stop)

# nf2ff calc
nf2ff = FDTD.CreateNF2FFBox()

### Run the simulation
CSX.Write2XML(sim.geometry_file)
FDTD.Run(str(sim.sim_path), cleanup=False)

### Postprocessing & plotting
# get Gaussian pulse strength at frequency f0
ef = UI_data('et', str(sim.sim_path), freq=f0)

Pin = 0.5*norm(E_dir)**2/Z0 * abs(ef.ui_f_val[0])**2
#
nf2ff_res = nf2ff.CalcNF2FF(str(sim.sim_path), f0, 90, arange(-180, 180.1, 2))
RCS = 4*pi/Pin[0]*nf2ff_res.P_rad[0]

fig = plt.figure()
ax  = fig.add_subplot(111, polar=True)
ax.plot( nf2ff_res.phi, RCS[0], 'k-', linewidth=2 )
ax.grid(True)
plt.savefig(dir_ / "phi.svg")

# calculate RCS over frequency
freq = linspace(f_start,f_stop,100)
ef = UI_data( 'et', str(sim.sim_path), freq ) # time domain/freq domain voltage
Pin = 0.5*norm(E_dir)**2/Z0 * abs(np.array(ef.ui_f_val[0]))**2

nf2ff_res = nf2ff.CalcNF2FF(str(sim.sim_path), freq, 90, 180+inc_angle, outfile='back_nf2ff.h5')

back_scat = np.array([4*pi/Pin[fn]*nf2ff_res.P_rad[fn][0][0] for fn in range(len(freq))])

plt.figure()
plt.plot(freq/1e6,back_scat, linewidth=2)
plt.grid()
plt.xlabel('frequency (MHz)')
plt.ylabel('RCS ($m^2$)')
plt.title('radar cross section')
plt.savefig(dir_ / "radar_cross_section.svg")

plt.figure()
plt.semilogy(sphere_rad*unit/C0*freq,back_scat/(pi*sphere_rad*unit*sphere_rad*unit), linewidth=2)
plt.ylim([10^-2, 10^1])
plt.grid()
plt.xlabel('sphere radius / wavelength')
plt.ylabel('RCS / ($\pi a^2$)')
plt.title('normalized radar cross section')
plt.savefig(dir_ / "radar_cross_section_normalized.svg")
