import os
from pylab import *

from CSXCAD  import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import *

# preview model/mesh only?
# postprocess existing data without re-running simulation?
preview_only = False
postprocess_only = False

# Simulate reverse path (S22 and S12) also?
full_2port = True

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

energy_limit = -40    # end criteria for residual energy
Boundaries   = ['PEC', 'PEC', 'PEC', 'PEC', 'PEC', 'PEC']  # xmin xmax ymin ymax zmin zmax

eps_max = 4.4 # maximum permittivity in model, used for calculating max cellsize

lim = exp(energy_limit/10 * log(10))
FDTD = openEMS(EndCriteria=lim)
FDTD.SetGaussExcite( (fstart+fstop)/2, (fstop-fstart)/2 )
FDTD.SetBoundaryCond( Boundaries )

wavelength_air = (3e8/unit)/fstop
max_cellsize = wavelength_air/(sqrt(eps_max)*20) # max cellsize is lambda/20 in medium
max_cellsize = min(max_cellsize, 2) # using lambda/20 would be too large here, creating abrupt steps in cell size -> use smaller value for nicely graded mesh

def createSimulation (exciteport):
# Define function for model creation because we need to create and run separate CSX
# for each excitation. For S11,S21 we only need to excite port 1, but for S22,S12
# we need to excite port 2. This requires separate CSX with different port settings.


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

    if exciteport==1:
        port1 = FDTD.AddLumpedPort(1, Z0, [-lline/2, -wline/2, port_zmin], [-lline/2, wline/2, port_zmax], 'z', excite=1.0, priority=150)
        port2 = FDTD.AddLumpedPort(2, Z0, [ lline/2, -wline/2, port_zmin], [ lline/2, wline/2, port_zmax], 'z', excite=0,   priority=150)
    else:
        port1 = FDTD.AddLumpedPort(1, Z0, [-lline/2, -wline/2, port_zmin], [-lline/2, wline/2, port_zmax], 'z', excite=0,   priority=150)
        port2 = FDTD.AddLumpedPort(2, Z0, [ lline/2, -wline/2, port_zmin], [ lline/2, wline/2, port_zmax], 'z', excite=1.0, priority=150)


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
    mesh.AddLine('y', linspace(-wline/2, wline/2,7))


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


    # create subdirectory to hold data for this excitation
    excitation_path = os.path.join(sim_path, 'sub-' + str(exciteport))
    if not os.path.exists(excitation_path):
        os.makedirs(excitation_path)

    # write CSX file
    CSX_file = os.path.join(excitation_path, model_basename + '.xml')
    CSX.Write2XML(CSX_file)

    if not postprocess_only: # preview model, but only for first port excitation
        if (exciteport==1):
            from CSXCAD import AppCSXCAD_BIN
            os.system(AppCSXCAD_BIN + ' "{}"'.format(CSX_file))

    if not preview_only:  # start simulation
        if not postprocess_only:
            print("Running FDTD simulation, excitation port " + str(exciteport))
            FDTD.Run(excitation_path, verbose=1)

    # return ports, so that we can postprocess them
    return port1, port2, excitation_path

######### end of function createSimulation (exciteport) ##########



########### create model, run and post-process ###########

f = np.linspace(fstart,fstop,numfreq)

# call createSimulation function defined above
sub1_port1, sub1_port2, sub1_excitation_path = createSimulation (1)  # excite port 1
if full_2port:
    sub2_port1, sub2_port2, sub2_excitation_path = createSimulation (2)  # excite port 2

if not preview_only:
    # evaluate port 1 excitation
    sub1_port1.CalcPort( sub1_excitation_path, f, ref_impedance = Z0)
    sub1_port2.CalcPort( sub1_excitation_path, f, ref_impedance = Z0)

    s11 = sub1_port1.uf_ref / sub1_port1.uf_inc
    s21 = sub1_port2.uf_ref / sub1_port1.uf_inc

    if full_2port:
        # evaluate port 2 excitation
        sub2_port1.CalcPort( sub2_excitation_path, f, ref_impedance = Z0)
        sub2_port2.CalcPort( sub2_excitation_path, f, ref_impedance = Z0)

        s22 = sub2_port2.uf_ref / sub2_port2.uf_inc
        s12 = sub2_port1.uf_ref / sub2_port2.uf_inc

    Zin_port1 = sub1_port1.uf_tot / sub1_port1.if_tot

    ### Plot results

    s11_dB = 20.0*np.log10(np.abs(s11))
    s11_phase = angle(s11, deg=True)

    s21_dB = 20.0*np.log10(np.abs(s21))
    s21_phase = angle(s21, deg=True)

    if full_2port:
        s22_dB = 20.0*np.log10(np.abs(s22))
        s22_phase = angle(s22, deg=True)

        s12_dB = 20.0*np.log10(np.abs(s12))
        s12_phase = angle(s12, deg=True)


    ## Plot reflection coefficient S11
    figure()
    plot( f/1e6, s11_dB, 'k-', linewidth=2, label='dB(S11)' )
    plot( f/1e6, s21_dB, 'r-', linewidth=2, label='dB(S21)' )
    grid()
    title( 'S11 and S21' )
    xlabel( 'frequency (MHz)' )
    ylabel( 'dB' )
    legend()

    if full_2port:
        # create Touchstone S2P output file in simulation data path
        s2p_name = os.path.join(sim_path, model_basename + '.s2p')
        s2p_file = open(s2p_name, 'w')
        s2p_file.write('#   Hz   S  RI   R   50\n')
        s2p_file.write('!\n')
        for index in range(0, numfreq):
            freq = f[index]
            s11re = real(s11[index])
            s11im = imag(s11[index])
            s12re = real(s12[index])
            s12im = imag(s12[index])
            s21re = real(s21[index])
            s21im = imag(s21[index])
            s22re = real(s22[index])
            s22im = imag(s22[index])
            s2p_file.write(f"{freq} {s11re} {s11im} {s21re} {s21im} {s12re} {s12im} {s22re} {s22im} \n")
        s2p_file.close()


    # show plots
    show()
