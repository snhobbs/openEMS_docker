
import os
from pylab import *

from CSXCAD  import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import *

# preview model/mesh only?
# postprocess existing data without re-running simulation?
preview_only = False
postprocess_only = False

# get *.py model path and put simulation files in data directory below
model_path = os.path.normcase(os.path.dirname(__file__))
model_basename = os.path.basename(__file__).replace('.py','')
common_data_path = os.path.join(model_path, 'data')
sim_path = os.path.join(common_data_path,  model_basename)

print('Model path:', model_path)
print('Model basename:', model_basename)
print('Simulation data path:', sim_path, '\n')

# create data directory if it does not exist
if not os.path.exists(sim_path):
    os.makedirs(sim_path)

# change to data directory
os.chdir(sim_path)

############ simulation settings ############

unit = 1e-3 # specify everything in mm
Z0=50 # reference impedance for ports

fstart = 0
fstop  = 10e9
numfreq = 2001  # number of frequency points (has no effect on simulation time!)

maxtime = 2e-9 # stop limit (real time in seconds)

energy_limit = -40    # end criteria for residual energy
Boundaries   = ['PEC', 'PEC', 'PEC', 'PEC', 'PEC', 'PEC']  # xmin xmax ymin ymax zmin zmax

eps_max = 4.4 # maximum permittivity in model, used for calculating max cellsize

lim = exp(energy_limit/10 * log(10))
FDTD = openEMS(EndCriteria=lim, MaxTime=maxtime)
FDTD.SetStepExcite(fstop)
FDTD.SetBoundaryCond( Boundaries )

FDTD.SetOverSampling (20)   # <<<<<<<<<<<<<<<<<<<<<<< oversampling for smoother time curves <<<<<<<<<<<<<<<<<<<<<<<<<<

wavelength_air = (3e8/unit)/fstop
max_cellsize = wavelength_air/(sqrt(eps_max)*20) # max cellsize is lambda/20 in medium

############ Geometry setup ############
CSX = ContinuousStructure()
FDTD.SetCSX(CSX)
mesh = CSX.GetGrid()
mesh.SetDeltaUnit(unit)

# air above and below
air_thick = 5

# substrate
Sub = CSX.AddMaterial('Sub', epsilon=4.4)
Sub_thick = 1.5
Sub_zmin = 0
Sub_zmax = Sub_zmin + Sub_thick

# TopMetal
TopMetal_thick = 0.1
TopMetal_zmin  = Sub_zmax
TopMetal_zmax  = Sub_zmax + TopMetal_thick
TopMetal = CSX.AddMetal('TopMetal')

# BottomMetal
BottomMetal_thick = 0.1
BottomMetal_zmax  = Sub_zmin
BottomMetal_zmin  = Sub_zmin - BottomMetal_thick
BottomMetal = CSX.AddMetal('BottomMetal')


############# begin layout geometries ###########

# TopMetal line over BottomMetal ground
# unit millimeter
wline = 2.7
lline = 100
wgnd  = 20
lgnd  = lline + 10

wdiscont = 5
ldiscont = 20
xdiscont = 30   # discontuity position

# signal line
TopMetal.AddBox(priority=200, start=[-lline/2, -wline/2, TopMetal_zmin], stop=[lline/2, wline/2, TopMetal_zmax])
# ground plane
BottomMetal.AddBox(priority=200, start=[-lgnd/2, -wgnd/2, BottomMetal_zmin], stop=[lgnd/2, wgnd/2, BottomMetal_zmax])
# substrate
Sub.AddBox(priority=200, start=[-lgnd/2, -wgnd/2, Sub_zmin], stop=[lgnd/2, wgnd/2, Sub_zmax])

# discontinuity in signal line
TopMetal.AddBox(priority=200, start=[xdiscont-lline/2, -wdiscont/2, TopMetal_zmin], stop=[xdiscont-lline/2+ldiscont, wdiscont/2, TopMetal_zmax])


############# end layout geometries ##########

############ ports created manually ##########

port_zmin = BottomMetal_zmax
port_zmax = TopMetal_zmin

