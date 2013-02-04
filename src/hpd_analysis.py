import numpy as np
import netCDF4
from matplotlib import pyplot as plt

try:
    p2v = np.load('lesker275i.npy') # try to load pressure to voltage conversion table
except:
    print "Could not load pressure to voltage table lesker275i.npy"
    p2v = None

def convPressure(volts):
    if p2v is None:
        print "Could not convert, no pressure look up table"
        return volts
    ptab = p2v[1:,0] #pressures, skip 0 Torr pressure value
    vtab = p2v[1:,1] #voltages
    press = 10**np.interp(volts,vtab,np.log10(ptab)) # interpolate in semilog space
    return press

def plotTemps(filename):
    nc = netCDF4.Dataset(filename)
    mjd = nc.variables['mjd_slow']
    t = (mjd[:]-mjd[0])*86400 # time in seconds
    fr = nc.groups['fridge']
    bt = fr.variables['bridge_temp_value'][:]
    magcur = fr.variables['dvm_volts_1'][:]
    t60k = fr.variables['therm_temperature_0'][:]
    tpillk = fr.variables['therm_temperature_1'][:]
    t4k = fr.variables['therm_temperature_2'][:]
    press = convPressure(fr.variables['dvm_volts_3'][:])
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
    
    f = plt.figure()
    ax = f.add_subplot(111)
#    ax2 = ax.twinx()
    ax.plot(t/3600,t4k,lw=2, label='4K Board Temp')
    ax.plot(t/3600,tpillk,lw=2,label='ADR Pill Temp')
    ax.plot(t/3600,t60k,lw=2,label='60 K stage Temp')
#    ax2.semilogy(t/3600,press,lw=2,label='Pressure (torr)')
    ax.set_xlabel('Time (hours)')
    ax.set_ylabel('Temperature (K)')
    ax.set_title('Cryostat temperatures vs. time\n%s' % filename)
    ax.legend(loc='upper right')
    ax.grid()    
    
    
    
    nc.close()
    return t,bt,magcur
    
