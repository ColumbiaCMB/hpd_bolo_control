#set the paths so python can find the comedi module
import sys, os, string, struct, time, mmap, array,time

import comedi as c

from numpy import *
#open a comedi device
dev=c.comedi_open('/dev/comedi0')
test = open('test3.dat', 'w')
device = dev
if not dev: raise "Error openning Comedi device"

#get a file-descriptor for use later
fd = c.comedi_fileno(dev)
if fd<=0: raise "Error obtaining Comedi device file descriptor"



freq=20000 # as defined in demo/common.c
subdevice=0 #as defined in demo/common.c

secs = 3 # used to stop scan after "secs" seconds

nchans = 1

chans= [1]
gains= [ 6 ]
aref =[c.AREF_DIFF ]

cmdtest_messages = [
	"success",
	"invalid source",
	"source conflict",
	"invalid argument",
	"argument conflict",
	"invalid chanlist"]


#wrappers include a "chanlist" object (just an Unsigned Int array) for holding the chanlist information
mylist = c.chanlist(nchans) #create a chanlist of length nchans

#now pack the channel, gain and reference information into the chanlist object
#N.B. the CR_PACK and other comedi macros are now python functions
for index in range(nchans):
	mylist[index]=c.cr_pack(chans[index], gains[index], aref[index])

size = c.comedi_get_buffer_size(dev, subdevice)
print "buffer size is ", size

map = mmap.mmap(fd, size, mmap.MAP_SHARED, mmap.PROT_READ)
print "map = ", map

def dump_cmd(cmd):
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

def prepare_cmd(dev, subdev, C):
    #global cmd
    C.subdev = subdev
    C.flags = 0
    C.start_src = c.TRIG_NOW
    C.start_arg = 0
    C.scan_begin_src = c.TRIG_TIMER
    C.scan_begin_arg = int(1e9/freq)
    C.convert_src = c.TRIG_TIMER
    C.convert_arg = 0
    C.scan_end_src = c.TRIG_COUNT
    C.scan_end_arg = nchans
    C.stop_src = c.TRIG_COUNT
    C.stop_arg = 2000000
    C.chanlist = mylist
    C.chanlist_len = nchans

cmd = c.comedi_cmd_struct()

cmd.chanlist = mylist # adjust for our particular context
cmd.chanlist_len = nchans
cmd.scan_end_arg = nchans

prepare_cmd(dev,subdevice,cmd)
crange = c.comedi_get_range(dev,0,0,gains[0])
print "command before testing"
dump_cmd(cmd)

#test our comedi command a few times. 
ret = c.comedi_command_test(dev,cmd)
print "first cmd test returns ", ret, cmdtest_messages[ret]
if ret<0:
	print "comedi_command_test failed"
dump_cmd(cmd)

ret = c.comedi_command_test(dev,cmd)
print "second test returns ", ret, cmdtest_messages[ret]
if ret<0:
	print "comedi_command_test failed"
if ret !=0:
	dump_cmd(cmd)
	print "ERROR preparing command"
dump_cmd(cmd)


front = 0
back = 0
flag = 1

ret = c.comedi_command(dev,cmd)


for i in xrange(10000):
    n_count = c.comedi_get_buffer_contents(dev,subdevice)
    if n_count == 0:
        time.sleep(.01)
        continue
    start = c.comedi_get_buffer_offset(dev,subdevice)
    data = map[start:(start+n_count)]
    format = "%iI" % (n_count/4)
    #print n_count,start,struct.unpack(format,data)
    dd = struct.unpack(format,data)
    for d in dd:
        test.write(str(c.comedi_to_phys(d,crange,(2**18))))
        test.write("\n")
    print n_count,start
    c.comedi_mark_buffer_read(dev,subdevice,n_count)
    

if ret<0:
    print "error executing comedi_command"

map.close()
test.close()
c.comedi_close(dev)


