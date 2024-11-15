# -*- coding: utf-8 -*-
"""
 Helical Antenna Tutorial

 Tested with
  - python 3.10
  - openEMS v0.0.35+

 (c) 2015-2023 Thorsten Liebig <thorsten.liebig@gmx.de>

"""

### Import Libraries
import os
import tempfile
from matplotlib import pyplot as plt
from math import pi, floor, ceil
import numpy as np
from numpy import linspace, imag, real, sqrt, array, log10, cos, sin, arange, squeeze, interp
from dataclasses import dataclass

from pathlib import Path

from CSXCAD import CSXCAD, ContinuousStructure
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

unit = 1e-3 # all length in mm

f0 = 2.4e9 # center frequency, frequency of interest!
lambda0 = round(C0/f0/unit) # wavelength in mm
fc = 0.5e9 # 20 dB corner frequency

Helix_radius = 20 # --> diameter is ~ lambda/pi
Helix_turns = 10  # --> expected gain is G ~ 4 * 10 = 40 (16dBi)
Helix_pitch = 30  # --> pitch is ~ lambda/4
Helix_mesh_res = 3

gnd_radius = lambda0/2

# feeding
feed_height = 3
feed_R = 120    #feed impedance

# size of the simulation box
SimBox = array([1, 1, 1.5])*2.0*lambda0

### Setup FDTD parameter & excitation function
FDTD = openEMS(EndCriteria=1e-4)
FDTD.SetGaussExcite( f0, fc )
FDTD.SetBoundaryCond( ['MUR', 'MUR', 'MUR', 'MUR', 'MUR', 'PML_8'] )

### Setup Geometry & Mesh
CSX = CSXCAD.ContinuousStructure()
FDTD.SetCSX(CSX)
mesh = CSX.GetGrid()
mesh.SetDeltaUnit(unit)

max_res = floor(C0 / (f0+fc) / unit / 20) # cell size: lambda/20

# create helix mesh
mesh.AddLine('x', [-Helix_radius, 0, Helix_radius])
mesh.SmoothMeshLines('x', Helix_mesh_res)
# add the air-box
mesh.AddLine('x', [-SimBox[0]/2-gnd_radius,  SimBox[0]/2+gnd_radius])
# create a smooth mesh between specified fixed mesh lines
mesh.SmoothMeshLines('x', max_res, ratio=1.4)

# copy x-mesh to y-direction
mesh.SetLines('y', mesh.GetLines('x'))

# create helix mesh in z-direction
mesh.AddLine('z', [0, feed_height, Helix_turns*Helix_pitch+feed_height])
mesh.SmoothMeshLines('z', Helix_mesh_res)

# add the air-box
mesh.AddLine('z', [-SimBox[2]/2, max(mesh.GetLines('z'))+SimBox[2]/2 ])
# create a smooth mesh between specified fixed mesh lines
mesh.SmoothMeshLines('z', max_res, ratio=1.4)

### Create the Geometry
## * Create the metal helix using the wire primitive.
## * Create a metal gorund plane as cylinder.
# create a perfect electric conductor (PEC)
helix_metal = CSX.AddMetal('helix' )

ang = linspace(0,2*pi,21)[0]
coil_x = Helix_radius*cos(ang)
coil_y = Helix_radius*sin(ang)
coil_z = ang/2/pi*Helix_pitch

helix_x = []
helix_y = []
helix_z = []
zpos = feed_height

for n in range(Helix_turns-1):
    helix_x.append(coil_x)
    helix_y.append(coil_y)
    helix_z.append(coil_z+zpos)
    zpos = zpos + Helix_pitch

print(helix_x)
print(helix_y)
print(helix_z)
helix_metal.AddCurve(points=[helix_x, helix_y, helix_z])

# create ground circular ground
gnd = CSX.AddMetal( 'gnd' ) # create a perfect electric conductor (PEC)

# add a box using cylindrical coordinates
start = [0, 0, -0.1]
stop  = [0, 0,  0.1]
gnd.AddCylinder(start, stop, radius=gnd_radius)

