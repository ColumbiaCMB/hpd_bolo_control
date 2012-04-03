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

    def setup_slots(self):
        QtCore.QObject.connect(self.plot_timer, QtCore.SIGNAL("timeout()"), self.update_plots)

    def update_plots(self):
        fb_x = arange(len(self.p.fb))
        self.fb_curve.setData(fb_x,list(self.p.fb))
        sa_x = arange(len(self.p.sa))
        self.sa_curve.setData(sa_x,list(self.p.sa))

        fb_ds_x = arange(len(self.p.fb_ds))
        self.fb_ds_curve.setData(fb_ds_x,list(self.p.fb_ds))
        sa_ds_x = arange(len(self.p.sa_ds))
        self.sa_ds_curve.setData(sa_ds_x,list(self.p.sa_ds))

        self.ui.fb_plot.replot()
        self.ui.ssa_plot.replot()
        self.ui.fb_plot_ds.replot()
        self.ui.ssa_plot_ds.replot()
