from PyQt4 import QtCore, QtGui,Qt
from plot_template import plot_template
import PyQt4.Qwt5 as Qwt
from numpy import arange,sqrt
from custom_qt_widgets import *

import numpy as np

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

""" Small class to create a widget with two plots in it
"""
class plot_widget(QtGui.QWidget):
     def __init__(self,fft_plot=False,gui_parent=None):
        QtGui.QWidget.__init__(self, gui_parent)
        self.fft_plot = fft_plot

        self.layout = QtGui.QVBoxLayout()
        print fft_plot
        if fft_plot is True:
            self.fb_plot = plot_template(x_log=True,y_log=True)
            self.ssa_plot = plot_template(x_log=True,y_log=True)
        else:
            self.fb_plot = plot_template()
            self.ssa_plot = plot_template()

        self.layout.addWidget(self.fb_plot)
        self.layout.addWidget(self.ssa_plot)

        self.setLayout(self.layout)
        
        self.setup_plots()

     def setup_plots(self):
         self.fb_plot.plot_region.setCanvasBackground(Qt.Qt.darkBlue)
         self.ssa_plot.plot_region.setCanvasBackground(Qt.Qt.black)
         if self.fft_plot is True:
             #We'll make a grid
             self.fft_fb_grid = Qwt.QwtPlotGrid()
             self.fft_fb_grid.enableXMin(True)
             self.fft_fb_grid.setMajPen(Qt.QPen(Qt.Qt.white,0,Qt.Qt.DotLine))
             self.fft_fb_grid.setMinPen(Qt.QPen(Qt.Qt.gray,0,Qt.Qt.DotLine))
             self.fft_fb_grid.attach(self.fb_plot.plot_region)

             self.fft_ssa_grid = Qwt.QwtPlotGrid()
             self.fft_ssa_grid.enableXMin(True)
             self.fft_ssa_grid.setMajPen(Qt.QPen(Qt.Qt.white,0,Qt.Qt.DotLine))
             self.fft_ssa_grid.setMinPen(Qt.QPen(Qt.Qt.gray,0,Qt.Qt.DotLine))
             self.fft_ssa_grid.attach(self.ssa_plot.plot_region)

             
