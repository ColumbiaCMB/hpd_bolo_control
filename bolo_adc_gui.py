from PyQt4 import QtCore, QtGui,Qt
from adc_ui import Ui_ADC_control
import PyQt4.Qwt5 as Qwt
from numpy import arange

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class bolo_adc_gui(QtGui.QDialog):
    def __init__(self,parent,gui_parent=None):
        QtGui.QDialog.__init__(self, gui_parent)
        self.p = parent
        self.ui = Ui_ADC_control()
        self.ui.setupUi(self)
        self.plot_timer = QtCore.QTimer()

        self.setup_slots()
        self.setup_plots()

    def setup_plots(self):
        #self.ui.fb_plot.setTitle("FIR filtered FB")
        self.ui.fb_plot.setCanvasBackground(Qt.Qt.darkBlue)
        self.fb_curve = Qwt.QwtPlotCurve("FB Monitor")
        self.fb_curve.attach(self.ui.fb_plot)
        self.fb_curve.setPen(Qt.QPen(Qt.Qt.yellow))

        self.ui.ssa_plot.setCanvasBackground(Qt.Qt.black)
        self.sa_curve = Qwt.QwtPlotCurve("SA Monitor")
        self.sa_curve.attach(self.ui.ssa_plot)
        self.sa_curve.setPen(Qt.QPen(Qt.Qt.green))
        
        self.ui.fb_plot_ds.setCanvasBackground(Qt.Qt.darkBlue)
        self.fb_ds_curve = Qwt.QwtPlotCurve("FB DS Monitor")
        self.fb_ds_curve.attach(self.ui.fb_plot_ds)
        self.fb_ds_curve.setPen(Qt.QPen(Qt.Qt.yellow))

        self.ui.ssa_plot_ds.setCanvasBackground(Qt.Qt.black)
        self.sa_ds_curve = Qwt.QwtPlotCurve("SA DS Monitor")
        self.sa_ds_curve.attach(self.ui.ssa_plot_ds)
        self.sa_ds_curve.setPen(Qt.QPen(Qt.Qt.green))

        self.ui.fft_fb_plot.setCanvasBackground(Qt.Qt.darkBlue)
        self.fft_fb_ds_curve = Qwt.QwtPlotCurve("FB FFT LS Monitor")
        self.fft_fb_curve = Qwt.QwtPlotCurve("FB FFT Monitor")
        self.fft_fb_ds_curve.attach(self.ui.fft_fb_plot)
        self.fft_fb_curve.attach(self.ui.fft_fb_plot)
        self.fft_fb_ds_curve.setPen(Qt.QPen(Qt.Qt.yellow))
        self.fft_fb_curve.setPen(Qt.QPen(Qt.Qt.red))
        self.ui.fft_fb_plot.setAxisScaleEngine(Qwt.QwtPlot.xBottom, Qwt.QwtLog10ScaleEngine())
        self.ui.fft_fb_plot.setAxisScaleEngine(Qwt.QwtPlot.yLeft, Qwt.QwtLog10ScaleEngine())

        self.ui.fft_ssa_plot.setCanvasBackground(Qt.Qt.black)
        self.fft_sa_ds_curve = Qwt.QwtPlotCurve("SA FFT LS Monitor")
        self.fft_sa_curve = Qwt.QwtPlotCurve("SA FFT Monitor")
        self.fft_sa_ds_curve.attach(self.ui.fft_ssa_plot)
        self.fft_sa_curve.attach(self.ui.fft_ssa_plot)
        self.fft_sa_ds_curve.setPen(Qt.QPen(Qt.Qt.yellow))
        self.fft_sa_curve.setPen(Qt.QPen(Qt.Qt.red))
        self.ui.fft_ssa_plot.setAxisScaleEngine(Qwt.QwtPlot.xBottom, Qwt.QwtLog10ScaleEngine())
        self.ui.fft_ssa_plot.setAxisScaleEngine(Qwt.QwtPlot.yLeft, Qwt.QwtLog10ScaleEngine())

    def setup_slots(self):
        QtCore.QObject.connect(self.ui.Reset_Button,QtCore.SIGNAL("clicked()"), self.reset_data_logging)
        QtCore.QObject.connect(self.plot_timer, QtCore.SIGNAL("timeout()"), self.update_plots)
        QtCore.QObject.connect(self.ui.LSData_Button,QtCore.SIGNAL("toggled(bool)"), self.ls_data_exec)

    def reset_data_logging(self):
        self.p.ls_freq = self.ui.ls_samp_freq_Input.value()
        self.p.hs_freq = self.ui.hs_samp_freq_Input.value()
        self.p.ntaps = self.ui.N_Taps_Input.value()
        self.p.cutoff_freq = self.ui.Cutoff_Input.value()
        self.p.downsample_freq = self.ui.DownSample_Input.value()
        self.p.adc_gain = self.ui.Gain_cb.currentIndex()
        
        #By unchecking the get_ls_data we execute the comedi_reset
        self.ui.LSData_Button.setChecked(False)

    def ls_data_exec(self,state):
        if state is False:

            self.p.comedi_reset()
        else:
            self.plot_timer.start(100)
            time = self.ui.RTime_Input.value()
            self.p.get_ls_data(time)

    def update_plots(self):
        fb_x = arange(len(self.p.fb))
        self.fb_curve.setData(fb_x,list(self.p.fb))
        sa_x = arange(len(self.p.sa))
        self.sa_curve.setData(sa_x,list(self.p.sa))

        fb_ds_x = arange(len(self.p.fb_ds))
        self.fb_ds_curve.setData(fb_ds_x,list(self.p.fb_ds))
        sa_ds_x = arange(len(self.p.sa_ds))
        self.sa_ds_curve.setData(sa_ds_x,list(self.p.sa_ds))

        #Deal with the FFTs
        count_ls = len(self.p.fourier_freq_ds)/2
        count_hs  = len(self.p.fourier_freq)/2
        self.fft_fb_curve.setData(self.p.fourier_freq[3:count_hs],self.p.fourier_fb[3:count_hs])
        self.fft_fb_ds_curve.setData(self.p.fourier_freq_ds[3:count_ls],self.p.fourier_fb_ds[3:count_ls])
        self.fft_sa_curve.setData(self.p.fourier_freq[3:count_hs],self.p.fourier_sa[3:count_hs])
        self.fft_sa_ds_curve.setData(self.p.fourier_freq_ds[3:count_ls],self.p.fourier_sa_ds[3:count_ls])

        self.ui.fb_plot.replot()
        self.ui.ssa_plot.replot()
        self.ui.fb_plot_ds.replot()
        self.ui.ssa_plot_ds.replot()
        self.ui.fft_fb_plot.replot()
        self.ui.fft_ssa_plot.replot()
