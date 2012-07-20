import scipy.signal as sig
from numpy import *

class bolo_filtering:
    def __init__(self,ntaps=1001,
                 cutoff_hz=35,sample_rate=5000,
                 decimate = None):
        self.ntaps = ntaps
        self.overlap = ntaps-1
        self.cutoff_hz = cutoff_hz
        self.decimate = decimate
        self.sample_rate = sample_rate
        self.nyq_rate = sample_rate/2.0

        self.setup_FIR()

    def setup_FIR(self):
        #Do a simple hanning window
        self.taps = sig.firwin(self.ntaps,self.cutoff_hz/self.nyq_rate)
        #And calulate the response in case you fancy a look
        self.w,self.h = sig.freqz(self.taps,worN=10000)
        self.freq = (self.w/pi)*self.nyq_rate
        self.h_Db = 20*log10(abs(self.h))

    def simple_filter(self,data):
        return sig.lfilter(self.taps,1.0,data)

    def stream_filter(self,chunk,init=False):
        #This uses the Overlap-add method to filter
        #streaming data or large data sizes
        #I think you can send in different chunk size but
        #should be 2**n
        #If we are starting then clear the data and we don't add
        
        #We also add timesamps in here to match up
        chunk_size = chunk.size
        filt = convolve(self.taps,chunk) #this is self.overlap larger

        if init is True:
            #And we shold not return the
            #FIR offset at the beginning
            self.extra = []
            self.offset = (self.ntaps-1)/2
        else:
            #We add and then expand
            filt[0:self.overlap] = filt[0:self.overlap] + self.extra
        self.extra = filt[chunk_size:]

        if self.decimate is not None:
            #We have to be careful otherwise we loose data sync
            #We could try saving the data but instead just skip
            #The relevent number entries next time around
            t_data = filt[self.offset:chunk_size:self.decimate]
            self.offset = self.decimate - len(filt[self.offset:chunk_size]) % self.decimate
            return t_data
        else:
            return filt[0:chunk_size]

    def test_stream(self,data,chunk_power):
        chunk_size = 2**chunk_power
        n_of_chunks = int(ceil(data.size/(1.0*chunk_size)))
        self.stream_filter(data[0:chunk_size], init=True)

        for i in xrange(1,n_of_chunks):
            print i, i*chunk_size, (i+1)*chunk_size, data.size
            self.stream_filter(data[(i*chunk_size):((i+1)*chunk_size)])
        
