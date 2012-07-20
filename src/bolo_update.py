import socket
import logging
import threading
import struct as st
from time import *
from numpy import *

logging.basicConfig()

class bolo(threading.Thread):
    def __init__(self,hostname="adc",port=2222):
        super(bolo,self).__init__()

        self.hostname = hostname
        self.port = port
        self.logger = logging.getLogger('BOLO_UPDATE')
        self.logger.setLevel(logging.INFO)
        self.port_mutex = threading.Lock()
        
    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.hostname,self.port))
        self.conn.setblocking(True)
        sleep(0.01)

    def close(self):
        sleep(0.01)
        self.conn.shutdown(1)
        self.conn.close()

    def __del__(self):
        print("Deleting")
        self.conn.close()

    def start(self):
        self.port_mutex.acquire()
        self.connect()
        self.conn.sendall(b"b\n")
        msg = "initialize, channels\n"
        self.conn.sendall(msg.encode())
        self.close()
        self.port_mutex.release()

    ## sending voltage through without decimal??
    def set_address(self, address_number, voltage):
        self.port_mutex.acquire()
        self.connect()
        self.conn.sendall(b"b\n")
        msg = "address, %i, %i\n" % (address_number, voltage) 
        self.conn.sendall(msg.encode())
        self.close()
        self.port_mutex.release()

    def close_address(self, address_number):
        self.port_mutex.acquire()
        self.connect()
        self.conn.sendall(b"b\n")
        msg = "close, %i\n" % (address_number) 
        self.conn.sendall(msg.encode())
        self.close()
        self.port_mutex.release()

    def set_voltages(self, s2bias, s2fb, htr, tesbias):
        self.port_mutex.acquire()
        self.connect()
        self.conn.sendall(b"b\n")
        msg = "voltages, %i, %i, %i, %i\n" % (s2bias, s2fb, htr, tesbias) 
        self.conn.sendall(msg.encode())
        self.close()
        self.port_mutex.release()

    def zero_all(self):
        self.port_mutex.acquire()
        self.connect()
        self.conn.sendall(b"b\n")
        msg = "zero, all\n"
        self.conn.sendall(msg.encode())
        self.close()
        self.port_mutex.release()
        
    def quit_server(self):
        self.port_mutex.acquire()
        self.connect()
        self.conn.sendall(b"b\n")
        msg = "quit, now \n"
        self.conn.sendall(msg.encode())
        self.close()
        self.port_mutex.release()

    
    def set_htr(self, voltage):
        self.port_mutex.acquire()
        self.connect()
        self.conn.sendall(b"b\n")
        msg = "htr,  %i\n" %  (voltage) 
        self.conn.sendall(msg.encode())
        self.close()
        self.port_mutex.release()

        
    def set_s2fb(self, voltage):
        self.port_mutex.acquire()
        self.connect()
        self.conn.sendall(b"b\n")
        msg = "s2fb,  %i\n" %  (voltage) 
        self.conn.sendall(msg.encode())
        self.close()
        self.port_mutex.release()
        
    def set_s2bias(self, voltage):
        self.port_mutex.acquire()
        self.connect()
        self.conn.sendall(b"b\n")
        msg = "s2bias,  %i\n" %  (voltage) 
        self.conn.sendall(msg.encode())
        self.close()
        self.port_mutex.release()

    def set_tesbias(self, voltage):
        self.port_mutex.acquire()
        self.connect()
        self.conn.sendall(b"b\n")
        msg = "tesbias,  %i\n" %  (voltage) 
        self.conn.sendall(msg.encode())
        self.close()
        self.port_mutex.release()
