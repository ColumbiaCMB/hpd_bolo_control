#!/usr/bin/python
import sys
import threading
import collections
import time,mmap,struct
import datetime
import logging
import comedi as c
from numpy import *
from bolo_filtering import *
from date_tools import *
from pylab import mlab
from bolo_adc_gui import *

logging.basicConfig()

class bolo_adcCommunicator():
    def __init__(self,max_buffer=10000,
                 data_logging=None):
        self.logger = logging.getLogger('bolo_adc')
        self.logger.setLevel(logging.DEBUG)
        self.max_buffer = max_buffer
        self.dlog = data_logging

        self.fb = collections.deque(maxlen=max_buffer) #ls_freq buffer
        self.fb_nofilt = collections.deque(maxlen=max_buffer) #ls_freq buffer with no filterting
        self.fb_uf = collections.deque()#hs_freq buffer
        self.fb_temp = collections.deque(maxlen=max_buffer) #For FIR filtering
        self.fb_ds =  collections.deque(maxlen=max_buffer)#downsample_buffer

        self.fb_logging = collections.deque(maxlen=max_buffer) #Buffer for 5khz data logging
        self.fb_ds_logging = collections.deque(maxlen=max_buffer) #Buffer 100 hz data logging

        self.sa  = collections.deque(maxlen=max_buffer)
        self.sa_nofilt = collections.deque(maxlen=max_buffer) #ls_freq buffer with no filterting
        self.sa_uf = collections.deque()
        self.sa_temp = collections.deque(maxlen=max_buffer) #For FIR filtering
        self.sa_ds =  collections.deque(maxlen=max_buffer)

        self.sa_logging = collections.deque(maxlen=max_buffer) #Buffer for 5khz data logging
        self.sa_ds_logging = collections.deque(maxlen=max_buffer) #Buffer 100 hz data logging

        self.ls_sa_data = collections.deque() #Internal logging buffer for sa
        self.ls_fb_data = collections.deque() #Internal logging buffer for fb
        self.ls_ts_data = collections.deque() #Internal logging buffer for ts

        self.mjd_logging = collections.deque(maxlen=max_buffer) #Buffer for 5khz data logging
        self.mjd_ds_logging = collections.deque(maxlen=max_buffer) #Buffer 100 hz data logging

        self.timestamps = collections.deque(maxlen=max_buffer)
        self.ts_temp = collections.deque(maxlen=max_buffer)
        self.ts_ds =  collections.deque(maxlen=max_buffer)

        self.fourier_freq_fb = []
        self.fourier_freq_fb_ds = []
        self.fourier_freq_sa = []
        self.fourier_freq_sa_ds = []
        self.fourier_sa =[]
        self.fourier_fb = []
        self.fourier_sa_ds = []
        self.fourier_fb_ds = []

        self.log_timer = threading.Thread()
        self.filter_thread = threading.Thread()
        self.collector_thread = threading.Thread()

        self.stop_event = threading.Event()
        self.filter_event = threading.Event()
        self.cdf_log_event = threading.Event()

        self.filter_lock = threading.Lock()
        self.data_lock = threading.Lock() #Used for poping data to client
        self.adc_lock = threading.Lock() #Used for poping data to client
        self.netcdf_data_lock = threading.Lock() #Used to lock data for writing to disk

        self.registers = {}

        self.cmdtest_messages = [
            "success",
            "invalid source",
            "source conflict",
            "invalid argument",
            "argument conflict",
            "invalid chanlist"]
        
        self.gain_lookup = {0 : 10, 1 : 5, 2 : 2, 3 : 1, 4 : 0.5, 5: 0.2, 6 : 0.1}

        self.fb_chan = 0
        self.sa_chan = 1
        self.fb_uf_chan = 2
        self.sa_uf_chan = 3

        self.adc_gain = 4

        self.ls_freq = 5000 #Low speed data taking frequency
        self.hs_freq = 312500 #High speed data taking frequency
        
        self.chunk_power = 12 #filter chunk size
        self.ntaps = 1001
        self.cutoff_freq = 35
        self.downsample_freq = 100
        self.ls_progress = 0

        self.setup_filtering()

        self.collect_data_flag = False
        self.speed_flag = None
        self.setup_adc()

    def reset_ls_data(self):
        self.comedi_reset()
        self.take_ls_data()

    def setup_filtering(self):
        deci = self.ls_freq/self.downsample_freq
        self.true_ds_freq = float(self.ls_freq)/float(deci)
        if self.ls_freq % self.downsample_freq != 0:
            temp_str = "Actual downsample freq is %f" % self.true_ds_freq
            self.logger.warn(temp_str)

        self.sa_filt = bolo_filtering(ntaps=self.ntaps,
                                      cutoff_hz=self.cutoff_freq,
                                       sample_rate=self.ls_freq,
                                      decimate = deci) 

        self.fb_filt = bolo_filtering(ntaps=self.ntaps,
                                      cutoff_hz=self.cutoff_freq,
                                      sample_rate=self.ls_freq,
                                      decimate = deci) 

        self.ts_filt = bolo_filtering(ntaps=self.ntaps,
                                      cutoff_hz=self.cutoff_freq,
                                      sample_rate=self.ls_freq,
                                      decimate = deci) 

    def setup_adc(self):
        self.subdevice=0 #Always the case here
        self.dev = c.comedi_open('/dev/comedi0')
        if not self.dev: 
            self.logger.error("Error openning Comedi device")
            return -1
        
        self.file_device = c.comedi_fileno(self.dev)
        if not self.file_device:
            self.logger.error("Error obtaining Comedi device file descriptor")
            return -1

        self.buffer_size = c.comedi_get_buffer_size(self.dev, self.subdevice)
        temp_msg = "Debug size: %i" % self.buffer_size
        self.logger.info(temp_msg)
        self.map = mmap.mmap(self.file_device,self.buffer_size,mmap.MAP_SHARED, mmap.PROT_READ)

    def start_data_logging(self,state):
        #Tell the code that you want some data
        #This is for doing IVs VPhi etc and is Internal
        #It is NOT for logging data to a file
        #First clear the buffer
        if state is True:
            #self.data_lock.acquire()
            self.ls_sa_data.clear()
            self.ls_fb_data.clear()
            self.ls_ts_data.clear()
            #self.data_lock.release()
            self.collect_data_flag = True
        else:
            #because of various delays in the system
            #We need extend the data logging time by a couple
            #of seconds
            stop_timer = threading.Timer(2.0,self.stop_data_logging)
            stop_timer.start()
            return stop_timer

    def stop_data_logging(self):
            self.collect_data_flag = False

    def reset_queues(self):
        #filter_lock is probably not correct here
        self.filter_lock.acquire()
        self.fb.clear()
        self.fb_nofilt.clear()
        self.fb_uf.clear()
        self.fb_temp.clear()
        self.fb_ds.clear()

        self.sa.clear()
        self.sa_nofilt.clear()
        self.sa_uf.clear()
        self.sa_temp.clear()
        self.sa_ds.clear()

        self.timestamps.clear()
        self.ts_temp.clear()
        self.ts_ds.clear()

        self.fb_logging.clear()
        self.fb_ds_logging.clear()
        self.sa_logging.clear()
        self.sa_ds_logging.clear()
        self.mjd_logging.clear()
        self.mjd_ds_logging.clear()

        self.filter_lock.release()

        #self.data_lock.acquire()
        self.ls_sa_data.clear()
        self.ls_fb_data.clear()
        self.ls_ts_data.clear()

        #self.data_lock.release()


    def take_ls_data(self):
        #This is a wrapper to setup for lowspeed data taking
        #It takes (not logs) data continously
        self.reset_queues()
        #We may as well get all four channels here
        channels = [self.fb_chan, self.sa_chan, self.fb_uf_chan, self.sa_uf_chan]
        gains = [self.adc_gain, self.adc_gain,self.adc_gain, self.adc_gain]
        refs = [c.AREF_DIFF, c.AREF_DIFF,c.AREF_DIFF, c.AREF_DIFF]
        self.speed_flag = "ls"
        self.get_data(channels,gains,refs,self.ls_freq,0)

    def log_ls_data_start(self,period,meta=None,suffix=None):
        #This function records data to the netcfg file 
        #the way to do this is via setting a flag in the 
        #data logger and then adding a timer.
        #We also reset the logging deque
        self.fb_logging.clear()
        self.fb_ds_logging.clear()
        self.sa_logging.clear()
        self.sa_ds_logging.clear()
        self.mjd_logging.clear()
        self.mjd_ds_logging.clear()
        
        self.dlog.record_ls_data(True,meta,suffix)
        #We have a thread to simply update the process and check
        #when the timer runs out - should be acurate to about a second
        self.log_ls_data_start_time = datetime.datetime.utcnow()
        self.ls_period = period #Use as check for percentage plot

        self.log_ls_data_stop_time = self.log_ls_data_start_time + datetime.timedelta(seconds=period)
        self.log_timer = threading.Thread(target=self.log_ls_thread)
        self.log_timer.start()

    def log_ls_thread(self):
        time_now = datetime.datetime.utcnow()
        dt = time_now - self.log_ls_data_start_time
        self.cdf_log_event.clear()
        while (dt.seconds < self.ls_period) and not self.cdf_log_event.isSet():
            self.ls_progress = (dt.seconds + dt.microseconds*1.0e-6)*100.0/self.ls_period
            time_now = datetime.datetime.utcnow()
            dt = time_now - self.log_ls_data_start_time
            time.sleep(0.5)
        self.ls_progress = 100
        self.dlog.record_ls_data(False)

    def cancel_logging(self):
        self.cdf_log_event.set()

    def get_hs_data(self,period,meta=None):
        if period > 60:
            self.logger.error("Will not take more than 60 seconds of data at 312.5khz")
            return -1
        self.hs_meta = meta #Used when logging later no
        channels = [self.fb_uf_chan, self.sa_uf_chan]
        gains = [self.adc_gain, self.adc_gain]
        refs = [c.AREF_DIFF, c.AREF_DIFF]
        self.speed_flag = "hs"
        self.ls_period = period
        self.get_data(channels,gains,refs,self.hs_freq,period)
        
    def get_data(self,channels,gains,refs,frequency,period):
        self.collect_data_stop()
        self.comedi_reset()
        self.reset_queues()
        self.setup_filtering()

        cmd = self.prepare_cmd(channels, gains,refs,frequency)
        #Get base timestamp here with tap delay
        self.adc_time  = datetime.datetime.utcnow()
        ret = c.comedi_command(self.dev,cmd)
        if ret<0:
            self.logger.error("Error executing comedi_command")
            return -1
        if self.speed_flag == "ls":
            self.collector_thread = threading.Thread(target=self.ls_collect_data)
            self.collector_thread.daemon = True
            self.collector_thread.start()
        
            self.filter_thread = threading.Thread(target=self.filter_data)
            self.filter_thread.daemon = True
            self.filter_thread.start()
        else:
            self.collector_thread = threading.Thread(target=self.hs_collect_data)
            self.collector_thread.daemon = True
            self.collector_thread.start()
       
        if period > 0:
            self.stop_timer = threading.Timer(period,self.collect_data_stop)
            self.stop_timer.daemon = True
            self.stop_timer.start()

    def collect_data_stop(self):
        self.cancel_logging()
        self.stop_event.set()
        self.filter_event.set()
        if self.filter_thread.isAlive():
            self.filter_thread.join()
        #if self.collector_thread.isAlive():
        #    self.collector_thread.join()

    def filter_data(self):
        #This thread checks for data in the sa_temp buffer
        #It then pipes it out to the filter class and get back
        #the low-pass filtered data - ideally in real-time ish
        self.filter_event.clear()
        first_pass = True
        chunk_size = 2**self.chunk_power
        while not self.stop_event.isSet():
            #Both should be filling up so make sure both are above chunk size
            if (size(self.sa_temp) > chunk_size) and (size(self.fb_temp) > chunk_size):
                chunk_sa = []
                chunk_fb = []    
                chunk_ts = []
                self.filter_lock.acquire()
                for i in xrange(chunk_size): #Is this really the only way
                    chunk_sa.append(self.sa_temp.popleft())
                    chunk_fb.append(self.fb_temp.popleft())
                    chunk_ts.append(self.ts_temp.popleft())
                self.filter_lock.release()

                temp_sa = self.sa_filt.stream_filter(array(chunk_sa),init=first_pass)
                temp_fb = self.fb_filt.stream_filter(array(chunk_fb),init=first_pass)
                temp_ts = self.ts_filt.stream_filter(array(chunk_ts),init=first_pass)

                if size(temp_sa) != size(temp_fb):
                    print len(self.sa_filt.offset),  len(self.fb_filt.offset)

                if self.collect_data_flag is True:
                    self.data_lock.acquire()
                    self.ls_ts_data.extend(temp_ts)
                    self.ls_sa_data.extend(temp_sa)
                    self.ls_fb_data.extend(temp_fb)
                    self.data_lock.release()

                #print  datetime.datetime.utcnow() - self.adc_time
                self.sa_ds.extend(temp_sa)
                self.fb_ds.extend(temp_fb)
                self.ts_ds.extend(temp_ts)

                self.netcdf_data_lock.acquire()
                self.sa_ds_logging.extend(temp_sa)
                self.fb_ds_logging.extend(temp_fb)
                self.mjd_ds_logging.extend(temp_ts)
                self.netcdf_data_lock.release()
                
                #And do some FFTs here if we need to - We have the time
                self.fourier_sa,self.fourier_freq_sa = mlab.psd(self.sa,
                                                                NFFT=2056,Fs=self.ls_freq,
                                                                detrend=mlab.detrend_linear)

                self.fourier_fb,self.fourier_freq_fb = mlab.psd(self.fb,
                                                                NFFT=2056,Fs=self.ls_freq,
                                                                detrend=mlab.detrend_linear)

                self.fourier_sa_ds,self.fourier_freq_sa_ds = mlab.psd(self.sa_ds,
                                                                NFFT=512,Fs=self.true_ds_freq,
                                                                detrend=mlab.detrend_linear)

                self.fourier_fb_ds,self.fourier_freq_fb_ds = mlab.psd(self.fb_ds,
                                                                NFFT=512,Fs=self.true_ds_freq,
                                                                detrend=mlab.detrend_linear)

                if first_pass is True:
                    first_pass = False
                    
            else:
                time.sleep(.05)
      
    def hs_collect_data(self):
        self.stop_event.clear()
        front = 0
        back = 0
        hs_data = []
        self.log_hs_data_start_time = datetime.datetime.utcnow()

        while not self.stop_event.isSet():
            time_now = datetime.datetime.utcnow()
            dt = time_now - self.log_hs_data_start_time
            self.ls_progress = (dt.seconds + dt.microseconds*1.0e-6)*100.0/self.ls_period
            front += c.comedi_get_buffer_contents(self.dev,self.subdevice)
            if front < back:
                self.logger.error("front<back comedi buffer error")
                break
            if (front-back)%8 != 0:
                #print front,back
                front = front-4
            if front == back:
                time.sleep(.01)
                continue
            
            print back,front,(front-back),(front%self.buffer_size)
            self.map.seek(back%self.buffer_size)
            for i in range(back,front,4):
                if i%self.buffer_size == 0:
                    self.map.seek(0)
                hs_data.append(self.map.read(4))

            c.comedi_mark_buffer_read(self.dev,self.subdevice,front-back)
            back = front

        #get remaining data
        front += c.comedi_get_buffer_contents(self.dev,self.subdevice)
        if (front-back)%8 != 0:
                #print front,back
                front = front-4
        if front > back:
            print "ending",back,front,(front-back),(front%self.buffer_size)
            self.map.seek(back%self.buffer_size)
            for i in range(back,front,4):
                if i%self.buffer_size == 0:
                    self.map.seek(0)
                hs_data.append(self.map.read(4))
        
        self.comedi_reset()

        #And process the high speed data
        temp_data = []
        for d in hs_data:
            temp_data.append(struct.unpack("I",d)[0])

        temp_data = array(temp_data)
        temp_data = temp_data.reshape(len(temp_data)/2,2)
        temp_fb = self.convert_to_real(self.adc_gain,temp_data[:,0])
        temp_sa = self.convert_to_real(self.adc_gain,temp_data[:,1])
        self.fb_uf.extend(temp_fb)
        self.sa_uf.extend(temp_sa)
        self.ls_progress = 100

        #And record the data
        if self.dlog.file_name is not None:
            self.dlog.add_hs_data(list(self.sa_uf),list(self.fb_uf),self.hs_freq,
                                  meta=self.hs_meta)

        #finally restart ls data
        self.take_ls_data()      

    def ls_collect_data(self):
        self.stop_event.clear()
        time_diff = datetime.timedelta(microseconds=200)
        front = 0
        back = 0
        while not self.stop_event.isSet():
            front += c.comedi_get_buffer_contents(self.dev,self.subdevice)
            if front < back:
                self.logger.error("front<back comedi buffer error")
                break
            if (front-back)%16 != 0:
                #print front,back
                front = front-(front-back)%16
            if front == back:
                time.sleep(.01)
                continue
            
            self.adc_lock.acquire()
            #start = c.comedi_get_buffer_offset(self.dev,self.subdevice)
            #print start,n_count,(start+n_count)
            self.map.seek(back%self.buffer_size)
            data = []
            for i in range(back,front,4):
                if i%self.buffer_size == 0:
                    self.map.seek(0)
                data.append(struct.unpack("I",self.map.read(4))[0])
          
            dd = array(data)
            n_elements = len(dd)/4
            dd = dd.reshape(n_elements, 4)
            c.comedi_mark_buffer_read(self.dev,self.subdevice,front-back)
            back = front
            self.adc_lock.release()

            #!!!RW247 FIX THIS!!!!!!
            temp_fb = self.convert_to_real(self.adc_gain,dd[:,0])
            temp_sa = self.convert_to_real(self.adc_gain,dd[:,1])
            temp_fb_nofilt = self.convert_to_real(self.adc_gain,dd[:,2])
            temp_sa_nofilt = self.convert_to_real(self.adc_gain,dd[:,3])

            #Here we assume that the first value is first channel
            #self.data_lock.acquire()
            self.fb.extend(temp_fb)
            self.sa.extend(temp_sa)
            self.fb_nofilt.extend(temp_fb_nofilt)
            self.sa_nofilt.extend(temp_sa_nofilt)
            
            self.sa_logging.extend(temp_sa)
            self.fb_logging.extend(temp_fb)

            #self.data_lock.release()
            self.filter_lock.acquire()
            self.fb_temp.extend(temp_fb)
            self.sa_temp.extend(temp_sa)
                
            for i in xrange(n_elements):
                mjd = dt_to_mjd(self.adc_time)
                self.timestamps.append(mjd)
                self.ts_temp.append(mjd)
                self.mjd_logging.append(mjd)
                self.adc_time = self.adc_time + time_diff

            self.filter_lock.release()
            
        #OK so we got a stop call - Halt the command
        #Get the latest data and then reset
        n_count = c.comedi_poll(self.dev,self.subdevice)
        n_count = c.comedi_get_buffer_contents(self.dev,self.subdevice)
        print "END LS POLL", n_count
        #if n_count != 0:
        #    start = c.comedi_get_buffer_offset(self.dev,self.subdevice)
         #   data = self.map[start:(start+n_count)]
 
        self.comedi_reset()

    def convert_to_real(self,gain,data):
        #This function replaces the comedi conversion as it works
        #On arrays (vectorized) and is much faster
        #We also have a gain of -1 to counteract the -1 of the active filter
        v_range = self.gain_lookup[gain]
        volts_per_bit = v_range*2.0/(2**18)
        real_volts = -v_range + volts_per_bit*data
        return -real_volts


    def comedi_reset(self):
        #self.collect_data_stop()
        ret = c.comedi_cancel(self.dev,self.subdevice)
        if ret!=0:
            self.logger.error("Error executing comedi reset")
            return -1

    def prepare_cmd(self,channels,gains,aref,freq):
        #First create the channel setup
        nchans = size(channels)
        channel_config = c.chanlist(nchans) #create a chanlist of length nchans

        print channel_config
        print channels
        
        for index in range(nchans):
            channel_config[index]=c.cr_pack(channels[index], gains[index], aref[index])
        
       #Then create the command
        cmd = c.comedi_cmd_struct()
        
        cmd.subdev = self.subdevice
        cmd.flags = 0
        cmd.start_src = c.TRIG_NOW
        cmd.start_arg = 0
        cmd.scan_begin_src = c.TRIG_TIMER
        cmd.scan_begin_arg = int(1e9/freq)
        cmd.convert_src = c.TRIG_TIMER
        cmd.convert_arg = 0
        cmd.scan_end_src = c.TRIG_COUNT
        cmd.scan_end_arg = nchans
        cmd.stop_src = c.TRIG_NONE
        cmd.stop_arg = 0
        cmd.chanlist = channel_config
        cmd.chanlist_len = nchans

        ret = self.test_cmd(cmd)

        if ret !=0:
            self.logger.error("Error preparing command")
            return -1

        return cmd

    def test_cmd(self,cmd):
        self.logger.info("Command before testing")
        self.dump_cmd(cmd)
        
        ret = c.comedi_command_test(self.dev,cmd)
        temp_str = "First cmd test returns:", ret, self.cmdtest_messages[ret]
        self.logger.info(temp_str)
        self.dump_cmd(cmd)
        if ret<0:
            self.logger.error("comedi_command_test failed")
            return -1

        ret = c.comedi_command_test(self.dev,cmd)
        temp_str = "Second cmd test returns:", ret, self.cmdtest_messages[ret]
        self.logger.info(temp_str)
        self.dump_cmd(cmd)
        if ret<0:
            self.logger.error("comedi_command_test failed")
            return -1
        
        return ret

    def dump_cmd(self,cmd):
        print "---------------------------"
	print "command structure contains:"
	print "cmd.subdev : ", cmd.subdev
	print "cmd.flags : ", cmd.flags
	print "cmd.start :\t", cmd.start_src, "\t", cmd.start_arg
	print "cmd.scan_beg :\t", cmd.scan_begin_src, "\t", cmd.scan_begin_arg
	print "cmd.convert :\t", cmd.convert_src, "\t", cmd.convert_arg
	print "cmd.scan_end :\t", cmd.scan_end_src, "\t", cmd.scan_end_arg
	print "cmd.stop :\t", cmd.stop_src, "\t", cmd.stop_arg
	print "cmd.chanlist : ", cmd.chanlist
	print "cmd.chanlist_len : ", cmd.chanlist_len
	print "cmd.data : ", cmd.data
	print "cmd.data_len : ", cmd.data_len
	print "---------------------------"

    def __del__(self):
        self.logger.info("Deleting Myself")
        self.collect_data_stop()
        self.map.close()
        c.comedi_close(self.dev)

    def launch_gui(self):
        self.app = QtGui.QApplication(sys.argv)
        self.gui = bolo_adc_gui(self)
        self.gui.show()

if __name__ == "__main__":
    b_adc = bolo_adcCommunicator(10000)
    b_adc.launch_gui()
    sys.exit(b_adc.app.exec_())
    
