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
        self.steps_label_fb = QtGui.QLabel("Steps")

        self.layout.addWidget(self.fbsweep_label,4,0,1,2)
        self.layout.addWidget(self.start_label_fb,5,0,1,1)
        self.layout.addWidget(self.stop_label_fb,6,0,1,1)
        self.layout.addWidget(self.sweep_label_fb,7,0,1,1)
        self.layout.addWidget(self.steps_label_fb,8,0,1,1)

        self.fb_start_Input = QtGui.QDoubleSpinBox()
        self.fb_stop_Input = QtGui.QDoubleSpinBox()
        self.fb_step_Input = QtGui.QDoubleSpinBox()
        self.fb_count_Input = QtGui.QSpinBox()

        self.layout.addWidget(self.fb_start_Input,5,1,1,1)
        self.layout.addWidget(self.fb_stop_Input,6,1,1,1)
        self.layout.addWidget(self.fb_step_Input,7,1,1,1)
        self.layout.addWidget(self.fb_count_Input,8,1,1,1)

        self.continuous_check = QtGui.QCheckBox("Continuous")
        self.layout.addWidget(self.continuous_check,9,0,1,2)

        self.VIButton = QtGui.QPushButton("VI")
        self.VIButton.setAutoDefault(False)
        self.VPhiButton = QtGui.QPushButton("VPhi")
        self.VPhiButton.setAutoDefault(False)
        self.CancelButton = QtGui.QPushButton("Cancel")
        self.CancelButton.setAutoDefault(False)

        self.layout.addWidget(self.VIButton,10,0,1,2)
        self.layout.addWidget(self.VPhiButton,11,0,1,2)
        self.layout.addWidget(self.CancelButton,12,0,1,2)

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
        self.fb_count_Input.setRange(1,10)

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
        self.fb_count_Input.setProperty("value", 5)

    def set_disable_all(self,state):
        #This disables (or enables) all the input controls except
        #Cancel if we are running a sweep

        self.bias_start_Input.setEnabled(state)
        self.bias_stop_Input.setEnabled(state)
        self.bias_step_Input.setEnabled(state)
        self.fb_start_Input.setEnabled(state)
        self.fb_stop_Input.setEnabled(state)
        self.fb_step_Input.setEnabled(state)
        self.VIButton.setEnabled(state)
        self.VPhiButton.setEnabled(state)
        self.fb_count_Input.setEnabled(state)
        self.continuous_check.setEnabled(state)

        self.CancelButton.setEnabled(not state)

