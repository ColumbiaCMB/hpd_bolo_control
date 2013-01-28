import numpy as np
import netCDF4
from matplotlib import pyplot as plt


def plotTemps(filename):
    nc = netCDF4.Dataset(filename)
    mjd = nc.variables['mjd_slow']
    t = (mjd[:]-mjd[0])*86400 # time in seconds
    fr = nc.groups['fridge']
    bt = fr.variables['bridge_temp_value'][:]
    magcur = fr.variables['dvm_volts_1'][:]
    f = plt.figure()
    ax = f.add_subplot(111)
    ax.plot(t/3600., bt, lw=2)
    ax.set_xlabel('Time (hours)')
    ax.set_ylabel('Temperature (K)')
    ax.set_title('Package temperature vs. time\n%s' % filename)
    ax.grid()
    
    f = plt.figure()
    ax = f.add_subplot(111)
    ax.plot(magcur, bt, ',')
    ax.set_xlabel('Magnet current (A)')
    ax.set_ylabel('Temperature (K)')
    ax.set_title('Package temperature vs. magnet current\n%s' % filename)
    ax.grid()
    nc.close()
    return t,bt,magcur