port1 = FDTD.AddLumpedPort(1, Z0, [-lline/2, -wline/2, port_zmin], [-lline/2, wline/2, port_zmax], 'z', excite=1.0, priority=150)
port2 = FDTD.AddLumpedPort(2, Z0, [ lline/2, -wline/2, port_zmin], [ lline/2, wline/2, port_zmax], 'z', excite=0,   priority=150)

#################  end ports  ################

# Simulation box with some margin to line
box_xmin = -(lgnd/2 + 5)
box_xmax =  (lgnd/2 + 5)
box_ymin = -(wgnd/2 + 5)
box_ymax =  (wgnd/2 + 5)

############# create  mesh  #############

# Detect metal edges and place mesh lines
FDTD.AddEdges2Grid(dirs='all', properties=TopMetal)
FDTD.AddEdges2Grid(dirs='all', properties=BottomMetal)

# manual mesh line in substrate
mesh.AddLine('z',linspace(Sub_zmin, Sub_zmax, 5))

# fine mesh near port 1
mesh.AddLine('x', linspace(-lline/2-wline/2, -lline/2+wline/2, 5))

#finer mesh near port 2
mesh.AddLine('x', linspace(+lline/2-wline/2, +lline/2+wline/2, 5))

# fine mesh across line width
mesh.AddLine('y', linspace(-wline/2, wline/2, 7))


# mesh lines at simulation boundaries

mesh.AddLine('x', box_xmin)
mesh.AddLine('x', box_xmax)

mesh.AddLine('y', box_ymin)
mesh.AddLine('y', box_ymax)

mesh.AddLine('z', TopMetal_zmax + air_thick)
mesh.AddLine('z', BottomMetal_zmin - air_thick)


mesh.SmoothMeshLines('x', max_cellsize, 1.3)
mesh.SmoothMeshLines('y', max_cellsize, 1.3)
mesh.SmoothMeshLines('z', max_cellsize, 1.3)


#################### write model file and view in AppCSXCAD ################

# write CSX file
CSX_file = os.path.join(sim_path, model_basename + '.xml')
CSX.Write2XML(CSX_file)

if not postprocess_only: # preview model, but only for first port excitation
    from CSXCAD import AppCSXCAD_BIN
    os.system(AppCSXCAD_BIN + ' "{}"'.format(CSX_file))

if not preview_only:  # start simulation
    if not postprocess_only:
        FDTD.Run(sim_path, verbose=1)



########### create model, run and post-process ###########

f = np.linspace(fstart,fstop,numfreq)

# call createSimulation function defined above
if not preview_only:
    # evaluate port 1 excitation
    port1.CalcPort( sim_path, f, ref_impedance = Z0)
    port2.CalcPort( sim_path, f, ref_impedance = Z0)


    ### Plot results

    #portVariable.u_data.ui_val[0] = U over time
    #portVariable.i_data.ui_val[0] = I over time
    #portVariable.u_data.ui_time[0] = timesteps
    #portVariable.i_data.ui_time[0] = timesteps (should be same as for voltage)

    u1 = port1.u_data.ui_val[0]
    u2 = port2.u_data.ui_val[0]
    i1 = port1.i_data.ui_val[0]
    i2 = port2.i_data.ui_val[0]
    t = port1.u_data.ui_time[0]

    portZ = Z0
    u1_inc = 0.5 * (u1 + i1 * portZ)
    u1_ref = u1 - u1_inc
    u2_inc = 0.5 * (u2 + i2 * portZ)
    u2_ref = u2 - u2_inc


    figure()
    plot(t,u1 / u1_inc, 'k-', label='u1')
    plot(t,u2 / u1_inc, 'r--',label='u2')
    plot(t,u1_ref / u1_inc, 'b--', label='u1 reflected')
    xlim(0, 2e-9)
    grid()
    legend()
    ylabel('Port voltages (normalized to incident)')
    xlabel('Time (s)')

    savefig(os.path.join(sim_path,'voltages.png'))

    # estimate impedance magnitude
    r = u1_ref / u1_inc
    Z = Z0 * (1+r)/(1-r)

    figure()
    plot(t,Z, 'k-', label='Z')
    xlim(0, 2e-9)
    ylim(0, 100)
    grid()
    legend()
    ylabel('Estimated Z')
    xlabel('Time (s)')


    # show plots
    show()