class bolo_squids_gui(QtGui.QDialog):
    def __init__(self,parent,gui_parent=None):
        QtGui.QDialog.__init__(self, gui_parent)

        self.p = parent
        self.setupUi()
        self.plot_timer = QtCore.QTimer()
        self.check_timer = QtCore.QTimer() #Used to check if sweeps are still running

        self.setup_slots()
        self.plot_timer.start(100) #try and update every 0.1s
        self.check_timer.start(500) #only need the check every 0.5s
        self.run_type = {"ssa_iv" : 0,  "ssa_vphi" : 1,
                         "s2_iv" : 2, "s2_vphi" : 3,
                         "s1_iv" : 4, "s1_vphi" : 5,
                         "idle" : -1}

        self.good_colors = [Qt.Qt.white,Qt.Qt.cyan, Qt.Qt.red, Qt.Qt.green,Qt.Qt.magenta,Qt.Qt.gray]
        self.run_job = self.run_type["idle"]
        
    def setupUi(self):
        self.setWindowTitle("SQUID Control")
        self.tabWidget = QtGui.QTabWidget(self)

        self.ssa_widget = sweep_widget(self.tabWidget)
        self.tabWidget.addTab(self.ssa_widget, "SSA")
        self.s2_widget = sweep_widget(self.tabWidget)
        self.tabWidget.addTab(self.s2_widget, "S2")
        self.s1_widget = sweep_widget(self.tabWidget)
        self.tabWidget.addTab(self.s1_widget, "S1")
        
        #We also need a column for the SSA feedback PID loop
        self.pid_group = QtGui.QGroupBox("SSA PID")
        self.pid_layout = QtGui.QGridLayout()

        self.P_label = QtGui.QLabel("P")
        self.I_label = QtGui.QLabel("I")
        self.D_label = QtGui.QLabel("D")
        self.setpoint_label = QtGui.QLabel("Set")

        self.P_Input = QtGui.QDoubleSpinBox()
        self.P_Input.setRange(-2,2)
        self.I_Input = QtGui.QDoubleSpinBox()
        self.I_Input.setRange(-2,2)
        self.D_Input = QtGui.QDoubleSpinBox()
        self.D_Input.setRange(-2,2)
        self.setpoint_Input = QtGui.QDoubleSpinBox()
        self.setpoint_Input.setDecimals(3)

        self.pid_layout.addWidget(self.P_label,0,0,1,1)
        self.pid_layout.addWidget(self.I_label,1,0,1,1)
        self.pid_layout.addWidget(self.D_label,2,0,1,1)
        self.pid_layout.addWidget(self.setpoint_label,3,0,1,1)

        self.pid_layout.addWidget(self.P_Input,0,1,1,1)
        self.pid_layout.addWidget(self.I_Input,1,1,1,1)
        self.pid_layout.addWidget(self.D_Input,2,1,1,1)
        self.pid_layout.addWidget(self.setpoint_Input,3,1,1,1)

        self.SSA_FB_Button = QtGui.QPushButton("SSA Feedback")
        self.SSA_FB_Button.setCheckable(True)

        self.pid_layout.addWidget(self.SSA_FB_Button,4,0,1,-1)

        self.range_thermo = Qwt.QwtThermo()
        self.range_thermo.setOrientation(Qt.Qt.Vertical,Qwt.QwtThermo.LeftScale)
        self.range_thermo.setRange(-5.0,5.0)
        self.pid_layout.addWidget(self.range_thermo,5,0,1,-1)

        #Create a little group box with info
        self.info_group = QtGui.QGroupBox()
        self.info_layout = QtGui.QFormLayout()
        self.set_label = small_text("setpoint","blue")
        self.measure_label = small_text("measure","blue")
        self.error_label = small_text("error","blue")

        self.set_read_label = small_text("0.000","green")
        self.measure_read_label = small_text("0.000","green")
        self.error_read_label = small_text("0.000","red")

        self.info_layout.addRow(self.set_label, self.set_read_label)
        self.info_layout.addRow(self.measure_label, self.measure_read_label)
        self.info_layout.addRow(self.error_label, self.error_read_label)
        self.info_group.setLayout(self.info_layout)

        self.pid_layout.addWidget(self.info_group,6,0,1,-1)
        self.pid_group.setLayout(self.pid_layout)

        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.tabWidget)
        self.layout.addWidget(self.pid_group)
        self.setLayout(self.layout)

    def setup_curve(self):    
        self.vphi_curves = {} 
        self.ssa_current_curve = Qwt.QwtPlotCurve("Data")
        self.ssa_current_curve.attach(self.ssa_widget.ssa_plot.plot_region)
        self.ssa_current_curve.setPen(Qt.QPen(Qt.Qt.yellow))

    def setup_slots(self):
        QtCore.QObject.connect(self.ssa_widget.VIButton,QtCore.SIGNAL("clicked()"), self.run_ssa_VI)
        QtCore.QObject.connect(self.ssa_widget.VPhiButton,QtCore.SIGNAL("clicked()"), self.run_ssa_VPhi)
        QtCore.QObject.connect(self.plot_timer, QtCore.SIGNAL("timeout()"), self.update_plots)
        QtCore.QObject.connect(self.check_timer, QtCore.SIGNAL("timeout()"), self.check_status)
        QtCore.QObject.connect(self.SSA_FB_Button,QtCore.SIGNAL("toggled(bool)"), self.run_ssa_feedback)
        QtCore.QObject.connect(self.P_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.pid.setKp)
        QtCore.QObject.connect(self.I_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.pid.setKi)
        QtCore.QObject.connect(self.D_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.pid.setKd)
        QtCore.QObject.connect(self.setpoint_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.pid.setPoint)


    def update_plots(self):
        if self.run_job == self.run_type["ssa_iv"]:
            self.ssa_current_curve.setData(self.p.x_cont,self.p.y_cont)
            self.ssa_widget.ssa_plot.plot_region.replot()
        elif self.run_job == self.run_type["ssa_vphi"]:
            #Do dumb thing and update each curve
            #if available - burn those cpu cycles
            for s_bias in self.p.VPhi_data_x:
                if not self.vphi_curves.has_key(s_bias):
                    self.vphi_curves[s_bias] = Qwt.QwtPlotCurve(str(s_bias))
                    self.vphi_curves[s_bias].attach(self.ssa_widget.ssa_plot.plot_region)
                    color_index = len(self.vphi_curves) % len(self.good_colors)
                    self.vphi_curves[s_bias].setPen(self.good_colors[color_index])
                    self.vphi_curves[s_bias].setData(list(self.p.VPhi_data_x[s_bias]),list(self.p.VPhi_data_y[s_bias])) 

            #And also update the current curve
            self.ssa_current_curve.setData(self.p.x_cont,self.p.y_cont)
            self.ssa_widget.ssa_plot.plot_region.replot()
        #Update the status of the PID loop
        self.set_read_label.setText(str(self.p.pid.getPoint()))
        meas_size = len(self.p.adc_data.sa_ds) - 1
        meas_data = "%4.3f" % self.p.adc_data.sa_ds[meas_size]
        self.measure_read_label.setText(meas_data)
        error_data = "%4.3f" % self.p.pid.getError()
        self.error_read_label.setText(error_data)
        self.range_thermo.setValue(self.p.bb.registers["ssa_fb_voltage"])

    def run_ssa_feedback(self,state):
        #This starts the feedback loop on the SSA
        setpoint = self.setpoint_Input.value()
        P = self.P_Input.value()
        I = self.I_Input.value()
        D = self.D_Input.value()

        self.p.ssa_feedback_thread(setpoint,P,I,D)

    def check_status(self):
        #Simply check if the sweep_thread is alive 
        #and set the enable disable set
        state = not self.p.sweep_thread.isAlive() 
        self.ssa_widget.set_disable_all(state)
        self.s2_widget.set_disable_all(state)
        self.s1_widget.set_disable_all(state)

    def run_ssa_VPhi(self):
        self.ssa_widget.ssa_plot.plot_region.clear()
        self.setup_curve()
        self.run_job = self.run_type["ssa_vphi"]
        self.p.ssa_VPhi_thread(self.ssa_widget.fb_start_Input.value(),
                        self.ssa_widget.fb_stop_Input.value(),
                        self.ssa_widget.fb_step_Input.value(),
                        self.ssa_widget.bias_start_Input.value(),
                        self.ssa_widget.bias_stop_Input.value(),
                        self.ssa_widget.fb_count_Input.value())

    def run_ssa_VI(self):
        self.ssa_widget.ssa_plot.plot_region.clear()
        self.setup_curve()
        self.run_job = self.run_type["ssa_iv"]
        #This function takes a VI, either continously or a single shot
        #setup a curve on the plot
        if self.ssa_widget.continuous_check.isChecked() is True:
            count = -1;
        else:
            count = 1;
        print self.ssa_widget.bias_start_Input.value(),self.ssa_widget.bias_stop_Input.value(),self.ssa_widget.bias_step_Input.value(),  count
        self.p.ssa_iv_thread( self.ssa_widget.bias_start_Input.value(),
                                    self.ssa_widget.bias_stop_Input.value(),
                                    self.ssa_widget.bias_step_Input.value(),
                                    count)
        

class small_text(QtGui.QLabel):
     def __init__(self,text,color,gui_parent=None):
        QtGui.QLabel.__init__(self, gui_parent)
        self.setText(text)
        self.setFont(QtGui.QFont( "lucida", 10 ));
        color_string = "QLabel {color : %s;}" % color
        self.setStyleSheet(color_string);