# apply the excitation & resist as a current source
start = [Helix_radius, 0, 0]
stop  = [Helix_radius, 0, feed_height]
port = FDTD.AddLumpedPort(1 ,feed_R, start, stop, 'z', 1.0, priority=5)

# nf2ff calc
nf2ff = FDTD.CreateNF2FFBox(opt_resolution=[lambda0/15]*3)

### Run the simulation
CSX.Write2XML(sim.geometry_file)

FDTD.Run(str(sim.sim_path), cleanup=False)

### Postprocessing & plotting
freq = linspace( f0-fc, f0+fc, 501 )
port.CalcPort(str(sim.sim_path), freq)

Zin = port.uf_tot / port.if_tot
s11 = port.uf_ref / port.uf_inc

## Plot the feed point impedance
plt.figure()
plt.plot( freq/1e6, real(Zin), 'k-', linewidth=2, label=r'$\Re(Z_{in})$' )
plt.grid()
plt.plot( freq/1e6, imag(Zin), 'r--', linewidth=2, label=r'$\Im(Z_{in})$' )
plt.title( 'feed point impedance' )
plt.xlabel( 'frequency (MHz)' )
plt.ylabel( 'impedance ($\Omega$)' )
plt.legend( )
plt.savefig(dir_ / "feedpoint_impedance.svg")

## Plot reflection coefficient S11
plt.figure()
plt.plot( freq/1e6, 20*log10(abs(s11)), 'k-', linewidth=2 )
plt.grid()
plt.title( 'reflection coefficient $S_{11}$' )
plt.xlabel( 'frequency (MHz)' )
plt.ylabel( 'reflection coefficient $|S_{11}|$' )
plt.savefig(dir_ / "reflection_s11.svg")

### Create the NFFF contour
## * calculate the far field at phi=0 degrees and at phi=90 degrees
theta = arange(0.,180.,1.)
phi = arange(-180,180,2)
print( 'calculating the 3D far field...' )

nf2ff_res = nf2ff.CalcNF2FF(str(sim.sim_path), f0, theta, phi, read_cached=True, verbose=True )

Dmax_dB = 10*log10(nf2ff_res.Dmax[0])
E_norm = 20.0*log10(nf2ff_res.E_norm[0]/np.max(nf2ff_res.E_norm[0])) + 10*log10(nf2ff_res.Dmax[0])

theta_HPBW = theta[ np.where(squeeze(E_norm[:,phi==0])<Dmax_dB-3)[0][0] ]

## * Display power and directivity
print('radiated power: Prad = {} W'.format(nf2ff_res.Prad[0]))
print('directivity: Dmax = {} dBi'.format(Dmax_dB))
print('efficiency: nu_rad = {} %'.format(100*nf2ff_res.Prad[0]/interp(f0, freq, port.P_acc)))
print('theta_HPBW = {} °'.format(theta_HPBW))

E_norm = 20.0*log10(nf2ff_res.E_norm[0]/np.max(nf2ff_res.E_norm[0])) + 10*log10(nf2ff_res.Dmax[0])
E_CPRH = 20.0*log10(np.abs(nf2ff_res.E_cprh[0])/np.max(nf2ff_res.E_norm[0])) + 10*log10(nf2ff_res.Dmax[0])
E_CPLH = 20.0*log10(np.abs(nf2ff_res.E_cplh[0])/np.max(nf2ff_res.E_norm[0])) + 10*log10(nf2ff_res.Dmax[0])

## * Plot the pattern
plt.figure()
plt.plot(theta, E_norm[:,phi==0],'k-' , linewidth=2, label='$|E|$')
plt.plot(theta, E_CPRH[:,phi==0],'g--', linewidth=2, label='$|E_{CPRH}|$')
plt.plot(theta, E_CPLH[:,phi==0],'r-.', linewidth=2, label='$|E_{CPLH}|$')
plt.grid()
plt.xlabel('theta (deg)')
plt.ylabel('directivity (dBi)')
plt.title('Frequency: {} GHz'.format(nf2ff_res.freq[0]/1e9))
plt.legend()
plt.savefig(dir_ / "directivity.svg")
