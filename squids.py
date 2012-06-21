#!/usr/bin/python
import threading
from bolo_adc import *
from bolo_board import *
from scipy import interpolate
import collections
from squids_gui import *
from bolo_board_gui import *
import pid
from numpy import mean
from resistance_comp import *
from date_tools import *

class squids():
    def __init__(self,bolo_board=None,
                 bolo_adc=None,
                 data_logging=None):
        if bolo_adc is None:
            self.adc_data = bolo_adcCommunicator()
        else:
            self.adc_data = bolo_adc

        if bolo_board is None:
            self.bb = bolo_board()
        else:
            self.bb = bolo_board
        
        self.dlog = data_logging
        self.setup_res_comp()
        self.sweep_thread = threading.Thread()

        self.pid = pid.PID()
        self.pid_event = threading.Event()

        self.x_cont = []
        self.y_cont = []
        self.mjd_cont = []
        self.s2_data_x = []
        self.s2_data_y = []
        self.VPhi_data_x = {}
        self.VPhi_data_y = {}

    def setup_res_comp(self,wire_res=None):
        if wire_res is None:
            self.res_compensator = resistance_compensator(self.bb)
        else:
            self.res_compensator = resistance_compensator(self.bb,wire_res)

    ## This controlls the feedback on the SSA fb
    # channel for tuning second and first stage squids
    # @param self The object pointer
    # @param setpoint Where we want to lock at
    # @param state turn on and off
    def SSA_feedback(self, setpoint,P=0.01,I=0,D=0):
        self.pid.setKp(P)
        self.pid.setKi(I)
        self.pid.setKd(D)
        self.pid.setOffset(self.bb.registers["ssa_fb_voltage"])
        self.pid.setPoint(setpoint)
        while not self.pid_event.isSet():
            #We use SA_ds as measure
            corrected_V = self.res_compensator.correct_voltage(self.adc_data.sa[-1])
            pid_out = self.pid.update(corrected_V)
            new_voltage = pid_out
            self.bb.ssa_fb_voltage(new_voltage)
            time.sleep(0.001)

    def ssa_feedback_thread(self,setpoint,P=0.01,I=0.0,D=0):
        self.feedback_thread = threading.Thread(target=self.SSA_feedback,
                                                args = (setpoint,P,I,D))
                                               
        self.feedback_thread.daemon = True
        self.pid_event.clear()
        self.feedback_thread.start()

    def s2_bias_test_thread(self,fb_start,fb_stop,fb_step):
        self.sweep_thread = threading.Thread(target=self.s2_bias_test,
                                             args = (fb_start,fb_stop,fb_step))
        self.sweep_thread.daemon = True
        self.sweep_thread.start()

    def s2_bias_test(self,fb_start,fb_stop,fb_step):
        #Quick and dirty test of doing a sweep on the S2_stage Using feedback
        #Assumes feedback is running
        self.s2_data_x = []
        self.s2_data_y = []

        #So we set a sweep point and go from there - Can not handle quick changes
        bias_steps = arange(fb_start,fb_stop,fb_step)
        for fb_s in bias_steps:
            print fb_s
            #first set the position
            self.bb.s2_bias_voltage(fb_s)
            time.sleep(0.1)
            #And we now wait until the error is zero
            while(self.pid.getError() > 0.001):
                time.sleep(0.01)

            #Ok should be where we want - now record
            self.s2_data_x.append(fb_s)
            self.s2_data_y.append(self.bb.registers["ssa_fb_voltage"])
        

    def ssa_VPhi_thread(self,fb_start,fb_stop,fb_step,ssa_start,ssa_stop,n_steps):
        self.sweep_thread = threading.Thread(target=self.ssa_VPhi,
                                             args = (fb_start,fb_stop,fb_step,ssa_start,ssa_stop,n_steps))
        self.sweep_thread.daemon = True
        self.sweep_thread.start()

    def ssa_VPhi(self,fb_start,fb_stop,fb_step,start,stop,n_steps):
        #We do a number of sweeps of the feedback at different bias voltages
        bias_steps = linspace(start,stop,n_steps)
        self.VPhi_data_x = {}
        self.VPhi_data_y = {}
        self.adc_data.start_data_logging(True) #start filling the data buffer
        for b in bias_steps:
            self.bb.ssa_bias_voltage(b)
            self.sweep("ssa_fb",fb_start,fb_stop,fb_step)
            print "ROOOOOS", len(self.x_cont)
            self.VPhi_data_x[b] = self.x_cont
            self.VPhi_data_y[b] = self.y_cont
        
        self.adc_data.start_data_logging(False) #stop filling the data buffer

    def s2_VPhi_thread(self,fb_start,fb_stop,fb_step,start,stop,n_steps):
        self.sweep_thread = threading.Thread(target=self.s2_VPhi,
                                             args = (fb_start,fb_stop,fb_step,start,stop,n_steps))
        self.sweep_thread.daemon = True
        self.sweep_thread.start()

    def s2_VPhi(self,fb_start,fb_stop,fb_step,start,stop,n_steps):
        #We do a number of sweeps of the feedback at different bias voltages
        bias_steps = linspace(start,stop,n_steps)
        self.VPhi_data_x = {}
        self.VPhi_data_y = {}
        self.adc_data.start_data_logging(True) #start filling the data buffer
        for b in bias_steps:
            self.bb.s2_bias_voltage(b)
            self.sweep("s2_fb",fb_start,fb_stop,fb_step)
            self.VPhi_data_x[b] = self.x_cont
            self.VPhi_data_y[b] = self.y_cont
        
        self.adc_data.start_data_logging(False) #stop filling the data buffer

    def s1_VPhi_thread(self,fb_start,fb_stop,fb_step,start,stop,n_steps):
        self.sweep_thread = threading.Thread(target=self.s1_VPhi,
                                             args = (fb_start,fb_stop,fb_step,start,stop,n_steps))
        self.sweep_thread.daemon = True
        self.sweep_thread.start()

    def s1_VPhi(self,fb_start,fb_stop,fb_step,start,stop,n_steps):
        #We do a number of sweeps of the feedback at different bias voltages
        bias_steps = linspace(start,stop,n_steps)
        self.VPhi_data_x = {}
        self.VPhi_data_y = {}
        self.adc_data.start_data_logging(True) #start filling the data buffer
        for b in bias_steps:
            self.bb.rs_voltage(b)
            self.sweep("s1_fb",fb_start,fb_stop,fb_step)
            self.VPhi_data_x[b] = self.x_cont
            self.VPhi_data_y[b] = self.y_cont
        
        self.adc_data.start_data_logging(False) #stop filling the data buffer
        
    def ssa_iv_thread(self,ssa_start,ssa_stop,ssa_step,count):
         self.sweep_thread = threading.Thread(target=self.ssa_iv,
                                             args = (ssa_start,ssa_stop,ssa_step,count))
         self.sweep_thread.daemon = True
         self.sweep_thread.start()

    def ssa_iv(self,ssa_start,ssa_stop,ssa_step,count=1):
        self.adc_data.start_data_logging(True) #start filling the data buffer
        self.sweep("ssa_bias",ssa_start,ssa_stop,ssa_step,count)
        self.adc_data.start_data_logging(False) #stop filling the data buffer

    def s2_iv_thread(self,ssa_start,ssa_stop,ssa_step,count):
         self.sweep_thread = threading.Thread(target=self.s2_iv,
                                             args = (ssa_start,ssa_stop,ssa_step,count))
         self.sweep_thread.daemon = True
         self.sweep_thread.start()

    def s2_iv(self,ssa_start,ssa_stop,ssa_step,count=1):
        self.adc_data.start_data_logging(True) #start filling the data buffer
        self.sweep("s2_bias",ssa_start,ssa_stop,ssa_step,count)
        self.adc_data.start_data_logging(False) #stop filling the data buffer
        
    def s1_iv_thread(self,ssa_start,ssa_stop,ssa_step,count):
         self.sweep_thread = threading.Thread(target=self.s1_iv,
                                             args = (ssa_start,ssa_stop,ssa_step,count))
         self.sweep_thread.daemon = True
         self.sweep_thread.start()

    def s1_iv(self,ssa_start,ssa_stop,ssa_step,count=1):
        self.adc_data.start_data_logging(True) #start filling the data buffer
        self.sweep("s1_bias",ssa_start,ssa_stop,ssa_step,count)
        self.adc_data.start_data_logging(False) #stop filling the data buffer
    
        
    def wrapper_sweep_thread(self,name,start,stop,count):
        self.sweep_thread = threading.Thread(target=self.sweep,
                                             args=(name,start,stop,step,count))
        self.sweep_thread.daemon = True
        self.sweep_thread.start()

    def sweep(self,name,start,stop,step,count=1):
       #Sweep is now a low level function - you NEED to turn on loggin elsewhere
        self.bb.wrapper_sweep_voltage(name,start,stop,step,count)
        self.x_cont = []
        self.y_cont = []
        self.mjd_cont = []
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
            ts = array(temp_ts_data)

            ind = where(isfinite(x))
            ind_remain = where(self.s_ts_buffer > temp_ts_data[-1])[0]

            self.s_ts_buffer = array(self.s_ts_buffer)[ind_remain].tolist()
            self.s_v_buffer = array(self.s_v_buffer)[ind_remain].tolist()

            #And here we do the resistance compensation for sweeping the squids
            v_corrected = self.res_compensator.correct_batch_voltage(x[ind],y[ind],name)
            #v_corrected = y[ind]

            self.x_cont.extend(x[ind])
            self.y_cont.extend(v_corrected)
            self.mjd_cont.extend(ts[ind])

    def write_IV_data(self,name,meta):
        if self.dlog is not None:
            if self.dlog.file_name is not None:
                self.dlog.add_IV_data(self.x_cont, self.y_cont, self.mjd_cont,meta,name)

    def write_VPHI_data(self,name,meta):
        #fudge mjd_cont
        mjd = mjdnow()
        if self.dlog is not None:
            if self.dlog.file_name is not None:
                self.dlog.add_VPHI_data(self.VPhi_data_x, 
                                        self.VPhi_data_y,
                                        mjd,meta,name)

    def __del__(self):
        del self.bb
        del self.adc_data

    def launch_gui(self):
        self.app = QtGui.QApplication(sys.argv)
        self.gui = bolo_squids_gui(self)
        self.gui.show()

    def launch_all_gui(self):
        self.app = QtGui.QApplication(sys.argv)
        self.gui = bolo_squids_gui(self)
        self.bb_gui = bolo_board_gui(self.bb,self.gui)
        self.adc_gui = bolo_adc_gui(self.adc_data,self.gui)
        self.gui.show()
        self.bb_gui.show()
        self.adc_gui.show()

if __name__ == "__main__":
    squids = squids()
    squids.launch_all_gui()
    sys.exit(squids.app.exec_())