class bolo_adc_gui(QtGui.QDialog):
    def __init__(self,parent,gui_parent=None):
        QtGui.QDialog.__init__(self, gui_parent)
        self.p = parent
        self.setupUi()
        self.plot_timer = QtCore.QTimer()
        self.setup_plots()
        self.setup_slots()
        self.plot_timer.start(100)

    def setupUi(self):
        self.setWindowTitle("ADC Control")
        #NI CARD stuff
        self.niGroupBox = QtGui.QGroupBox("NI Card Options")
        self.ni_layout = QtGui.QGridLayout()
        self.ls_freq_label = QtGui.QLabel("LS Freq")
        self.hs_freq_label = QtGui.QLabel("HS Freq")
        self.range_label = QtGui.QLabel("Range")
        self.ls_samp_freq_input = QtGui.QSpinBox()
        self.ls_samp_freq_input.setMinimum(5000)
 
        self.hs_samp_freq_input = QtGui.QSpinBox()
        self.hs_samp_freq_input.setMinimum(10000)
        self.hs_samp_freq_input.setMaximum(312500)
        self.hs_samp_freq_input.setProperty("value",312500)

        self.Gain_cb = QtGui.QComboBox()
        self.Gain_cb.addItem("+-10V")
        self.Gain_cb.addItem("+-5V")
        self.Gain_cb.addItem("+-2V")
        self.Gain_cb.addItem("+-1V")
        self.Gain_cb.addItem("+-0.5V")
        self.Gain_cb.addItem("+-0.2V")
        self.Gain_cb.addItem("+-0.1V")
        self.Gain_cb.setCurrentIndex(4)

        self.ni_layout.addWidget(self.ls_freq_label,0,0,1,1)
        self.ni_layout.addWidget(self.hs_freq_label,1,0,1,1)
        self.ni_layout.addWidget(self.range_label,2,0,1,1)
        self.ni_layout.addWidget(self.ls_samp_freq_input,0,1,1,1)
        self.ni_layout.addWidget(self.hs_samp_freq_input,1,1,1,1)
        self.ni_layout.addWidget(self.Gain_cb,2,1,1,1)

        self.niGroupBox.setLayout(self.ni_layout)

        #FIR filter stuff
        self.firGroupBox = QtGui.QGroupBox("FIR filter")
        self.fir_layout = QtGui.QGridLayout()
        self.n_taps_label = QtGui.QLabel("N TAPS")
        self.cutoff_label = QtGui.QLabel("Cutoff")
        self.decimate_label = QtGui.QLabel("Down Freq")
        
        self.N_Taps_Input = QtGui.QSpinBox()
        self.N_Taps_Input.setMinimum(101)
        self.N_Taps_Input.setMaximum(10001)
        self.N_Taps_Input.setProperty("value", 1001)

        self.Cutoff_Input = QtGui.QDoubleSpinBox()
        self.Cutoff_Input.setDecimals(2)
        self.Cutoff_Input.setMinimum(1.0)
        self.Cutoff_Input.setMaximum(100.0)
        self.Cutoff_Input.setSingleStep(0.01)
        self.Cutoff_Input.setProperty("value", 35.0)

        self.DownSample_Input = QtGui.QSpinBox()
        self.DownSample_Input.setMaximum(200)
        self.DownSample_Input.setProperty("value", 100)

        self.fir_layout.addWidget(self.n_taps_label,0,0,1,1)
        self.fir_layout.addWidget(self.cutoff_label,1,0,1,1)
        self.fir_layout.addWidget(self.decimate_label,2,0,1,1)
        self.fir_layout.addWidget(self.N_Taps_Input,0,1,1,1)
        self.fir_layout.addWidget(self.Cutoff_Input,1,1,1,1)
        self.fir_layout.addWidget(self.DownSample_Input,2,1,1,1)

        self.firGroupBox.setLayout(self.fir_layout)

        #Daq option box
        self.daqGroupBox = QtGui.QGroupBox("DAQ Options")
        self.Reset_Button = QtGui.QPushButton()
        self.Reset_Button.setText("Commit and Reset")
        self.daq_layout = QtGui.QVBoxLayout()
        self.daq_layout.addWidget(self.niGroupBox)
        self.daq_layout.addWidget(self.firGroupBox)
        self.daq_layout.addWidget(self.Reset_Button)
        self.daqGroupBox.setLayout(self.daq_layout)
        
        #Record data
        self.recordGroupBox = QtGui.QGroupBox("Record Data")
        self.record_layout = QtGui.QGridLayout()
        self.LSData_Button = QtGui.QPushButton("Record LS Data")
        self.HSData_Button = QtGui.QPushButton("Record HS Data")
        self.Cancel_Button = QtGui.QPushButton("Cancel")
        self.record_time_label = QtGui.QLabel("Record Time (s)")
        self.RTime_Input = QtGui.QSpinBox()
        self.RTime_Input.setProperty("value",60)
        self.RTime_Input.setMinimum(1)
        self.RTime_Input.setMaximum(10000)
        self.Sweep_pb = QtGui.QProgressBar()
        self.Sweep_pb.setProperty("value", 0)
        self.meta_data = QtGui.QPlainTextEdit()
        self.meta_data.setFixedHeight(75)
        self.meta_data.setFixedWidth(150)
        self.filename_label = small_text("No File", "red")

        self.record_layout.addWidget(self.LSData_Button,0,0,1,-1)
        self.record_layout.addWidget(self.HSData_Button,1,0,1,-1)
        self.record_layout.addWidget(self.Cancel_Button,2,0,1,-1)
        self.record_layout.addWidget(self.record_time_label,3,0,1,1)
        self.record_layout.addWidget(self.RTime_Input,3,1,1,1)
        self.record_layout.addWidget(self.Sweep_pb,4,0,1,-1)
        self.record_layout.addWidget(self.meta_data,5,0,1,-1)
        self.record_layout.addWidget(self.filename_label,6,0,1,-1)

        self.recordGroupBox.setLayout(self.record_layout)

        #And combine these all together
        self.left_panel = QtGui.QVBoxLayout()
        self.left_panel.addWidget(self.daqGroupBox)
        self.left_panel.addStretch()
        self.left_panel.addWidget(self.recordGroupBox)

        #And now work on the tabs and plots
        self.tabWidget = QtGui.QTabWidget()
        self.fir_plots = plot_widget(gui_parent=self.tabWidget)
        self.tabWidget.addTab(self.fir_plots, "FIR Data")
        self.raw_plots = plot_widget(gui_parent=self.tabWidget)
        self.tabWidget.addTab(self.raw_plots, "RAW Data")
        self.fft_plots = plot_widget(fft_plot=True,gui_parent=self.tabWidget)
        self.tabWidget.addTab(self.fft_plots, "FFT Data")

        #And now have the final layout
        self.layout = QtGui.QHBoxLayout()
        self.layout.addLayout(self.left_panel)
        self.layout.addWidget(self.tabWidget)

        self.setLayout(self.layout)

    def setup_plots(self):
        self.fb_curve = Qwt.QwtPlotCurve("FB Monitor")
        self.fb_curve.attach(self.raw_plots.fb_plot.plot_region)
        self.fb_curve.setPen(Qt.QPen(Qt.Qt.yellow))

        self.sa_curve = Qwt.QwtPlotCurve("SA Monitor")
        self.sa_curve.attach(self.raw_plots.ssa_plot.plot_region)
        self.sa_curve.setPen(Qt.QPen(Qt.Qt.green))
        
        self.mon_curve = Qwt.QwtPlotCurve("SA Setpoint")
        self.mon_curve.attach(self.raw_plots.ssa_plot.plot_region)
        self.mon_curve.setPen(Qt.QPen(Qt.Qt.blue))
        
        self.err_curve = Qwt.QwtPlotCurve("SA Error")
        self.err_curve.attach(self.raw_plots.ssa_plot.plot_region)
        self.err_curve.setPen(Qt.QPen(Qt.Qt.red))
        
        
        self.fb_ds_curve = Qwt.QwtPlotCurve("FB DS Monitor")
        self.fb_ds_curve.attach(self.fir_plots.fb_plot.plot_region)
        self.fb_ds_curve.setPen(Qt.QPen(Qt.Qt.yellow))

        self.sa_ds_curve = Qwt.QwtPlotCurve("SA DS Monitor")
        self.sa_ds_curve.attach(self.fir_plots.ssa_plot.plot_region)
        self.sa_ds_curve.setPen(Qt.QPen(Qt.Qt.green))

        #FFT plots
        self.fft_fb_ds_curve = Qwt.QwtPlotCurve("FB FFT LS Monitor")
        self.fft_fb_curve = Qwt.QwtPlotCurve("FB FFT Monitor")
        self.fft_fb_ds_curve.attach(self.fft_plots.fb_plot.plot_region)
        self.fft_fb_curve.attach(self.fft_plots.fb_plot.plot_region)
        self.fft_fb_ds_curve.setPen(Qt.QPen(Qt.Qt.yellow))
        self.fft_fb_curve.setPen(Qt.QPen(Qt.Qt.green))     
    
        self.fft_sa_ds_curve = Qwt.QwtPlotCurve("SA FFT LS Monitor")
        self.fft_sa_curve = Qwt.QwtPlotCurve("SA FFT Monitor")
        self.fft_sa_ds_curve.attach(self.fft_plots.ssa_plot.plot_region)
        self.fft_sa_curve.attach(self.fft_plots.ssa_plot.plot_region)
        self.fft_sa_ds_curve.setPen(Qt.QPen(Qt.Qt.yellow))
        self.fft_sa_curve.setPen(Qt.QPen(Qt.Qt.green))
    
  
    def setup_slots(self):
        QtCore.QObject.connect(self.Reset_Button,QtCore.SIGNAL("clicked()"), self.reset_data_logging)
        QtCore.QObject.connect(self.plot_timer, QtCore.SIGNAL("timeout()"), self.update_plots)
        QtCore.QObject.connect(self.LSData_Button,QtCore.SIGNAL("clicked()"), self.ls_data_exec)
        QtCore.QObject.connect(self.HSData_Button,QtCore.SIGNAL("clicked()"), self.hs_data_exec)
        QtCore.QObject.connect(self.Cancel_Button,QtCore.SIGNAL("clicked()"), self.cancel_exec)

    def reset_data_logging(self):
        self.p.ls_freq = self.ls_samp_freq_input.value()
        self.p.hs_freq = self.hs_samp_freq_input.value()
        self.p.ntaps = self.N_Taps_Input.value()
        self.p.cutoff_freq = self.Cutoff_Input.value()
        self.p.downsample_freq = self.DownSample_Input.value()
        self.p.adc_gain = self.Gain_cb.currentIndex()
        
        self.p.reset_ls_data()

    def ls_data_exec(self):
        period = self.RTime_Input.value()
        meta = str(self.meta_data.toPlainText())
        self.p.log_ls_data_start(period,meta)
        
    def hs_data_exec(self):
        period = self.RTime_Input.value()
        meta = str(self.meta_data.toPlainText())
        self.p.get_hs_data(period,meta)

    def cancel_exec(self):
        #This just works with LS data at the moment
        self.p.cancel_logging()

    def log_data_idle(self,state):
        self.LSData_Button.setEnabled(state)
        self.HSData_Button.setEnabled(state)
        self.RTime_Input.setEnabled(state)
        self.meta_data.setEnabled(state)
        self.Cancel_Button.setEnabled(not state)

    def update_plots(self):
        fb_x = arange(len(self.p.fb))
        self.fb_curve.setData(fb_x,list(self.p.fb))
        sa_x = arange(len(self.p.sa))
        self.sa_curve.setData(sa_x,list(self.p.sa_nofilt))
        mon_x = arange(len(self.p.mon))
        self.mon_curve.setData(mon_x,list(self.p.mon))
        err_x = arange(len(self.p.err))
        self.err_curve.setData(err_x,list(self.p.err))

        fb_ds_x = arange(len(self.p.fb_ds))
        self.fb_ds_curve.setData(fb_ds_x,list(self.p.fb_ds))
        sa_ds_x = arange(len(self.p.sa_ds))
        self.sa_ds_curve.setData(sa_ds_x,list(self.p.sa_ds))

        #Deal with the FFTs - We like V/sqrt(hz)
        self.fft_fb_curve.setData(self.p.fourier_freq_fb[3:],sqrt(self.p.fourier_fb[3:]))
        self.fft_fb_ds_curve.setData(self.p.fourier_freq_fb_ds[3:],sqrt(self.p.fourier_fb_ds[3:]))
        self.fft_sa_curve.setData(self.p.fourier_freq_sa[3:],sqrt(self.p.fourier_sa[3:]))
        self.fft_sa_ds_curve.setData(self.p.fourier_freq_sa_ds[3:],sqrt(self.p.fourier_sa_ds[3:]))

        self.fir_plots.fb_plot.plot_region.replot()
        self.fir_plots.ssa_plot.plot_region.replot()
        self.raw_plots.fb_plot.plot_region.replot()
        self.raw_plots.ssa_plot.plot_region.replot()
        self.fft_plots.fb_plot.plot_region.replot()
        self.fft_plots.ssa_plot.plot_region.replot()

        #And check the data logging for a file etc
        if self.p.dlog.file_name is None:
            self.filename_label.set_color_text("No File", "red")
            self.file_label_prefix = None
        else:   
            tmp_txt = "%s " % self.p.dlog.file_name
            self.filename_label.set_color_text(tmp_txt,"blue")
            if self.file_label_prefix is None: 
                self.SaveLabel = small_text("No Info", "blue")
            else:
                tmp_txt = "%s" % (self.file_label_prefix)
                self.SaveLabel.set_color_text(tmp_txt,"green")

        #Check and do things related to logging data
        self.Sweep_pb.setValue(self.p.ls_progress)
        if self.p.log_timer.isAlive():
          self.log_data_idle(False)
        else:
            self.log_data_idle(True)

