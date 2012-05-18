from netCDF4 import Dataset
import threading
import logging
import sys
import os
from date_tools import *
from data_logging_gui import *

logging.basicConfig()

class data_logging:
    def __init__(self,):
        self.logger = logging.getLogger('data_logging')
        self.logger.setLevel(logging.DEBUG)

        self.logging_event = threading.Event()
        self.logging_event.set()
        self.chunksize = 512
        self.reg_speeds = {'reg_1hz' : 0, 'reg_100hz'  : 1, 'reg_5khz' : 2}
        self.file_name = None
        self.file_size = 0
        self.top_registers = {}
        self.stream_sources = {}

    def open_file(self,suffix=None):
        temp_name = date_toolkit("now","file")
        if suffix is None:
            self.file_name = temp_name + ".nc"
        else:
            self.file_name = temp_name + "_" + suffix + ".nc"

        self.rootgrp = Dataset(self.file_name, 'w', format='NETCDF4')
        self.setup_file()

        self.addRegGroups()
        self.setStream()
        self.rootgrp.sync()

                                       
    def setup_file(self):
        self.dim_1hz = self.rootgrp.createDimension('reg_1hz',None)
        self.dim_100hz = self.rootgrp.createDimension('reg_100hz',None)
        self.dim_5khz = self.rootgrp.createDimension('reg_5khz',None)

        self.rootgrp.createVariable("mjd_slow",'f8',('reg_1hz'),
                                    zlib=True,chunksizes=[self.chunksize])
        

    ## This adds a stream to the data based on a python
    #deque. It simply pops out the front into the netcdf file 
    #Currently only works with 100Hz data
    #We just put these in the top level rootgrp
    def setStream(self):
        for name in self.stream_sources:
            print name, self.stream_sources[name]["log"]
            if self.stream_sources[name]["log"] is False:
                print name,"False"
                continue
            speed = self.stream_sources[name]["speed"]
            self.rootgrp.createVariable(name,'f4',(speed),
                                    zlib=True,chunksizes=[self.chunksize])

    def addRegisters(self,name,registers):
        self.top_registers[name] = registers

    def addStream(self,name,st_buffer,speed):
        if self.reg_speeds.has_key(speed) is False:
            self.logger.error("Incorrect speed register")
            return -1
        
        temp_dict = {"buffer" : st_buffer, "speed" : speed, "log" : True}
        self.stream_sources[name] = temp_dict
        
    def addRegGroups(self):
        for name in self.top_registers:
            self.rootgrp.createGroup(name)
            #We are just going to use float32 for now...
            #And assume single depth of groups
            for i in self.top_registers[name]:
                self.rootgrp.groups[name].createVariable(i,'f4',('reg_1hz'),
                                                         zlib=True,chunksizes=[self.chunksize])

    def add_hs_data(self,sa_data,fb_data,freq,mjd=None,prefix=None):
        #Ideally an mjd will be supplied of the start time 
        #If not we just add one here
        if mjd is None:
            mjd = mjdnow()
        
        group_name = "HS_%f" % mjd
        if prefix is not None:
            group_name = "%s_%s" % (prefix,group_name)

        group = self.rootgrp.createGroup(group_name)
        group.createDimension("n_points",len(sa_data))

        sa_var = group.createVariable("SA",'f4',("n_points"),zlib=True)
        fb_var = group.createVariable("FB",'f4',("n_points"),zlib=True)
        group.sample_freq = freq

        sa_var[:] = sa_data
        fb_var[:] = fb_data
            
    def add_VPHI_data(self,prefix,V,Phi,mjd,bias_points,suffix=None):
        #This adds data to the netcdf file 
        #We can have multiple inputs
        #prefix is for say SSA,S2,S1
        #suffix is for anything else you need
        
        if suffix is None:
            Phi_name = "Phi"
            V_name = "V"
            mjd_name = "mjd"
            bias_name = "bias_points"
        else:
            Phi_name =  "Phi_" + suffix
            V_name = "V_" + suffix
            mjd_name = "mjd_" + suffix
            bias_name = "bias_points_" + suffix

        temp_name = "_VPHI_%i" & mjd[0]
        group_name = prefix + temp_name 
        group = self.rootgrp.createGroup(group_name)

        n_bias_points = len(bias_points)
        group.createDimension("n_points",len(I))
        group.createDimension("n_biases",n_bias_points)

        Phi_var = group.createVariable(I_name,'f4',("n_points","n_biases"),zlib=True)
        V_var = group.createVariable(V_name,'f4',("n_points","n_biases"),zlib=True)
        mjd_var = group.createVariable(mjd_name,'f8',("n_points","n_biases"),zlib=True)
        b_points =group.createVariable("bias_points",'f4',("n_biases"),zlib=True)

        Phi_var[:,:] = Phi
        V_var[:,:] = V
        mjd[:,:] = mjd
        bias_points[:] = bias_points

    def add_IV_data(self,I,V,mjd,suffix=None):
        #This adds IV data - We only really have one of these
        #Need to add attributes to descibe this but can do later

        if suffix is None:
            I_name = "I"
            V_name = "V"
            mjd_name = "mjd"
        else:
            I_name =  "I_" + suffix
            V_name = "V_" + suffix
            mjd_name = "mjd_" + suffix
       

        group_name = "IV_%f" % mjd[0] #cast to float
        group = self.rootgrp.createGroup(group_name)

        group.createDimension("n_points",len(I))

        I_var = group.createVariable(I_name,'f4',("n_points"),zlib=True)
        V_var = group.createVariable(V_name,'f4',("n_points"),zlib=True)
        mjd_var = group.createVariable(mjd_name,'f8',("n_points"),zlib=True)
                        
        I_var[:] = I
        V_var[:] = V
        mjd_var[:] = mjd

        self.rootgrp.sync()

    def log_data(self):
        #This writes data every second
        #We just grab the current register value for
        #the lowspeed and dump the fifo for the highspeed
        
        slow_reg_size = len(self.dim_1hz)
        self.rootgrp.variables["mjd_slow"][slow_reg_size] = mjdnow()

        for group_names in self.top_registers:
            for reg in self.rootgrp.groups[group_names].variables:
                data = self.top_registers[group_names][reg]
                variable = self.rootgrp.groups[group_names].variables[reg]
                variable[slow_reg_size] = data
                
        #work on streaming data - we log the current start pos of the dimensions
        start_pos_100hz = len(self.dim_100hz)
        start_pos_5khz = len(self.dim_5khz)

        for stream_name in self.stream_sources:
            if self.stream_sources[stream_name]["log"] is False:
                continue
            stream_size =  len(self.stream_sources[stream_name]["buffer"])
            if stream_size == 0:
                break

            #Not sure this is completely safe - I worry that we could loose
            #a block of points from the copy to the clear - Should use mutex
            #Will use mutex but not just yet

            dim_type = self.rootgrp.variables[stream_name].dimensions[0]
            if dim_type == "reg_100hz":
                sp = start_pos_100hz
            elif dim_type == "reg_5khz":
                sp = start_pos_5khz
            else:
                self.logger.error("WTF - bad dimension")

            data = list(self.stream_sources[stream_name]["buffer"])
            self.stream_sources[stream_name]["buffer"].clear()
            self.rootgrp.variables[stream_name][sp:] = data

        self.rootgrp.sync()
        #And get the filesize
        tstat = os.stat(self.file_name)
        self.file_size = tstat.st_size
        if not self.logging_event.isSet():
            threading.Timer(1,self.log_data).start()

    def start_logging(self):
        self.logging_event.clear()
        self.log_data()

    def stop_logging(self):
        self.logging_event.set()
        self.rootgrp.sync()

    def  launch_gui(self):
        self.app = QtGui.QApplication(sys.argv)
        self.gui = data_logging_gui(self)
        self.gui.show()

    def close_file(self):
        if not self.logging_event.isSet():
            self.stop_logging()
        print "here"
        self.rootgrp.close()
        self.file_name = None
        self.file_size = 0
        
