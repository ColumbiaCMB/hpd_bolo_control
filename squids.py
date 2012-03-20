import threading
from bolo_adc import *
from bolo_board import *
from scipy import interpolate
import collections
#import dualscope

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
        self.bb = bolo_board()
        self.setup_board()

    def setup_board(self):
        self.bb.set_voltage(2,1,0) #SSA BIAS
        self.bb.set_voltage(2,0,0) #SSA BIAS

        self.bb.set_switch(3,2,False) #No external SA bias
        self.bb.set_switch(3,8,True) #Low Gain
        self.bb.set_switch(3,12,True) # Low T constant
        self.bb.set_switch(3,15,True) #short PI
        self.bb.set_switch(3,0,True) #SA FB
        self.bb.sa_bias_switch(True)
        self.bb.set_switch(2,1,True) #S2 Bias

        self.adc_data.comedi_reset() #reset any state
        self.adc_data.get_ls_data(0) #Take data for ever
        self.scope_data = collections.deque()

    def sweep(self,mux,channel,start,stop):
        #This takes data for the Series Array IV
        self.adc_data.start_data_logging(True) #start filling the data buffer
        #Setup a thread to do the sweep
        sweep_thread = threading.Thread(target=self.bb.sweep_voltage,
                                        args=(mux,channel,start,stop,0.001,1))
        sweep_thread.start()
        
        self.timestamp = []
        self.ssa_in = []
        self.ssa_out = []
        while sweep_thread.isAlive():
            if len(self.adc_data.ls_data) == 0 or len(self.bb.sweep_data) == 0:
                time.sleep(0.1)
                continue
            #self.adc_data.adc_lock.acquire()
            #temp_data = array(self.adc_data.ls_data)
            #self.adc_data.ls_data.clear()
            #self.adc_data.adc_lock.release()
        
            #Ok for simplicity - Do something slow and dumb
            #To create the data array of [timestamp,ssa_in,ssa_out]
            #This is not conducive to memory usage or CPU but we create
            #A lookup table of all the data all the time - quite dumb
            #self.bb.data_lock.acquire()
            #temp_sweep = array(self.bb.sweep_data)
            #self.bb.data_lock.release()
            #self.f_int = interpolate.interp1d(temp_sweep[:,0], temp_sweep[:,1], bounds_error=False)
            #time.sleep(0.1)
        
        stop_timer = self.adc_data.start_data_logging(False) #start filling the data buffer
        stop_timer.join()
        data = array(self.adc_data.ls_data)
        sdata = array(self.bb.sweep_data)
        f_int = interpolate.interp1d(sdata[:,0], sdata[:,1], bounds_error=False)
        self.x = f_int(data[:,0])
        self.y = data[:,1]

    def __del__(self):
        del self.bb
        del self.adc_data
