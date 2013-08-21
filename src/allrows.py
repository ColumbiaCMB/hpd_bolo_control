# -*- coding: utf-8 -*-
"""
Created on Thu Feb 14 15:26:57 2013

@author: -
"""

import threading
import time

mb = main_b

def scanrows(rows=range(16),fb_start=-1,fb_stop=1,fb_step=0.002,bias_start=0.4,bias_stop=0.6,n_steps=10):
    tic = time.time()
    for row in rows:
        print "measuring s1 on row",row
        mb.bb_gui.rs_channel_Input.setValue(row)
        mb.bb_gui.rs_channel_Button.click()
        mb.sq.s1_VPhi(fb_start,fb_stop,fb_step,bias_start,bias_stop,n_steps)
        print "finished row",row," elapsed time", time.time()-tic
        print "waiting..."
        time.sleep(5)
        

def do_scanrows(rows=range(16),fb_start=-1,fb_stop=1,fb_step=0.002,bias_start=0.2,bias_stop=0.9,n_steps=20):
    worker = threading.Thread(target=scanrows,
              args = (rows,fb_start,fb_stop,fb_step,bias_start,bias_stop,n_steps))
    worker.daemon = True
    worker.start()
    return worker
    print "launched worker"