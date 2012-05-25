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
        self.log_streams = False
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
            if self.stream_sources[name]["log"] is False:
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

    def add_hs_data(self,sa_data,fb_data,freq,mjd=None,
                    meta=None,suffix=None):
        #Ideally an mjd will be supplied of the start time 
        #If not we just add one here
        print "ADDING DATA"

        temp_date = date_toolkit("now","file")
        if suffix is None:
            group_name = "HS_%s" % temp_date
        else:
            group_name = "%s_HS_%s" % (suffix,temp_date)

        group = self.rootgrp.createGroup(group_name)
        group.createDimension("n_points",len(sa_data))

        sa_var = group.createVariable("SA",'f4',("n_points"),zlib=True)
        fb_var = group.createVariable("FB",'f4',("n_points"),zlib=True)
        group.sample_freq = freq
        group.log = meta

        sa_var[:] = sa_data
        fb_var[:] = fb_data
            
    def record_ls_data(self,state,meta=None,suffix=None):
        #This function records lowspeed data
        #It will only record data where "log" is True 
        #It sets up a group as normal but it doesn't contain
        #Any actually data - Instead it logs the start And
        #stop indicies and mjd of the data.  the actual data
        #Is just appened into the unlimeted dimension
        if state is True:
            temp_date = date_toolkit("now","file")
            if suffix is None:
                group_name = "LS_%s" % temp_date
            else:
                group_name = "%s_LS_%s" % (suffix,temp_date)

            self.ls_group = self.rootgrp.createGroup(group_name)
        
            self.ls_group.start_index_100hz = len(self.dim_100hz)
            self.ls_group.start_index_5khz = len(self.dim_5khz)
            self.ls_group.log = meta
            self.log_streams = True
        else:
            self.log_streams = False
            self.ls_group.end_index_100hz = len(self.dim_100hz)
            self.ls_group.end_index_5khz = len(self.dim_5khz)

    def add_VPHI_data(self,Phi,V,mjd,meta=None,suffix=None):
        #This adds data to the netcdf file 
        #The data arrives as a dict with the bias_points as the key
        #due to the way the data works, we create separate variables
        #for each V-Phi and also record the bias points
        #this **may** make analysis slightly more complex but keeps
        #things simple here
            
        self.test_data = Phi
        temp_date = mjd_to_dt(mjd)
        temp_date = date_toolkit(temp_date,"file")
        if suffix is None:
            group_name = "VPHI_%s" % temp_date
        else:
            group_name = "%s_VPHI_%s" % (suffix,temp_date)

        group = self.rootgrp.createGroup(group_name)
        
        bpoints = []
        curve_num = 0 
        for bias_point in sorted(Phi.iterkeys()):
            bpoints.append(bias_point)
            phi_data = []
            v_data = []
            phi_data.extend(Phi[bias_point])
            v_data.extend(V[bias_point])
            n_points = len(phi_data)

            dim_name = "n_points_%i" % curve_num
            phi_name = "PHI_%i" % curve_num
            v_name = "V_%i" % curve_num
            group.createDimension(dim_name,len(phi_data))
            phi_var = group.createVariable(phi_name,'f4',(dim_name),zlib=True)
            v_var = group.createVariable(v_name,'f4',(dim_name),zlib=True)
            phi_var[:] = phi_data
            v_var[:] = v_data
            curve_num += 1

        
        group.createDimension("n_biases",len(Phi))
        #mjd_var = group.createVariable("mjd",'f8',("n_points","n_biases"),zlib=True)
        b_points =group.createVariable("bias_points",'f4',("n_biases"),zlib=True)
        b_points[:] = bpoints

        if meta is not None:
            group.log = meta

        group.bias_points = bpoints
        self.rootgrp.sync()

    def add_IV_data(self,I,V,mjd,meta=None,suffix=None):
        #This adds IV data - We only really have one of these
   
        temp_date = mjd_to_dt(mjd[0])
        temp_date = date_toolkit(temp_date,"file")
        if suffix is None:
            group_name = "IV_%s" % temp_date
        else:
            group_name = "%s_IV_%s" % (suffix,temp_date)

        group = self.rootgrp.createGroup(group_name)

        group.createDimension("n_points",len(I))

        I_var = group.createVariable("I",'f4',("n_points"),zlib=True)
        V_var = group.createVariable("V",'f4',("n_points"),zlib=True)
        mjd_var = group.createVariable("mjd",'f8',("n_points"),zlib=True)
                        
        I_var[:] = I
        V_var[:] = V
        mjd_var[:] = mjd

        if meta is not None:
            group.log = meta

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

        if self.log_streams is True:
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
        self.file_size = float(tstat.st_size)
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
        self.rootgrp.close()
        self.file_name = None
        self.file_size = 0
        
