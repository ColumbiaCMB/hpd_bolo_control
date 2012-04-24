from PyQt4 import QtCore, QtGui,Qt
from plot_template import plot_template
import PyQt4.Qwt5 as Qwt
from numpy import arange,sqrt

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class sweep_widget(QtGui.QWidget):
    def __init__(self,gui_parent=None):
        QtGui.QWidget.__init__(self, gui_parent)

        self.layout = QtGui.QGridLayout()

        #Do the bias sweep
        self.biassweep_label = QtGui.QLabel("BIAS Sweep")
        self.biassweep_label.setAlignment(QtCore.Qt.AlignCenter)
        self.start_label = QtGui.QLabel("Start")
        self.stop_label = QtGui.QLabel("Stop")
        self.sweep_label = QtGui.QLabel("Sweep")
        
        self.layout.addWidget(self.biassweep_label,0,0,1,2)
        self.layout.addWidget(self.start_label,1,0,1,1)
        self.layout.addWidget(self.stop_label,2,0,1,1)
        self.layout.addWidget(self.sweep_label,3,0,1,1)

        self.bias_start_Input = QtGui.QDoubleSpinBox()
        self.bias_stop_Input = QtGui.QDoubleSpinBox()
        self.bias_step_Input = QtGui.QDoubleSpinBox()

        self.layout.addWidget(self.bias_start_Input,1,1,1,1)
        self.layout.addWidget(self.bias_stop_Input,2,1,1,1)
        self.layout.addWidget(self.bias_step_Input,3,1,1,1)

        #Do the Feedback
        self.fbsweep_label = QtGui.QLabel("FB Sweep")
        self.fbsweep_label.setAlignment(QtCore.Qt.AlignCenter)
        self.start_label_fb = QtGui.QLabel("Start")
        self.stop_label_fb = QtGui.QLabel("Stop")
        self.sweep_label_fb = QtGui.QLabel("Sweep")
        
        self.layout.addWidget(self.fbsweep_label,4,0,1,2)
        self.layout.addWidget(self.start_label_fb,5,0,1,1)
        self.layout.addWidget(self.stop_label_fb,6,0,1,1)
        self.layout.addWidget(self.sweep_label_fb,7,0,1,1)

        self.fb_start_Input = QtGui.QDoubleSpinBox()
        self.fb_stop_Input = QtGui.QDoubleSpinBox()
        self.fb_step_Input = QtGui.QDoubleSpinBox()

        self.layout.addWidget(self.fb_start_Input,5,1,1,1)
        self.layout.addWidget(self.fb_stop_Input,6,1,1,1)
        self.layout.addWidget(self.fb_step_Input,7,1,1,1)

        self.continuous_check = QtGui.QCheckBox("Continuous")
        self.layout.addWidget(self.continuous_check,8,0,1,2)

        self.VIButton = QtGui.QPushButton("VI")
        self.VPhiButton = QtGui.QPushButton("VPhi")
        self.layout.addWidget(self.VIButton,9,0,1,2)
        self.layout.addWidget(self.VPhiButton,10,0,1,2)

        #Add the plotter
        self.ssa_plot = plot_template()
        self.layout.addWidget(self.ssa_plot,0,2,-1,1)

        #And set the layout
        self.setLayout(self.layout)

        self.setupDefaults()

    def setupDefaults(self):
        self.bias_start_Input.setRange(-5,5)
        self.bias_stop_Input.setRange(-5,5)
        self.bias_step_Input.setRange(-1,1)
        self.fb_start_Input.setRange(-5,5)
        self.fb_stop_Input.setRange(-5,5)
        self.fb_step_Input.setRange(-1,1)

        self.bias_start_Input.setDecimals(3)
        self.bias_stop_Input.setDecimals(3)
        self.bias_step_Input.setDecimals(3)
        self.fb_start_Input.setDecimals(3)
        self.fb_stop_Input.setDecimals(3)
        self.fb_step_Input.setDecimals(3)

        self.bias_start_Input.setSingleStep(0.01)
        self.bias_stop_Input.setSingleStep(0.01)
        self.bias_step_Input.setSingleStep(0.001)
        self.fb_start_Input.setSingleStep(0.01)
        self.fb_stop_Input.setSingleStep(0.01)
        self.fb_step_Input.setSingleStep(0.001)

        self.bias_start_Input.setProperty("value", -5.0)
        self.bias_stop_Input.setProperty("value", 5.0)
        self.bias_step_Input.setProperty("value", 0.001)
        self.fb_start_Input.setProperty("value", -5.0)
        self.fb_stop_Input.setProperty("value", 5.0)
        self.fb_step_Input.setProperty("value", 0.001)

class bolo_squids_gui(QtGui.QDialog):
    def __init__(self,parent,gui_parent=None):
        QtGui.QDialog.__init__(self, gui_parent)

        self.p = parent
        self.setupUi()
        self.setupDefaults()
        self.plot_timer = QtCore.QTimer()

        self.setup_slots()
        self.plot_timer.start(100)
        self.update_functions = []

    def setupUi(self):
        self.setWindowTitle("SQUID Control")
        self.tabWidget = QtGui.QTabWidget(self)

        self.ssa_widget = sweep_widget(self.tabWidget)
        self.tabWidget.addTab(self.ssa_widget, "SSA")
        self.s2_widget = sweep_widget(self.tabWidget)
        self.tabWidget.addTab(self.s2_widget, "S2")
        self.s1_widget = sweep_widget(self.tabWidget)
        self.tabWidget.addTab(self.s1_widget, "S1")
        
        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.tabWidget)
        self.setLayout(self.layout)

    def setupDefaults(self):
        pass

    #def setup_plots(self):    
        self.ssa_current_curve = Qwt.QwtPlotCurve("SSA_IV")
        self.ssa_current_curve.attach(self.ssa_widget.ssa_plot.plot_region)
        self.ssa_current_curve.setPen(Qt.QPen(Qt.Qt.yellow))

    def setup_slots(self):
        QtCore.QObject.connect(self.ssa_widget.VIButton,QtCore.SIGNAL("clicked()"), self.run_ssa_VI)
        QtCore.QObject.connect(self.ssa_widget.VPhiButton,QtCore.SIGNAL("clicked()"), self.run_ssa_VPhi)
        QtCore.QObject.connect(self.plot_timer, QtCore.SIGNAL("timeout()"), self.update_plots)

    def update_plots(self):
        self.ssa_current_curve.setData(self.p.x_cont,self.p.y_cont)
        self.ssa_widget.ssa_plot.plot_region.replot()

    def run_ssa_VPhi(self):
        self.p.ssa_VPhi_thread(self.ssa_widget.fb_start_Input.value(),
                        self.ssa_widget.fb_stop_Input.value(),
                        self.ssa_widget.fb_step_Input.value(),
                        self.ssa_widget.bias_start_Input.value(),
                        self.ssa_widget.bias_stop_Input.value(),
                        5)

    def run_ssa_VI(self):
        #This function takes a VI, either continously or a single shot
        #setup a curve on the plot

        if self.ssa_widget.continuous_check.isChecked() is True:
            count = -1;
        else:
            count = 1;
        print self.ssa_widget.bias_start_Input.value(),self.ssa_widget.bias_stop_Input.value(),self.ssa_widget.bias_step_Input.value(),  count
        self.p.wrapper_sweep_thread("ssa_bias",
                                    self.ssa_widget.bias_start_Input.value(),
                                    self.ssa_widget.bias_stop_Input.value(),
                                    self.ssa_widget.bias_step_Input.value(),
                                    count)

