import sys
import os
import skrf
import matplotlib.pyplot as plt
skrf.stylely()

model_path = os.path.normcase(os.path.dirname(__file__))
network_filename = os.path.join(model_path,  'discont_sparam_2port.s2p')

network = skrf.Network(network_filename)
network_dc = network.extrapolate_to_dc(kind='linear')

plt.figure()
plt.title("Time Domain Reflectometry")
network_dc.s11.plot_z_time_step(window='hamming', label="impedance")
plt.xlim((0, 2))

plt.tight_layout()
plt.show()

