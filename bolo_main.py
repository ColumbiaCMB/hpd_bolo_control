#!/usr/bin/python

## @package bolo_main
# This Is the front end to the bolo software
# This is what sould be run

import sys
from bolo_main_gui import *
from bolo_board import *
from bolo_adc import *
from squids import *
from data_logging import *

## The main class function
class bolo_main():
    def __init__(self):
        self.bb = bolo_board()
        self.dl = data_logging()
        self.adc = bolo_adcCommunicator(data_logging=self.dl)
        self.sq = squids(bolo_board=self.bb,bolo_adc=self.adc,data_logging=self.dl)
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
        self.sq.setup_res_comp()

    def setup_logging(self):
        #This sets up a simple logging system
        #We attache the bolo_board registers to it
        self.dl.addRegisters("bolo_board",self.bb.registers)
        self.dl.addStream("sa",self.adc.sa_logging,"reg_5khz")
        self.dl.addStream("sa_ds",self.adc.sa_ds_logging,"reg_100hz")
        self.dl.addStream("fb",self.adc.fb_logging,"reg_5khz")
        self.dl.addStream("fb_ds",self.adc.fb_ds_logging,"reg_100hz")
        
    def launch_gui(self):
        self.app = QtGui.QApplication(sys.argv)
        #We setup all required gui's here but only
        #Show the main one
        self.gui = bolo_main_gui(self)
        self.bb_gui = bolo_board_gui(self.bb,self.gui)
        self.adc_gui = bolo_adc_gui(self.adc,self.gui)
        self.squid_gui = bolo_squids_gui(self.sq,self.gui)
        self.data_gui = data_logging_gui(self.dl,self.gui)

        self.gui.show()

if __name__ == "__main__":
    main_b = bolo_main()
    main_b.launch_gui()
    sys.exit(main_b.app.exec_())
