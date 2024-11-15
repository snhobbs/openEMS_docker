# -*- coding: utf-8 -*-
"""
 Rectangular Waveguide Tutorial

 Tested with
  - python 3.10
  - openEMS v0.0.35+

 (c) 2015-2023 Thorsten Liebig <thorsten.liebig@gmx.de>

"""
import os
import tempfile
from matplotlib import pyplot as plt
from math import pi
import numpy as np
from dataclasses import dataclass

from pathlib import Path

from CSXCAD import CSXCAD
from openEMS.openEMS import openEMS
from openEMS.physical_constants import C0, EPS0, Z0, MUE0

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
unit = 1e-6; #drawing unit in um

# waveguide dimensions
# WR42
a = 10700;   #waveguide width
b = 4300;    #waveguide height
length = 50000;

# frequency range of interest
f_start = 20e9;
f_0     = 24e9;
f_stop  = 26e9;
lambda0 = C0/f_0/unit;

#waveguide TE-mode definition
TE_mode = 'TE10';

#targeted mesh resolution
mesh_res = lambda0/30

### Setup FDTD parameter & excitation function
FDTD = openEMS(NrTS=1e4);
FDTD.SetGaussExcite(0.5*(f_start+f_stop),0.5*(f_stop-f_start));

# boundary conditions
FDTD.SetBoundaryCond([0, 0, 0, 0, 3, 3]);

### Setup geometry & mesh
CSX = CSXCAD.ContinuousStructure()
FDTD.SetCSX(CSX)
mesh = CSX.GetGrid()
mesh.SetDeltaUnit(unit)

mesh.AddLine('x', [0, a])
mesh.AddLine('y', [0, b])
mesh.AddLine('z', [0, length])

## Apply the waveguide port
ports = []
start=[0, 0, 10*mesh_res];
stop =[a, b, 15*mesh_res];
mesh.AddLine('z', [start[2], stop[2]])
ports.append(FDTD.AddRectWaveGuidePort( 0, start, stop, 'z', a*unit, b*unit, TE_mode, 1))

start=[0, 0, length-10*mesh_res];
stop =[a, b, length-15*mesh_res];
mesh.AddLine('z', [start[2], stop[2]])
ports.append(FDTD.AddRectWaveGuidePort( 1, start, stop, 'z', a*unit, b*unit, TE_mode))

mesh.SmoothMeshLines('all', mesh_res, ratio=1.4)

### Define dump box...
Et = CSX.AddDump('Et', file_type=0, sub_sampling=[2,2,2])
start = [0, 0, 0];
stop  = [a, b, length];
Et.AddBox(start, stop);

### Run the simulation
CSX.Write2XML(sim.geometry_file)

FDTD.Run(str(sim.sim_path), cleanup=False)

### Postprocessing & plotting
freq = np.linspace(f_start,f_stop,201)
for port in ports:
    port.CalcPort(str(sim.sim_path), freq)

s11 = ports[0].uf_ref / ports[0].uf_inc
s21 = ports[1].uf_ref / ports[0].uf_inc
ZL  = ports[0].uf_tot / ports[0].if_tot
ZL_a = ports[0].ZL # analytic waveguide impedance

## Plot s-parameter
plt.figure()
plt.plot(freq*1e-6,20*np.log10(abs(s11)),'k-',linewidth=2, label='$S_{11}$')
plt.grid()
plt.plot(freq*1e-6,20*np.log10(abs(s21)),'r--',linewidth=2, label='$S_{21}$')
plt.legend();
plt.ylabel('S-Parameter (dB)')
plt.xlabel(r'frequency (MHz) $\rightarrow$')
plt.savefig(dir_ / "sparam.svg")

## Compare analytic and numerical wave-impedance
plt.figure()
plt.plot(freq*1e-6,np.real(ZL), linewidth=2, label='$\Re\{Z_L\}$')
plt.grid()
plt.plot(freq*1e-6,np.imag(ZL),'r--', linewidth=2, label='$\Im\{Z_L\}$')
plt.plot(freq*1e-6,ZL_a,'g-.',linewidth=2, label='$Z_{L, analytic}$')
plt.ylabel('ZL $(\Omega)$')
plt.xlabel(r'frequency (MHz) $\rightarrow$')
plt.legend()
plt.savefig(dir_ / "frequency_impedance.svg")
