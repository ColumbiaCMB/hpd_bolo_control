#!/usr/bin/python
import threading
from bolo_adc import *
from bolo_board import *
from scipy import interpolate
import collections
from squids_gui import *

class timestamp_match():
    def __init__(self):
        pass

    def setup_match(self,in_d,out_d):
        #First setup  the data
        self.f_int = interpolate.interp1d(in_d[:,0], in_d[:,1], bounds_error=False)
        int_values = self.f_int(out_d[:,0])


class squids():
    def __init__(self):
        self.adc_data = bolo_adcCommunicator(10000)
        self.sweep_thread = threading.Thread()
        self.bb = bolo_board()
        self.setup_board()

        self.x_cont = []
        self.y_cont = []
        self.VPhi_data_x = {}
        self.VPhi_data_y = {}

    def setup_board(self):
        self.bb.zero_voltages()

        self.bb.set_switch(3,2,False) #No external SA bias
        self.bb.set_switch(3,8,True) #Low Gain
        self.bb.set_switch(3,12,True) # Low T constant
        self.bb.set_switch(3,15,True) #short PI

        self.adc_data.comedi_reset() #reset any state
        self.adc_data.get_ls_data(0) #Take data for ever
        self.scope_data = collections.deque()

        self.setup_run()

    def setup_run(self):
        self.bb.ssa_bias_switch(True)
        #self.bb.set_voltage(3,1,3.6) #SSA BIAS
        #self.bb.set_voltage(2,2,0.05) #Offset
        #self.bb.set_switch(3,0,True) #SAFB (now input)
        #self.bb.set_switch(3,3,True) # FB
        #self.bb.set_switch(3,15,False) #short PI


    def ssa_VPhi_thread(self,fb_start,fb_stop,fb_step,ssa_start,ssa_stop,n_steps):
        self.sweep_thread = threading.Thread(target=self.ssa_VPhi,
                                             args = (fb_start,fb_stop,fb_step,ssa_start,ssa_stop,n_steps))
        self.sweep_thread.daemon = True
        self.sweep_thread.start()

    def ssa_VPhi(self,fb_start,fb_stop,fb_step,ssa_start,ssa_stop,n_steps):
        #We do a number of sweeps of the feedback at different bias voltages
        bias_steps = linspace(ssa_start,ssa_stop,n_steps)
        self.VPhi_data_x = {}
        self.VPhi_data_y = {}
        self.adc_data.start_data_logging(True) #start filling the data buffer
        for ssa_b in bias_steps:
            print ssa_b
            self.bb.ssa_bias_voltage(ssa_b)
            #start the sweep thread and poll for when done
            self.sweep("ssa_fb",fb_start,fb_stop,fb_step)
            self.VPhi_data_x[ssa_b] = self.x_cont
            self.VPhi_data_y[ssa_b] = self.y_cont
        
        self.adc_data.start_data_logging(False) #stop filling the data buffer

    def ssa_iv_thread(self,ssa_start,ssa_stop,ssa_step,count):
         self.sweep_thread = threading.Thread(target=self.ssa_iv,
                                             args = (ssa_start,ssa_stop,ssa_step,count))
         self.sweep_thread.daemon = True
         self.sweep_thread.start()

    def ssa_iv(self,ssa_start,ssa_stop,ssa_step,count):
        self.adc_data.start_data_logging(True) #start filling the data buffer
        self.sweep("ssa_bias",ssa_start,ssa_stop,ssa_step)
        self.adc_data.start_data_logging(False) #stop filling the data buffer

    def wrapper_sweep_thread(self,name,start,stop,step=0.001,count=1):
        self.sweep_thread = threading.Thread(target=self.sweep,
                                             args=(name,start,stop,step,count))
        self.sweep_thread.daemon = True
        self.sweep_thread.start()

    def sweep(self,name,start,stop,step=0.001,count=1):
       #Sweep is now a low level function - you NEED to turn on loggin elsewhere
        self.bb.wrapper_sweep_voltage(name,start,stop,step,count,False)
        
        self.x_cont = []
        self.y_cont = []
        self.s_ts_buffer = []
        self.s_v_buffer = [] 
        while self.bb.sweep_thread.isAlive():
            if len(self.adc_data.ls_ts_data) < 2 or len(self.bb.sweep_ts_data) < 2:
                time.sleep(0.1)
                continue
          
            #We have two buffers for the sweep data
            #This gives us more points to match but 
            #makes the code complicated

            self.bb.data_lock.acquire()
            self.s_ts_buffer.extend(self.bb.sweep_ts_data)
            self.s_v_buffer.extend(self.bb.sweep_v_data)
            self.bb.sweep_ts_data.clear()
            self.bb.sweep_v_data.clear()
            self.bb.data_lock.release()

            self.adc_data.adc_lock.acquire()
            temp_sa_data  = list(self.adc_data.ls_sa_data)
            temp_ts_data  = list(self.adc_data.ls_ts_data)
            self.adc_data.ls_sa_data.clear()
            self.adc_data.ls_ts_data.clear()
            self.adc_data.adc_lock.release()

            f_int = interpolate.interp1d(self.s_ts_buffer, self.s_v_buffer,bounds_error=False)
            x = f_int(temp_ts_data)
            y = array(temp_sa_data)

            ind = where(isfinite(x))
            ind_remain = where(self.s_ts_buffer > temp_ts_data[-1])[0]

            self.s_ts_buffer = array(self.s_ts_buffer)[ind_remain].tolist()
            self.s_v_buffer = array(self.s_v_buffer)[ind_remain].tolist()

            self.x_cont.extend(x[ind])
            self.y_cont.extend(y[ind])
            
    def __del__(self):
        del self.bb
        del self.adc_data

    def launch_gui(self):
        self.app = QtGui.QApplication(sys.argv)
        self.gui = bolo_squids_gui(self)
        self.gui.show()

if __name__ == "__main__":
    squids = squids()
    squids.launch_gui()
    sys.exit(squids.app.exec_())
