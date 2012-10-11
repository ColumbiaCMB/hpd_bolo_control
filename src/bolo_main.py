#!/usr/bin/python

## @package bolo_main
# This Is the front end to the bolo software
# This is what sould be run

import sys
from bolo_main_gui import *
from bolo_board import *
from bolo_adc import *
from squids import *
from fridge_gui import *
from data_logging import *
import pygcp.servers.sim900.sim900Client as sc
import IPython

## The main class function
class bolo_main():
    ## The init functoin
    def __init__(self):
        self.bb = bolo_board()
        self.dl = data_logging()
        self.adc = bolo_adcCommunicator(data_logging=self.dl)
        self.sq = squids(bolo_board=self.bb,bolo_adc=self.adc,data_logging=self.dl)
        self.sim900 = sc.sim900Client(hostname="192.168.1.152")
        self.default_setup()
        self.quick_setup()
        self.setup_logging()
        
    def default_setup(self):
        #We just start data logging - nothing else
        self.adc.comedi_reset() #reset any state
        self.adc.take_ls_data() #Take data for ever

    def quick_setup(self):
        #this is stuff we really want to do but doesn't
        #conform to the blank slate option
        self.bb.ssa_bias_ext_switch(False) 
        self.bb.set_pgain(5)
        self.bb.set_tconst(184)
        self.bb.pgain_switch(True)
        self.bb.tconst_switch(True)
        self.bb.short_int_switch(True)
        #self.sq.setup_res_comp()

    def setup_logging(self):
        #This sets up a simple logging system
        #We attache the bolo_board registers to it
        self.dl.addRegisters("bolo_board",self.bb.registers)
        self.dl.addStream("sa",self.adc.sa_logging,"reg_5khz",self.adc.netcdf_data_lock)
        self.dl.addStream("sa_ds",self.adc.sa_ds_logging,"reg_100hz",self.adc.netcdf_data_lock)
        self.dl.addStream("fb",self.adc.fb_logging,"reg_5khz",self.adc.netcdf_data_lock)
        self.dl.addStream("fb_ds",self.adc.fb_ds_logging,"reg_100hz",self.adc.netcdf_data_lock)
        
    def launch_gui(self):
        self.app = QtGui.QApplication(sys.argv)
        #We setup all required gui's here but only
        #Show the main one
        self.gui = bolo_main_gui(self)
        self.bb_gui = bolo_board_gui(self.bb,self.gui)
        self.adc_gui = bolo_adc_gui(self.adc,self.gui)
        self.squid_gui = bolo_squids_gui(self.sq,self.gui)
        self.data_gui = data_logging_gui(self.dl,self.gui)
        self.fridge_gui = fridge_gui(simclient=self.sim900, gui_parent=self.gui)

        self.gui.show()
        
    def set_defaults(self):
        self.adc_gui.Gain_cb.setCurrentIndex(0) # +/-10 V range
        self.adc_gui.Reset_Button.click() #commit
        
        self.bb_gui.ssa_bias_Input.setValue(1.2)
        self.bb_gui.s2_bias_Input.setValue(2.0)
        self.bb_gui.s1_bias_Input.setValue(0.8)
        self.bb_gui.rs_channel_Input.setValue(2)
        self.bb_gui.tes_bias_Input.setValue(-4.0)
        self.bb_gui.pgain_Input.setCurrentIndex(2) # pgain 15
        self.bb_gui.Ims_Input.setCurrentIndex(0) # igain 18.2
        self.bb_gui.setpoint_Input.setValue(0.0335)
        
        

if __name__ == "__main__":
    main_b = bolo_main()
    main_b.launch_gui()
    use_ipython = True
    if use_ipython:
        try:
            IPython.embed()
        except AttributeError:
            IPython.Shell.IPShellEmbed()()
    sys.exit()# main_b.app.exec_())
