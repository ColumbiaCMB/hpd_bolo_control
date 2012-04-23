from PyQt4 import QtCore, QtGui,Qt
from adc_ui import Ui_ADC_control
import PyQt4.Qwt5 as Qwt
from numpy import arange,sqrt

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

"""This code is messy - One should write a class for
The plots - The lazyness comes from using qtdesigner 
to make the GUIs... Sorry if your looking for bugs"""

class bolo_adc_picker(Qwt.QwtPlotPicker):
    def __init__(self,qwt_plot):
        Qwt.QwtPlotPicker.__init__(self,
                                   Qwt.QwtPlot.xBottom,
                                   Qwt.QwtPlot.yLeft,
                                   Qwt.QwtPicker.PointSelection | Qwt.QwtPicker.DragSelection,
                                   Qwt.QwtPlotPicker.CrossRubberBand,
                                   Qwt.QwtPicker.AlwaysOn,
                                   qwt_plot.canvas())

        self.setRubberBandPen(Qt.QPen(Qt.Qt.green))
        self.setTrackerPen(Qt.QPen(Qt.Qt.red))

class bolo_adc_zoomer(Qwt.QwtPlotZoomer):
    def __init__(self,qwt_plot):
        Qwt.QwtPlotZoomer.__init__(self,
                                   Qwt.QwtPlot.xBottom,
                                   Qwt.QwtPlot.yLeft,
                                   Qwt.QwtPicker.DragSelection,
                                   Qwt.QwtPicker.AlwaysOff,
                                   qwt_plot.canvas())
        self.setRubberBandPen(Qt.QPen(Qt.Qt.green))
        self.setEnabled(False)

class bolo_adc_mover(Qwt.QwtPlotZoomer):
    def __init__(self,qwt_plot):
        Qwt.QwtPlotZoomer.__init__(self,
                                   Qwt.QwtPlot.xBottom,
                                   Qwt.QwtPlot.yLeft,
                                   Qwt.QwtPicker.PointSelection | Qwt.QwtPicker.DragSelection,
                                   Qwt.QwtPicker.AlwaysOff,
                                   qwt_plot.canvas())
        self.setRubberBand(Qwt.QwtPicker.NoRubberBand)
        self.setEnabled(False)

