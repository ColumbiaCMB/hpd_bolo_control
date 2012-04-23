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
        self.bb = bolo_board()
        self.setup_board()

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


    def wrapper_sweep_thread(self,name,start,stop,step=0.001,count=1,continuous=False):
        self.sweep_thread = threading.Thread(target=self.sweep,
                                             args=(name,start,stop,step,count,continuous))
        self.sweep_thread.start()

    def sweep(self,name,start,stop,step=0.001,count=1,continuous=False):
        #This takes data for the Series Array IV
        self.adc_data.start_data_logging(True) #start filling the data buffer
        #Setup a thread to do the sweep
        self.bb.wrapper_sweep_voltage(name,start,stop,step,count,False)
        
        self.x_cont = []
        self.y_cont = []
        self.s_ts_buffer = []
        self.s_v_buffer = [] 
        while self.bb.sweep_thread.isAlive():
            if len(self.adc_data.ls_ts_data) == 0 or len(self.bb.sweep_ts_data) == 0:
                time.sleep(0.1)
                continue
            if continuous is True:
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
            
        
        
        stop_timer = self.adc_data.start_data_logging(False)
        stop_timer.join()
        f_int = interpolate.interp1d(list(self.bb.sweep_ts_data), 
                                     list(self.bb.sweep_v_data),
                                     bounds_error=False)
        x = f_int(self.adc_data.ls_ts_data)
        y = array(self.adc_data.ls_sa_data)
        #And  get rid of nans from the fitting
        ind = where(isfinite(x))[0]        
        self.x_cont = x[ind]
        self.y_cont = y[ind]

    def __del__(self):
        del self.bb
        del self.adc_data

    def launch_gui(self):
        self.app = QtGui.QApplication(sys.argv)
        self.gui = bolo_squids_gui(self)
        self.gui.show()
