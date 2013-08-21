# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 12:51:06 2013

@author: -
"""

import netCDF4
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

import date_tools
import datetime
import time
import os
import scipy.optimize

def svphi(x,a,b,c,d,e):
    return a + b*x + c*np.sin(d*x) + e*np.cos(d*x)
    
def vphiObj(p,x,y):
    return (np.abs(y-svphi(x,*p))**2).sum()
    
def axb(x,a,b):
    return a + b*x
    
def getStateAt(nc,mjd):
    mjds = nc.variables['mjd_slow'][:]
    idx = np.argmin(np.abs(mjd-mjds)) # index of time closest to desired mjd
    bbg = nc.groups['bolo_board']
    bb = dict([(str(x),bbg.variables[x][idx]) for x in bbg.variables.keys()])
    frg = nc.groups['fridge']
    fridge = dict([(str(x),frg.variables[x][idx]) for x in frg.variables.keys()])
    return bb,fridge
    
def stateString(bb,fridge):
    r = "SSA Bias: %.3f  SSA FB: %.3f  S2 Bias: %.3f  S2 FB: %.3f\nS1 Bias: %.3f  S1 FB: %.3f  RS: %d  Package temp: %.1f mK\n" % (
        bb['ssa_bias_voltage'], bb['ssa_fb_voltage'], bb['s2_bias_voltage'], bb['s2_fb_voltage'],
        bb['rs_voltage'], bb['s1_fb_voltage'], bb['rs_channel'], fridge['bridge_temp_value'] * 1000
        )
    return r
def plotAllVphi(ncname,plotdir = '/home/adclocal/tesdata/plots'):
    nc = netCDF4.Dataset(ncname)
    vphis = [str(x) for x in nc.groups.keys() if x.find('VPHI') >= 0]   # list of all vphi groups
    fits = {}
    if plotdir:
        figure = Figure
        figsize=(8,15)
    else:
        figure = plt.figure
        figsize=(8,6)
    for vphi in vphis:
        f = figure(figsize=figsize)
        ax = f.add_subplot(311)
        ax2 = f.add_subplot(312)
        ax3 = f.add_subplot(313)
        
        vphig = nc.groups[vphi]
        vphiv = vphig.variables
        mjd = vphig.mjd
        bb,fridge = getStateAt(nc,mjd)
        ut = time.mktime(date_tools.mjd_to_dt(mjd).timetuple())
        biases = vphiv['bias_points'][:]
        ax.set_color_cycle([plt.cm.gist_rainbow(x) for x in np.linspace(0,1,biases.shape[0])])
        fitarry = np.zeros((biases.shape[0],5)) # five fit parameters
        for n,bias in enumerate(biases):
            x = vphiv['PHI_%d' % n][:]
            y = vphiv['V_%d' % n][:]
            x0 = [y.mean(),  #initial offset
                  0.01, # initial slope
                  y.max()-y.min(), # initial sinusoid amplitude
                15, # approx right for s1
                0]
            frac = x.shape[0]/10 # remove 10% from either end for fitting

            p = scipy.optimize.fmin(vphiObj,x0=x0,args=(x[frac:-frac],y[frac:-frac]),xtol=1e-6,ftol=1e-6)
            fitarry[n,:] = p
#            p,cv = scipy.optimize.curve_fit(svphi,x,y,p0=[y.mean(),0,(y.max()-y.min()),6*np.pi/(x.max()-x.min()),0])
#            p,cv = scipy.optimize.curve_fit(axb,x,y,p0=[y.mean(),(y.max()-y.min())/(x.max()-x.min())])
            label = ('%.4f' % bias)
            l, = ax.plot(x, y, label=label, lw=1.5)
            ax2.plot(x,svphi(x,*p),lw=1.5,color=l.get_color(),label=label)
            ax3.plot(x,y - svphi(x,*p),lw=1.5,color=l.get_color(),label=label)
#            ax.plot(x,axb(x,*p),'--',color=l.get_color())
        fits[vphi] = fitarry
        stage_temp = fridge['bridge_temp_value']
        ax.legend(title='bias', prop=dict(size='x-small'))
        ax2.legend(title='bias', prop=dict(size='x-small'))
        ax3.legend(title='bias', prop=dict(size='x-small'))
        ax2.set_title('fits')
        ax3.set_title('residuals')
        ax.set_xlabel('FB Voltage')
        ax.set_ylabel('SSA Output Voltage')
        ax.grid(True)        

        ax.text(0.05,0.99,stateString(bb,fridge),fontdict=dict(size='small'),
               ha = 'left', va='top', transform=ax.transAxes, bbox=dict(facecolor='white',alpha=0.5,edgecolor='gray'))
        
        title = "%s\n%s : %s UTC\n%s" % (os.path.abspath(ncname),vphi, time.ctime(ut),vphig.log)
        f.suptitle(title,size='small')
        if plotdir:
            fname = os.path.join(plotdir,ncname + '_' + vphi + '.png')
            canvas = FigureCanvasAgg(f)
            canvas.print_figure(fname)
        
    nc.close()
    return fits