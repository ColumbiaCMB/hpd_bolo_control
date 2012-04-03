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
from bolo_adc_gui import *
#import dualscope

import matplotlib
#matplotlib.use('GTKAgg') # do this before importing pylab
import matplotlib.pyplot as plt

logging.basicConfig()

class bolo_adcCommunicator():
    def __init__(self,max_buffer=None):
        self.logger = logging.getLogger('bolo_adc')
        self.logger.setLevel(logging.DEBUG)
        self.max_buffer = max_buffer

        self.fb = collections.deque(maxlen=max_buffer) #ls_freq buffer
        self.fb_uf = collections.deque(maxlen=max_buffer)#hs_freq buffer
        self.fb_temp = collections.deque(maxlen=max_buffer) #For FIR filtering
        self.fb_ds =  collections.deque(maxlen=max_buffer)#downsample_buffer

        self.sa  = collections.deque(maxlen=max_buffer)
        self.sa_uf = collections.deque(maxlen=max_buffer)
        self.sa_temp = collections.deque(maxlen=max_buffer) #For FIR filtering
        self.sa_ds =  collections.deque(maxlen=max_buffer)
        self.ls_data = collections.deque() #timestamp with FIR delay

        self.timestamps = collections.deque(maxlen=max_buffer)
        self.ts_temp = collections.deque(maxlen=max_buffer)
        self.ts_ds =  collections.deque(maxlen=max_buffer)

        self.stop_event = threading.Event()
        self.filter_event = threading.Event()
        self.filter_lock = threading.Lock()
        self.data_lock = threading.Lock() #Used for poping data to client
        self.adc_lock = threading.Lock() #Used for poping data to client

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

        self.fb_gain = 3
        self.sa_gain = 3

        self.ls_freq = 5000 #Low speed data taking frequency
        self.hs_freq = 500000 #High speed data taking frequency
        
        self.chunk_power = 12 #filter chunk size
        self.ntaps = 1001

        self.sa_filt = bolo_filtering(ntaps=self.ntaps,
                                      cutoff_hz=35,sample_rate=self.ls_freq,
                                      decimate = 50) #100 hz 5000/50

        self.fb_filt = bolo_filtering(ntaps=self.ntaps,
                                      cutoff_hz=35,sample_rate=self.ls_freq,
                                      decimate = 50) #100 hz 5000/50

        self.ts_filt = bolo_filtering(ntaps=self.ntaps,
                                      cutoff_hz=35,sample_rate=self.ls_freq,
                                      decimate = 50) #100 hz 5000/50

        self.collect_data_flag = False

        #temorary data
        self.x_min = 0
        self.x_max = 0.03
        self.setup_adc()

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
        #First clear the buffer
        if state is True:
            self.data_lock.acquire()
            self.ls_data.clear()
            self.data_lock.release()
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
        self.fb_uf.clear()
        self.fb_temp.clear()
        self.fb_ds.clear()

        self.sa.clear()
        self.sa_uf.clear()
        self.sa_temp.clear()
        self.sa_ds.clear()

        self.timestamps.clear()
        self.ts_temp.clear()
        self.ts_ds.clear()

        self.filter_lock.release()

        self.data_lock.acquire()
        self.ls_data.clear()
        self.data_lock.release()


    def get_ls_data(self,period):
        #This is a wrapper to setup for lowspeed data taking
        #This is just the filtered outputs
        self.reset_queues()
        channels = [self.fb_chan, self.sa_chan]
        gains = [self.fb_gain, self.sa_gain]
        refs = [c.AREF_DIFF, c.AREF_DIFF]
        self.speed_flag = "ls"
        self.get_data(channels,gains,refs,self.ls_freq,period)

    def get_hs_data(self,period):
        #This is a wrapper to setup for lowspeed data taking
        #This is just the filtered outputs
        channels = [self.fb_uf_chan, self.sa_uf_chan]
        gains = [self.fb_gain, self.sa_gain]
        refs = [c.AREF_DIFF, c.AREF_DIFF]
        self.speed_flag = "hs"
        self.get_data(channels,gains,refs,self.hs_freq,period)
        
    def get_data(self,channels,gains,refs,frequency,period):
        self.comedi_reset()
        cmd = self.prepare_cmd(channels, gains,refs,frequency)
        #Get base timestamp here with tap delay
        self.adc_time  = datetime.datetime.utcnow()
        ret = c.comedi_command(self.dev,cmd)
        if ret<0:
            self.logger.error("Error executing comedi_command")
            return -1
        collector_thread = threading.Thread(target=self.collect_data)
        collector_thread.daemon = True
        collector_thread.start()
        filter_thread = threading.Thread(target=self.filter_data)
        filter_thread.daemon = True
        filter_thread.start()
        if period > 0:
            stop_timer = threading.Timer(period,self.collect_data_stop)
            stop_timer.start()
        else:
            self.logger.info("Taking data indefinitely - watch for memory usage")

    def collect_data_stop(self):
        self.stop_event.set()
        self.filter_event.set()

    def write_data(self,filename,ftwo):
        #Dead simple thread that writes to a text file every second
        #For debug purposes
        temp_file = open(filename,"w")
        temp_file2 = open(ftwo,"w")

        while not self.stop_event.isSet():
            n_elements = size(self.fb_ds)
            if n_elements != 0:
                self.filter_lock.acquire()
                for i in xrange(n_elements):
                    temp_file.write(str(self.fb_ds.popleft()))
                    temp_file.write("\n")
                self.filter_lock.release()

            n_elements = size(self.fb)
            if n_elements != 0:
                self.filter_lock.acquire()
                for i in xrange(n_elements):
                    temp_file2.write(str(self.fb.popleft()))
                    temp_file2.write("\n")
                self.filter_lock.release()
            temp_file.flush()
            time.sleep(1)

        temp_file.close()
        temp_file2.close()

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
                for i in xrange(len(temp_fb)):
                    #Think we need to do it like this maybe
                    #Thre is a more efficient way
                    #We only add data if the collect data flag is set
                    if self.collect_data_flag is True:
                        self.data_lock.acquire()
                        self.ls_data.append([temp_ts[i],temp_sa[i],temp_fb[i]])
                        self.data_lock.release()

                #print  datetime.datetime.utcnow() - self.adc_time
                self.sa_ds.extend(temp_sa)
                self.fb_ds.extend(temp_fb)
                self.ts_ds.extend(temp_ts)

                if first_pass is True:
                    first_pass = False
                    
            else:
                time.sleep(.05)
          
    def collect_data(self):
        self.stop_event.clear()
        time_diff = datetime.timedelta(microseconds=200)
        while not self.stop_event.isSet():
            n_count = c.comedi_get_buffer_contents(self.dev,self.subdevice)
            if n_count == 0:
                time.sleep(.01)
                continue
            if n_count % 2: #Odd then take one less
                self.logger.info("n_count is odd!")
                n_count = n_count - 1
            self.adc_lock.acquire()
            start = c.comedi_get_buffer_offset(self.dev,self.subdevice)
            data = self.map[start:(start+n_count)]
            format = "%iI" % (n_count/4)
            dd = array(struct.unpack(format,data))
            dd = dd.reshape(n_count/8, 2)

            self.adc_lock.release()
            temp_fb = self.convert_to_real(self.fb_gain,dd[:,0])
            temp_sa = self.convert_to_real(self.sa_gain,dd[:,1])
            #Here we assume that the first value is first channel
            if self.speed_flag == "ls":
                self.data_lock.acquire()
                self.fb.extend(temp_fb)
                self.sa.extend(temp_sa)
                self.data_lock.release()
                self.filter_lock.acquire()
                self.fb_temp.extend(temp_fb)
                self.sa_temp.extend(temp_sa)
                
                for i in xrange(n_count/8):
                    mjd = dt_to_mjd(self.adc_time)
                    self.timestamps.append(mjd)
                    self.ts_temp.append(mjd)
                    self.adc_time = self.adc_time + time_diff

                self.filter_lock.release()
            else:
                self.fb_uf.extend(temp_fb)
                self.sa_uf.extend(temp_sa)

            c.comedi_mark_buffer_read(self.dev,self.subdevice,n_count)
            
            
        #OK so we got a stop call - Halt the command
        #Get the latest data and then reset
        n_count = c.comedi_poll(self.dev,self.subdevice)
        n_count = c.comedi_get_buffer_contents(self.dev,self.subdevice)
        print "END POLL", n_count
        if n_count != 0:
            start = c.comedi_get_buffer_offset(self.dev,self.subdevice)
            data = self.map[start:(start+n_count)]
 
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
        #First stop  the command
        ret = c.comedi_cancel(self.dev,self.subdevice)
        if ret!=0:
            self.logger.error("Error executing comedi reset")
            return -1
        self.stop_event.set()
        self.filter_event.set()

    def prepare_cmd(self,channels,gains,aref,freq):
        #First create the channel setup
        nchans = size(channels)
        channel_config = c.chanlist(nchans) #create a chanlist of length nchans

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
        

    def test_plot(self):
        fig = plt.figure()
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)
        #ax1.set_autoscale_on(False)
        #ax2.set_autoscale_on(False)
        #ax1.axis([0,self.max_buffer,self.x_min,self.x_max])
        #ax2.axis([0,self.max_buffer,self.x_min,self.x_max])

        line1, = ax1.plot(array(self.fb_ds)[-300:])
        line2, = ax2.plot(array(self.sa_ds)[-300:])

        while(1):
            line1.set_ydata(array(self.fb_ds)[-300:])
            line2.set_ydata(array(self.sa_ds)[-300:])
            ax1.relim()
            ax2.relim()
            ax1.autoscale_view(True, True, True)
            ax2.autoscale_view(True, True, True)
            fig.canvas.draw()
            time.sleep(0.2)


    def plot_thread(self):
        temp_thread = threading.Thread(target=self.test_plot)
        temp_thread.daemon = True
        temp_thread.start()

    def test_fft(self):
        fig = plt.figure()
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)
        #ax1.set_autoscale_on(true)
        #ax2.set_autoscale_on(False)
        #ax1.axis([0,self.max_buffer,self.x_min,self.x_max])
        #ax2.axis([0,self.max_buffer,self.x_min,self.x_max])
        
        freq = fft.fftfreq(len(self.sa),(1.0/self.ls_freq))
        fourier = abs(fft.fft(self.sa))
        line1, = ax1.plot(self.sa)
        line2, = ax2.plot(freq[3:400],fourier[3:400])
        #ax2.set_yscale('log')

        while(1):
            fourier = abs(fft.fft(self.sa))
            line1.set_ydata(self.sa)
            line2.set_ydata(fourier[3:400])
            ax1.relim()
            ax2.relim()
            ax1.autoscale_view(True, True, True)
            ax2.autoscale_view(True, True, True)
            fig.canvas.draw()
            time.sleep(0.2)


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
    b_adc.get_ls_data(0)
    b_adc.launch_gui()
    b_adc.gui.plot_timer.start(100)
    sys.exit(b_adc.app.exec_())
    
