from PyQt4 import QtCore, QtGui,Qt
from squids_ui import Ui_squids
import PyQt4.Qwt5 as Qwt
from numpy import arange,sqrt

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class bolo_squids_gui(QtGui.QDialog):
    def __init__(self,parent,gui_parent=None):
        QtGui.QDialog.__init__(self, gui_parent)

        self.p = parent
        self.ui = Ui_squids()
        self.ui.setupUi(self)
        self.plot_timer = QtCore.QTimer()

        self.setup_plots()
        self.setup_slots()

    def setup_plots(self):
        self.ui.ssa_plot.setCanvasBackground(Qt.Qt.darkBlue)
        self.ssa_iv_curve = Qwt.QwtPlotCurve("SSA_IV")
        self.ssa_iv_curve.attach(self.ui.ssa_plot)
        self.ssa_iv_curve.setPen(Qt.QPen(Qt.Qt.yellow))

    def setup_slots(self):
        QtCore.QObject.connect(self.ui.ssa_iv_Button,QtCore.SIGNAL("clicked()"), self.temp_func)
        QtCore.QObject.connect(self.plot_timer, QtCore.SIGNAL("timeout()"), self.update_plots)

    def update_plots(self):
        self.ssa_iv_curve.setData(self.p.x_cont,self.p.y_cont)
        self.ui.ssa_plot.replot()

    def temp_func(self):
        self.plot_timer.start(100)