class bolo_adc_gui(QtGui.QDialog):
    def __init__(self,parent,gui_parent=None):
        QtGui.QDialog.__init__(self, gui_parent)
        self.p = parent
        self.ui = Ui_ADC_control()
        self.ui.setupUi(self)
        self.plot_timer = QtCore.QTimer()

        self.setup_plots()
        self.setup_picker()
        self.setup_zooms()
        self.setup_slots()


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

        #FFT Plots (should really create a class)

        self.ui.fft_fb_plot.setCanvasBackground(Qt.Qt.darkBlue)
        self.fft_fb_ds_curve = Qwt.QwtPlotCurve("FB FFT LS Monitor")
        self.fft_fb_curve = Qwt.QwtPlotCurve("FB FFT Monitor")
        self.fft_fb_ds_curve.attach(self.ui.fft_fb_plot)
        self.fft_fb_curve.attach(self.ui.fft_fb_plot)
        self.fft_fb_ds_curve.setPen(Qt.QPen(Qt.Qt.yellow))
        self.fft_fb_curve.setPen(Qt.QPen(Qt.Qt.green))
        self.ui.fft_fb_plot.setAxisScaleEngine(Qwt.QwtPlot.xBottom, Qwt.QwtLog10ScaleEngine())
        self.ui.fft_fb_plot.setAxisScaleEngine(Qwt.QwtPlot.yLeft, Qwt.QwtLog10ScaleEngine())
        
        self.fft_fb_grid = Qwt.QwtPlotGrid()
        self.fft_fb_grid.enableXMin(True)
        self.fft_fb_grid.setMajPen(Qt.QPen(Qt.Qt.white,0,Qt.Qt.DotLine))
        self.fft_fb_grid.setMinPen(Qt.QPen(Qt.Qt.gray,0,Qt.Qt.DotLine))
        self.fft_fb_grid.attach(self.ui.fft_fb_plot)

        self.ui.fft_ssa_plot.setCanvasBackground(Qt.Qt.black)
        self.fft_sa_ds_curve = Qwt.QwtPlotCurve("SA FFT LS Monitor")
        self.fft_sa_curve = Qwt.QwtPlotCurve("SA FFT Monitor")
        self.fft_sa_ds_curve.attach(self.ui.fft_ssa_plot)
        self.fft_sa_curve.attach(self.ui.fft_ssa_plot)
        self.fft_sa_ds_curve.setPen(Qt.QPen(Qt.Qt.yellow))
        self.fft_sa_curve.setPen(Qt.QPen(Qt.Qt.green))
        self.ui.fft_ssa_plot.setAxisScaleEngine(Qwt.QwtPlot.xBottom, Qwt.QwtLog10ScaleEngine())
        self.ui.fft_ssa_plot.setAxisScaleEngine(Qwt.QwtPlot.yLeft, Qwt.QwtLog10ScaleEngine())
        
        self.fft_sa_grid = Qwt.QwtPlotGrid()
        self.fft_sa_grid.enableXMin(True)
        self.fft_sa_grid.setMajPen(Qt.QPen(Qt.Qt.white,0,Qt.Qt.DotLine))
        self.fft_sa_grid.setMinPen(Qt.QPen(Qt.Qt.gray,0,Qt.Qt.DotLine))
        self.fft_sa_grid.attach(self.ui.fft_ssa_plot)

    def setup_zooms(self):
        self.fft_ssa_mover = bolo_adc_mover(self.ui.fft_ssa_plot)
        self.fft_ssa_zoomer = bolo_adc_zoomer(self.ui.fft_ssa_plot)

    def setup_picker(self):
        self.fb_picker = bolo_adc_picker(self.ui.fb_plot)
        self.sa_picker = bolo_adc_picker(self.ui.ssa_plot)
        self.fb_ds_picker = bolo_adc_picker(self.ui.fb_plot_ds)
        self.sa_ds_picker = bolo_adc_picker(self.ui.ssa_plot_ds)
        self.fft_fb_picker = bolo_adc_picker(self.ui.fft_fb_plot)
        self.fft_ssa_picker = bolo_adc_picker(self.ui.fft_ssa_plot)

    def setup_slots(self):
        QtCore.QObject.connect(self.ui.Reset_Button,QtCore.SIGNAL("clicked()"), self.reset_data_logging)
        QtCore.QObject.connect(self.plot_timer, QtCore.SIGNAL("timeout()"), self.update_plots)
        QtCore.QObject.connect(self.ui.LSData_Button,QtCore.SIGNAL("toggled(bool)"), self.ls_data_exec)
        QtCore.QObject.connect(self.ui.fft_ssa_zoomButton,QtCore.SIGNAL("toggled(bool)"), self.fft_ssa_zoom)
        QtCore.QObject.connect(self.ui.fft_ssa_auto,QtCore.SIGNAL("toggled(bool)"), self.fft_ssa_autoscale)
        QtCore.QObject.connect(self.ui.fft_ssa_xs_Input,QtCore.SIGNAL("valueChanged(double)"), self.fft_ssa_set_range)
        QtCore.QObject.connect(self.ui.fft_ssa_xe_Input,QtCore.SIGNAL("valueChanged(double)"), self.fft_ssa_set_range)
        QtCore.QObject.connect(self.ui.fft_ssa_ys_Input,QtCore.SIGNAL("valueChanged(double)"), self.fft_ssa_set_range)
        QtCore.QObject.connect(self.ui.fft_ssa_ye_Input,QtCore.SIGNAL("valueChanged(double)"), self.fft_ssa_set_range)

    def fft_ssa_autoscale(self,state):
        self.ui.fft_ssa_xs_Input.setEnabled(not state)
        self.ui.fft_ssa_xe_Input.setEnabled(not state)
        self.ui.fft_ssa_ys_Input.setEnabled(not state)
        self.ui.fft_ssa_ye_Input.setEnabled(not state)

        if state is True:
            self.ui.fft_ssa_zoomButton.setChecked(False)
            self.ui.fft_ssa_plot.setAxisAutoScale(Qwt.QwtPlot.xBottom)
            self.ui.fft_ssa_plot.setAxisAutoScale(Qwt.QwtPlot.yLeft)


    def fft_ssa_set_range(self,dummy_val):
        self.ui.fft_ssa_plot.setAxisScale(Qwt.QwtPlot.xBottom, 
                                          self.ui.fft_ssa_xs_Input.value(),
                                          self.ui.fft_ssa_xe_Input.value())
        self.ui.fft_ssa_plot.setAxisScale(Qwt.QwtPlot.yLeft, 
                                          pow(10,self.ui.fft_ssa_ys_Input.value()),
                                          pow(10,self.ui.fft_ssa_ye_Input.value()))

    def fft_ssa_zoom(self, state):
        self.fft_ssa_mover.setEnabled(state)
        self.fft_ssa_mover.setZoomBase()
        self.fft_ssa_zoomer.setEnabled(state)
        self.fft_ssa_zoomer.setZoomBase()

        if state:
            self.fft_ssa_picker.setRubberBand(Qwt.QwtPicker.NoRubberBand)
        else:
            self.fft_ssa_picker.setRubberBand(Qwt.QwtPicker.CrossRubberBand)

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

        #Deal with the FFTs - We like V/sqrt(hz)
        self.fft_fb_curve.setData(self.p.fourier_freq_fb[3:],sqrt(self.p.fourier_fb[3:]))
        self.fft_fb_ds_curve.setData(self.p.fourier_freq_fb_ds[3:],sqrt(self.p.fourier_fb_ds[3:]))
        self.fft_sa_curve.setData(self.p.fourier_freq_sa[3:],sqrt(self.p.fourier_sa[3:]))
        self.fft_sa_ds_curve.setData(self.p.fourier_freq_sa_ds[3:],sqrt(self.p.fourier_sa_ds[3:]))

        self.ui.fb_plot.replot()
        self.ui.ssa_plot.replot()
        self.ui.fb_plot_ds.replot()
        self.ui.ssa_plot_ds.replot()
        self.ui.fft_fb_plot.replot()
        self.ui.fft_ssa_plot.replot()
