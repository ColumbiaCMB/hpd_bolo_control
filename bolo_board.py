#!/usr/bin/python
import sys
import threading
import comedi as cm
import gmpy
import collections
import mmap
import time
import datetime
from numpy import arange,linspace
import sqlite3 as lite
from bolo_board_gui import *
from date_tools import *

class bolo_board():
    def __init__(self,reload_state = False):
        self.subdev = 2
        self.fsync_chan = 2
        self.sclk_chan  = 1
        self.din_chan = 0
       
        #Set the dac pa mapping for the 3 dac
        #0b10000, 0b10001, 0b10010
        self.dac_pa = [2**4, (2**4 + 1), (2**4 + 2**1)]
        #Switches required to get the requested gain
        self.pgains = {}
        self.pgains[5] = [0]
        self.pgains[10] = [1]
        self.pgains[15] = [0,1]
        self.pgains[20] = [2]
        self.pgains[25] = [0,2]
        self.pgains[30] = [1,2]
        self.pgains[35] = [0,1,2]
        self.pgains[40] = [3]
        self.pgains[45] = [0,3]
        self.pgains[50] = [1,3]
        self.pgains[55] = [0,1,3]
        self.pgains[60] = [2,3]
        self.pgains[65] = [0,2,3]
        self.pgains[70] = [1,2,3]
        self.pgains[75] = [0,1,2,3]

        #Switches required for time constant
        self.tcon = {}
        self.tcon[184] = [4]
        self.tcon[94] = [5]
        self.tcon[62] = [4,5]
        self.tcon[47] = [6]
        self.tcon[37] = [4,6]
        self.tcon[31] = [5,6]
        self.tcon[27] = [4,5,6]

        #Set some common indexs [mux,switch]

        self.rs_32 = [2,0] #Extra RS
        self.s2_bias = [2,1]
        self.s2_fb = [2,2]
        self.htr_e = [2,3]
        self.htr = [2,4]
        self.tes_bias_external = [2,5]
        self.tes_bias = [2,6]
        self.ssa_fb = [3,0]
        self.ssa_bias = [3,1]
        self.ssa_bias_external = [3,2]
        self.s1_fb = [3,3]
        self.s1_fb_m = [3,4]
        self.short_int = [3,15]
        self.aux = [3,5]
        self.gains = [3,8]

        #And the voltages
        self.rs_v = [0,0]
        self.s2b_v = [0,1]
        self.s2fb_v = [0,2]
        self.htr_v = [0,3]
        self.tes_v = [1,0]
        self.s1fb_v = [1,1]
        self.ssafb_v = [2,0]
        self.ssab_v = [2,1]
        self.pid_v = [2,2]
        self.aux_v = [2,3]
        
        #Dummy dict to mape voltage to names:
        self.volt_lookup = {"ssa_bias" : self.ssab_v,
                          "ssa_fb" : self.ssafb_v,
                          "s2_bias" : self.s2b_v,
                          "s2_fb" : self.s2fb_v,
                          "rs_bias" : self.rs_v,
                          "s1_fb" : self.s1fb_v,
                          "tes_bis" : self.tes_v,
                          "heater" : self.htr_v,
                          "AUX" : self.aux_v}

        self.registers = {} #Dict to store common information
        self.con = lite.connect('bolo_board.db') #database for registers
        self.cur = self.con.cursor()

        self.data = 0
        #Just set switches to zero and then add to what is needed
        #We have four so just use array
        self.switch_state = [0,0,0,0]
        self.sweep_ts_data = collections.deque()
        self.sweep_v_data = collections.deque()
        self.sweep_progress = 0 

        self.cf = cm.comedi_open("/dev/comedi0")
        #Setup dio config
        cm.comedi_dio_config(self.cf,self.subdev,self.fsync_chan,cm.COMEDI_OUTPUT)
        cm.comedi_dio_config(self.cf,self.subdev,self.sclk_chan,cm.COMEDI_OUTPUT)
        cm.comedi_dio_config(self.cf,self.subdev,self.din_chan,cm.COMEDI_OUTPUT)

        #And set them all low
        cm.comedi_dio_write(self.cf,self.subdev,self.fsync_chan,0)
        cm.comedi_dio_write(self.cf,self.subdev,self.sclk_chan,0)
        cm.comedi_dio_write(self.cf,self.subdev,self.din_chan,0)
        self.data_lock = threading.Lock() 

        if reload_state is True:
            self.reload_db()

    def heater_switch(self,state):
        if state is True:
            self.set_switch(self.htr_e[0],self.htr_e[1],False)
            self.write_register("heater_ext_switch", False)
        self.set_switch(self.htr[0],self.htr[1],state)
        self.write_register("heater_switch",state)

    def heater_ext_switch(self,state):
        if state is True:
            self.set_switch(self.htr[0],self.htr[1],state)
            self.write_register("heater_switch",False)
        self.set_switch(self.htr_e[0],self.htr_e[1],state)
        self.write_register("heater_ext_switch",state)

    def s1_fb_switch(self,state):
        if state is True:
            self.set_switch(self.s1_fb_m[0],self.s1_fb_m[1],False)
            self.write_register("s1_fb_m_switch", False)
        self.set_switch(self.s1_fb[0],self.s1_fb[1],state)
        self.write_register("s1_fb_switch", state)

    def s1_fb_m_switch(self,state):
        if state is True:
            self.set_switch(self.s1_fb[0],self.s1_fb[1],False)
            self.write_register("s1_fb_switch", False)
        self.set_switch(self.s1_fb_m[0],self.s1_fb_m[1],state)
        self.write_register("s1_fb_m_switch", state)


    def tes_bias_switch(self,state):
        if state is True:
            self.set_switch(self.tes_bias_external[0],self.tes_bias_external[1],False)
            self.write_register("tes_bias_ext_switch", False)
        self.set_switch(self.tes_bias[0],self.tes_bias[1],state)
        self.write_register("tes_bias_switch", state)

    def tes_bias_ext_switch(self,state):
        if state is True:
            self.set_switch(self.tes_bias[0],self.tes_bias[1],state)
            self.write_register("tes_bias_switch",False)
        self.set_switch(self.tes_bias_external[0],self.tes_bias_external[1],state)
        self.write_register("tes_bias_ext_switch",state)

    def ssa_fb_switch(self,state):
        self.set_switch(self.ssa_fb[0],self.ssa_fb[1],state)
        self.write_register("ssa_fb_switch", state)

    def ssa_bias_switch(self,state):
        if state is True:
            self.set_switch(self.ssa_bias_external[0],self.ssa_bias_external[1],False)
            self.write_register("ssa_bias_ext_switch",False)
        self.set_switch(self.ssa_bias[0],self.ssa_bias[1],state)
        self.write_register("ssa_bias_switch",state)

    def ssa_bias_ext_switch(self,state):
        if state is True:
            self.set_switch(self.ssa_bias[0],self.ssa_bias[1],False)
            self.write_register("ssa_bias_switch",False)
        self.set_switch(self.ssa_bias_external[0],self.ssa_bias_external[1],state)
        self.write_register("ssa_bias_ext_switch", state)
        
    def s2_fb_switch(self,state):
        self.set_switch(self.s2_fb[0],self.s2_fb[1],state)
        self.write_register("s2_fb_switch", state)

    def s2_bias_switch(self,state):
        self.set_switch(self.s2_bias[0],self.s2_bias[1],state)
        self.write_register("s2_bias_switch", state)

    def short_int_switch(self,state):
        self.set_switch(self.short_int[0],self.short_int[1],state)
        self.write_register("short_int_switch", state)

    def aux_switch(self,state):
        self.set_switch(self.aux[0],self.aux[1],state)
        self.write_register("aux_switch", state)

    def turn_off_rs(self):
        #All Y0 and Y1 set to 0 plus self.rs_32
            self.switch_state[0] = 0 #0-15
            self.set_switch(0,0,False) #Set it
            self.switch_state[1] = 0 #16-31
            self.set_switch(1,0,False) #Set it
            self.set_switch(self.rs_32[0],self.rs_32[1],False)

    def s1_bias_switch(self,state):
        #RS channel should be stored in register
        if state is True:
            self.rs_channel(self.registers["rs_channel"])
        else:
            self.turn_off_rs()
        self.write_register("rs_switch", state)

    def rs_channel(self, channel):
        self.turn_off_rs()
        if channel <=15:
            self.set_switch(0,channel,True)
        if channel >15 and channel <=31:
            self.set_switch(1,(channel-16),True)
        if channel > 31:
            self.set_switch(self.rs_32[0],self.rs_32[1],True)

        self.write_register("rs_channel", channel)

    def zero_voltages(self):
       self.rs_voltage(0)
       self.s2_bias_voltage(0)
       self.s2_fb_voltage(0)
       self.htr_voltage(0)
       self.tes_voltage(0)
       self.s1_fb_voltage(0)
       self.ssa_bias_voltage(0)
       self.ssa_fb_voltage(0)
       self.pid_offset_voltage(0)
       self.aux_voltage(0)
       #and the extra two  that are not connected
       self.set_voltage(1,2,0)
       self.set_voltage(1,3,0)

    def rs_voltage(self,volts):
        self.set_voltage(self.rs_v[0],self.rs_v[1],volts)
        self.write_register("rs_voltage", volts)

    def s2_bias_voltage(self,volts):
        self.set_voltage(self.s2b_v[0], self.s2b_v[1],volts)
        self.write_register("s2_bias_voltage", volts)

    def s2_fb_voltage(self,volts):
        self.set_voltage(self.s2fb_v[0], self.s2fb_v[1],volts)
        self.write_register("s2_fb_voltage", volts)

    def htr_voltage(self,volts):
        self.set_voltage(self.htr_v[0], self.htr_v[1],volts)
        self.write_register("htr_voltage", volts)

    def tes_voltage(self,volts):
        self.set_voltage(self.tes_v[0], self.tes_v[1],volts)
        self.write_register("tes_voltage", volts)

    def s1_fb_voltage(self,volts):
        self.set_voltage(self.s1fb_v[0], self.s1fb_v[1],volts)
        self.write_register("s1_fb_voltage", volts)

    def ssa_bias_voltage(self,volts):
        self.set_voltage(self.ssab_v[0], self.ssab_v[1],volts)
        self.write_register("ssa_bias_voltage", volts)

    def ssa_fb_voltage(self,volts):
        self.set_voltage(self.ssafb_v[0], self.ssafb_v[1],volts)
        self.write_register("ssa_fb_voltage", volts)

    def pid_offset_voltage(self,volts):
        self.set_voltage(self.pid_v[0], self.pid_v[1],volts)
        self.write_register("pid_offset_voltage", volts)

    def aux_voltage(self,volts):
        self.set_voltage(self.aux_v[0], self.aux_v[1],volts)
        self.write_register("aux_voltage", volts)

    def turn_off_gain(self):
        for sw in xrange(4):
            self.set_switch(self.gains[0],(self.gains[1]+sw),False)

    def set_pgain(self,gain):
        self.turn_off_gain()
        if self.registers["pgain_switch"] is True:
            for sw in self.pgains[gain]:
                self.set_switch(self.gains[0],(self.gains[1]+sw),True)
        self.write_register("set_pgain", gain)

    def pgain_switch(self,state):
        self.write_register("pgain_switch", state)
        if state is True:
            self.set_pgain(self.registers["set_pgain"])
        else:
            self.turn_off_gain()

    def turn_off_tconst(self):
        for sw in xrange(4,7):
            self.set_switch(self.gains[0],(self.gains[1]+sw),False)

    def set_tconst(self,tconst):
        self.turn_off_tconst()
        if self.registers["tconst_switch"] is True:
            for sw in self.tcon[tconst]:
                self.set_switch(self.gains[0],(self.gains[1]+sw),True)
        self.write_register("set_tconst", tconst)

    def tconst_switch(self,state):
        self.write_register("tconst_switch", state)
        if state is True:
            self.set_tconst(self.registers["set_tconst"])
        else:
            self.turn_off_tconst()


    def set_voltage(self,mux,channel,volts):
        self.data = 1 #MSB need to be 1 to work
        self.data = (self.data << 2) + channel
        #Add the mux_pa
        self.data = (self.data << 5) + self.dac_pa[mux]
        #print "Mux Bits :", gmpy.digits(self.data,2).zfill(8)

        bit_value = int(((volts + 5)*(2**14))/10)
        #print "DAC Bits :", gmpy.digits(bit_value,2).zfill(16)

        self.data = (self.data << 16) + bit_value
        self.send_data(self.data)

    def wrapper_sweep_voltage(self,name,start,stop,step,count=1,loop=False):
        #This is just a wrapper that takes a name rather than
        #A mux and channel - useful for GUI etc

        self.sweep_thread = threading.Thread(target=self.sweep_voltage, 
                                             args=(self.volt_lookup[name][0], 
                                                   self.volt_lookup[name][1], 
                                                   start, stop, step, count, loop))
        self.sweep_thread.start()

    def sweep_voltage(self,mux,channel,start,stop,step,count=1,loop=False):
        #Do the really really dumb thing
        #We record the value and the timestamp for matching
        #Calculate number of steps etc

        self.data_lock.acquire()
        self.sweep_ts_data.clear()
        self.sweep_v_data.clear()
        self.data_lock.release()
        
        nsteps = len(arange(start,stop,step))*count
        if loop is True:
            nsteps = nsteps*2

        self.sweep_progress = 0 
        sweep_step = 100.0/nsteps

        for i in xrange(count):
            for v in arange(start,stop,step):
                self.set_voltage(mux,channel,v)
                self.data_lock.acquire()
                self.sweep_ts_data.append(mjdnow())
                self.sweep_v_data.append(v)
                self.data_lock.release()
                self.sweep_progress = self.sweep_progress + sweep_step
                time.sleep(0.001)
            if loop is True:
                for v in arange(stop,start,-step):
                    self.set_voltage(mux,channel,v)
                    self.data_lock.acquire()
                    self.sweep_ts_data.append(mjdnow())
                    self.sweep_v_data.append(v)
                    self.data_lock.release()
                    self.sweep_progress = self.sweep_progress + sweep_step
                    time.sleep(0.001)
        
        self.sweep_progress = -1 #For GUI 

    def set_switch(self,mux,switch_number,state):
        print "Mux Bits :", gmpy.digits(mux,2).zfill(8)
       #need to bit shift that 16 bits to right
        self.data = mux << 16
       #Now just set the singular switch
       #We add it's relevent bit value to the state
       #First check if it's already set
        is_set = (self.switch_state[mux] & (1<<switch_number)) >> switch_number
        if state is False and is_set == 1:
            self.switch_state[mux] = self.switch_state[mux] - (1<<switch_number)
        if state is True and is_set == 0:
            self.switch_state[mux] = self.switch_state[mux] + (1<<switch_number)
        
        print "Switch Bits :", gmpy.digits(self.switch_state[mux],2).zfill(16)

        #And add this to the data
        self.data = self.data + self.switch_state[mux]
        self.send_data(self.data)

    def send_data(self,data):
        #So first make sure that sclk and fsync are low
        cm.comedi_dio_write(self.cf,self.subdev,self.fsync_chan,0)
        cm.comedi_dio_write(self.cf,self.subdev,self.sclk_chan,0)
        #print "Sending Bits :", gmpy.digits(self.data,2).zfill(24)

        #Then set bit and clock it by taking sclk from low to high to low
        #This seems like a waste of one instruction but the DAC reads
        #data on the falling edge, the switch on the rising edge
        #Should write two functions really

        for i in arange(23,-1,-1):
            dbit = ((data >> i) & 0x01)
            cm.comedi_dio_write(self.cf,self.subdev,self.din_chan,int(dbit))
            cm.comedi_dio_write(self.cf,self.subdev,self.sclk_chan,0)
            cm.comedi_dio_write(self.cf,self.subdev,self.sclk_chan,1)
            cm.comedi_dio_write(self.cf,self.subdev,self.sclk_chan,0)

        #And set Fsync high to set the switch then low
        # Also make sure clk is low too
        cm.comedi_dio_write(self.cf,self.subdev,self.sclk_chan,0)
        cm.comedi_dio_write(self.cf,self.subdev,self.fsync_chan,1)
        cm.comedi_dio_write(self.cf,self.subdev,self.fsync_chan,0)

    def launch_gui(self):
        self.app = QtGui.QApplication(sys.argv)
        self.gui = bolo_board_gui(self)
        self.gui.show()

    def write_register(self,name,value):
        self.registers[name] = value
        #self.cur.execute("INSERT OR REPLACE INTO Registers VALUES (null,?,?)", (name,value))
        #self.con.commit()

    def setup_db(self):
            self.cur.execute("DROP TABLE IF EXISTS Registers")
            self.cur.execute("CREATE TABLE Registers(ID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT UNIQUE, Value NUMERIC)")
            self.con.commit()

    def reload_db(self):
        #Register name is the command so life should be easy!
        self.cur.execute("SELECT * FROM Registers")
        cmd = ""
        for row in self.cur:
            cmd = cmd + "self.%s(%i);" % (row[1],row[2])
        exec cmd

if __name__ == "__main__":
    b_board = bolo_board()
    b_board.launch_gui()
    sys.exit(b_board.app.exec_())
