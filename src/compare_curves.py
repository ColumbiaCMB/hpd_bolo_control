"""
Last edited by Joshua Sobrin on 2014-01-12

This script contains a function called "plot_curves"
which asks for two netCDF4 files,
and then mines temperature data from them.
It then plots the temperature curves from both cooldowns
on the same figure, allowing a comparison of 2 cooldowns
"""

import netCDF4
from matplotlib import pyplot

def plot_curves(filename_1,filename_2):
    # Grab data from first file
    nc_1 = netCDF4.Dataset(filename_1)
    mjd_1 = nc_1.variables['mjd_slow']
    t_1 = (mjd_1[:]-mjd_1[0])*86400 # time in seconds
    fr_1 = nc_1.groups['fridge']
    t60k_1 = fr_1.variables['therm_temperature_0'][:]
    tpillk_1 = fr_1.variables['therm_temperature_1'][:]
    t4k_1 = fr_1.variables['therm_temperature_2'][:]
    
    # Grab data from second file
    nc_2 = netCDF4.Dataset(filename_2)
    mjd_2 = nc_2.variables['mjd_slow']
    t_2 = (mjd_2[:]-mjd_2[0])*86400 # time in seconds
    fr_2 = nc_2.groups['fridge']
    t60k_2 = fr_2.variables['therm_temperature_0'][:]
    tpillk_2 = fr_2.variables['therm_temperature_1'][:]
    t4k_2 = fr_2.variables['therm_temperature_2'][:]
    
    # Do the plot
    f = pyplot.figure()
    ax = f.add_subplot(111)
    ax.plot(t_1/3600,t4k_1,lw=2, label='4K Board 1')
    ax.plot(t_1/3600,tpillk_1,lw=2,label='ADR Magnet 1')
    ax.plot(t_1/3600,t60k_1,lw=2,label='60K Stage 1')
    ax.plot(t_2/3600,t4k_2,lw=2, label='4K Board 2')
    ax.plot(t_2/3600,tpillk_2,lw=2,label='ADR Magnet 2')
    ax.plot(t_2/3600,t60k_2,lw=2,label='60K Stage 2')
    ax.set_xlabel('Time (hours)')
    ax.set_ylabel('Temperature (K)')
    ax.set_title('Cooldown Curve Comparison')
    ax.legend(loc='lower right')
    ax.grid()
