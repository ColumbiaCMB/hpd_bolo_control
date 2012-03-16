import threading
import comedi as cm
import gmpy
import collections
import mmap
import time
import datetime
from numpy import arange,linspace
from date_tools import *

class bolo_board():
    def __init__(self):
        self.subdev = 2
        self.fsync_chan = 2
        self.sclk_chan  = 1
        self.din_chan = 0
       
        #Set the dac pa mapping for the 3 dac
        #0b10000, 0b10001, 0b10010
        self.dac_pa = [2**4, (2**4 + 1), (2**4 + 2**1)]
      
        #Set some common indexs [mux,switch]
        self.sa_fb = [3,0]
        self.sa_bias = [3,1]
        self.sa_bias_external = [3,2]
        self.s1_fb = [3,3]
        self.s1_fb_m = [3,4]
        self.aux = [3,5]

        self.data = 0
        #Just set switches to zero and then add to what is needed
        #We have four so just use array
        self.switch_state = [0,0,0,0]
        self.sweep_data = collections.deque()

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

    def sa_fb_switch(self,state):
        self.set_switch(self.sa_fb[0],self.sa_fb[1],state)

    def sa_bias_switch(self,state):
        self.set_switch(self.sa_bias[0],self.sa_bias[1],state)

    def sa_bias_ext_switch(self,state):
        self.set_switch(self.sa_bias_external[0],self.sa_bias_external[1],state)

    def s1_fb_switch(self,state):
        self.set_switch(self.s1_fb[0],self.s1_fb[1],state)

    def s1_fb_m_switch(self,state):
        self.set_switch(self.s1_fb_m[0],self.s1_fb_m[1],state)

    def aux_switch(self,state):
        self.set_switch(self.aux[0],self.aux[1],state)

    def zero_voltages(self):
        for i in xrange(3):
            for j in xrange(4):
                self.set_voltage(i,j,0)

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

    def sweep_voltage(self,mux,channel,start,stop,step,count=1,loop=False):
        #Do the really really dumb thing
        #We record the value and the timestamp for matching

        self.data_lock.acquire()
        self.sweep_data.clear()
        self.data_lock.release()
        
        for i in xrange(count):
            for v in arange(start,stop,step):
                self.set_voltage(mux,channel,v)
                self.data_lock.acquire()
                self.sweep_data.append([mjdnow(),v])
                self.data_lock.release()
                time.sleep(0.001)
                #time.sleep(0.05)
            if loop is True:
                for v in arange(stop,start,-step):
                    self.set_voltage(mux,channel,v)
                    self.data_lock.acquire()
                    self.sweep_data.append([mjdnow(),v])
                    self.data_lock.release()
                    time.sleep(0.001)

    def set_switch(self,mux,switch_number,state):
        #print "Mux Bits :", gmpy.digits(mux,2).zfill(8)
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

 
