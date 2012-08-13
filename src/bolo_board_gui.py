from PyQt4 import QtCore, QtGui
#from control_ui import Ui_RawControl

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class bolo_board_gui(QtGui.QDialog):
    def __init__(self,parent,gui_parent=None):
        QtGui.QDialog.__init__(self, gui_parent)
        self.p = parent
        self.setupUi()
        self.sweep_timer = QtCore.QTimer()

        self.setup_slots()

    def setup_slots(self):
        #buttons
        QtCore.QObject.connect(self.ssa_bias_Button,QtCore.SIGNAL("toggled(bool)"), self.ssa_switch)
        QtCore.QObject.connect(self.ssa_bias_ext_Button,QtCore.SIGNAL("toggled(bool)"), self.ssa_ext_switch)
        QtCore.QObject.connect(self.ssa_fb_Button,QtCore.SIGNAL("toggled(bool)"), self.p.ssa_fb_switch)
        QtCore.QObject.connect(self.s2_bias_Button,QtCore.SIGNAL("toggled(bool)"), self.p.s2_bias_switch)
        QtCore.QObject.connect(self.s2_fb_Button,QtCore.SIGNAL("toggled(bool)"), self.p.s2_fb_switch)
        QtCore.QObject.connect(self.s1_bias_Button,QtCore.SIGNAL("toggled(bool)"), self.p.s1_bias_switch)
        QtCore.QObject.connect(self.s1_fb_Button,QtCore.SIGNAL("toggled(bool)"), self.s1_fb_m_switch)
        QtCore.QObject.connect(self.tes_bias_Button,QtCore.SIGNAL("toggled(bool)"), self.tes_switch)
        QtCore.QObject.connect(self.tes_bias_ext_Button,QtCore.SIGNAL("toggled(bool)"), self.tes_ext_switch)

        QtCore.QObject.connect(self.heater_switch,QtCore.SIGNAL("toggled(bool)"), self.run_heater_switch)
        QtCore.QObject.connect(self.heater_ext_switch,QtCore.SIGNAL("toggled(bool)"), self.run_heater_ext_switch)
        QtCore.QObject.connect(self.AUX_switch,QtCore.SIGNAL("toggled(bool)"), self.p.aux_switch)

        QtCore.QObject.connect(self.rs_channel_Button,QtCore.SIGNAL("clicked()"), self.set_rs)
        QtCore.QObject.connect(self.sweep_switch,QtCore.SIGNAL("clicked()"), self.sweep_pressed)
        QtCore.QObject.connect(self.zero_switch,QtCore.SIGNAL("toggled(bool)"), self.run_zero_switch)


        #voltages and RS
        QtCore.QObject.connect(self.ssa_bias_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.ssa_bias_voltage)
        QtCore.QObject.connect(self.ssa_fb_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.ssa_fb_voltage)
        QtCore.QObject.connect(self.s2_bias_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.s2_bias_voltage)
        QtCore.QObject.connect(self.s2_fb_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.s2_fb_voltage)
        QtCore.QObject.connect(self.s1_bias_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.rs_voltage)
        QtCore.QObject.connect(self.s1_fb_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.s1_fb_voltage)
        QtCore.QObject.connect(self.tes_bias_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.tes_voltage)

        QtCore.QObject.connect(self.heater_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.htr_voltage)
        QtCore.QObject.connect(self.AUX_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.aux_voltage)

        #PI Loop
        QtCore.QObject.connect(self.pgain_Input,QtCore.SIGNAL("currentIndexChanged(const QString)"), self.set_pgain)
        QtCore.QObject.connect(self.pgain_switch,QtCore.SIGNAL("toggled(bool)"), self.p.pgain_switch)
        QtCore.QObject.connect(self.Ims_Input,QtCore.SIGNAL("currentIndexChanged(const QString)"), self.set_tconst)
        QtCore.QObject.connect(self.Ims_switch,QtCore.SIGNAL("toggled(bool)"), self.p.tconst_switch)
        QtCore.QObject.connect(self.enablefb_switch,QtCore.SIGNAL("toggled(bool)"), self.Feedback_switch)
        QtCore.QObject.connect(self.shortint_switch,QtCore.SIGNAL("toggled(bool)"), self.p.short_int_switch)
        QtCore.QObject.connect(self.mod_type_cb,QtCore.SIGNAL("currentIndexChanged(const QString)"), self.mod_cb_changed)
        QtCore.QObject.connect(self.setpoint_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.pid_offset_voltage)

        #Connect the timer function to the update 
        QtCore.QObject.connect(self.sweep_timer, QtCore.SIGNAL("timeout()"), self.update_sweep)

    def run_zero_switch(self):
        #just run zero_voltages but need to do 
        #fancier stuff here
        self.p.zero_voltages()

    def set_pgain(self,gain):
        self.p.set_pgain(gain.toInt()[0])

    def set_tconst(self,gain):
        self.p.set_tconst(int(gain.toFloat()[0]*10 + 0.5))

    def update_sweep(self):
        value = self.p.sweep_progress
        self.sweep_pb.setValue(value)
        if value == -1:
            self.sweep_timer.stop()
            self.sweep_pb.setValue(100)

    def sweep_pressed(self):
        #Starts sweep and update timer for progress bar
        start = self.start_input.value()
        stop = self.stop_input.value()
        step = self.step_input.value()
        count = self.count_input.value()
        mod_type = str(self.mod_type_cb.currentText())
        name = str(self.sweep_cb.currentText())

        self.sweep_timer.start(500)
        self.p.wrapper_sweep_voltage(name,start,stop,step,count,mod_type)

    def set_rs(self):
        self.p.rs_channel(self.rs_channel_Input.value())

    #Interlock functions
    def tes_switch(self,state):
        if state is True:
            self.tes_bias_ext_Button.setChecked(False)
        self.p.tes_bias_switch(state)

    def tes_ext_switch(self,state):
        if state is True:
            self.tes_bias_Button.setChecked(False)
        self.p.tes_bias_ext_switch(state)

    def ssa_switch(self,state):
        if state is True:
            self.ssa_bias_ext_Button.setChecked(False)
        self.p.ssa_bias_switch(state)

    def ssa_ext_switch(self,state):
        if state is True:
            self.ssa_bias_Button.setChecked(False)
        self.p.ssa_bias_ext_switch(state)
 
    def s1_fb_m_switch(self,state):
        if state is True:
            self.enablefb_switch.setChecked(False)
        self.p.s1_fb_m_switch(state)

    def Feedback_switch(self,state):
        if state is True:
            self.s1_fb_Button.setChecked(False)
        self.p.s1_fb_switch(state)

    def run_heater_switch(self,state):
        if state is True:
            self.heater_ext_switch.setChecked(False)
        self.p.heater_switch(state)

    def run_heater_ext_switch(self,state):
        if state is True:
            self.heater_switch.setChecked(False)
        self.p.heater_ext_switch(state)

    def mod_cb_changed(self,name):
        if name == "sin":
            self.step_label.setText("Period")
            self.step_input.setDecimals(1)
            self.step_input.setRange(0,20)
            self.step_input.setValue(5)
            self.step_input.setSingleStep(0.1)
        else:
            self.step_label.setText("Step")
            self.step_input.setDecimals(3)
            self.step_input.setRange(-5,5)
            self.step_input.setValue(0.001)
            self.step_input.setSingleStep(0.001)

#Layout stuff here if you need it

    def setupUi(self):
        self.setWindowTitle("BOLO Control")
        self.bias_layout = QtGui.QGridLayout()
        self.bias_group = QtGui.QGroupBox("Bias Control")

        self.internal_label = QtGui.QLabel("Internal")
        self.external_label = QtGui.QLabel("External")
        self.bias_layout.addWidget(self.internal_label,0,2,1,1)
        self.bias_layout.addWidget(self.external_label,0,3,1,1)

        #Do the labels
        self.ssa_bias_label = QtGui.QLabel("SSA Bias")
        self.ssa_fb_label = QtGui.QLabel("SSA Fb")
        self.s2_bias_label = QtGui.QLabel("S2 Bias")
        self.s2_fb_label = QtGui.QLabel("S2 Fb")
        self.rs_channel_label = QtGui.QLabel("RS Channel")
        self.s1_bias_label = QtGui.QLabel("S1 Bias")
        self.s1_fb_label = QtGui.QLabel("S1 Fb")
        self.tes_bias_label = QtGui.QLabel("TES Bias")

        self.bias_layout.addWidget(self.ssa_bias_label,1,0,1,1)
        self.bias_layout.addWidget(self.ssa_fb_label,2,0,1,1)
        self.bias_layout.setRowMinimumHeight(3,15)
        self.bias_layout.setRowStretch(3,1)
        self.bias_layout.addWidget(self.s2_bias_label,4,0,1,1)
        self.bias_layout.addWidget(self.s2_fb_label,5,0,1,1)
        self.bias_layout.setRowMinimumHeight(6,15)
        self.bias_layout.setRowStretch(6,1)
        self.bias_layout.addWidget(self.rs_channel_label,7,0,1,1)
        self.bias_layout.addWidget(self.s1_bias_label,8,0,1,1)
        self.bias_layout.addWidget(self.s1_fb_label,9,0,1,1)
        self.bias_layout.setRowMinimumHeight(10,15)
        self.bias_layout.setRowStretch(10,1)
        self.bias_layout.addWidget(self.tes_bias_label,11,0,1,1)

        #Do the spin boxes
        self.ssa_bias_Input =  bolo_doubleInput()
        self.ssa_fb_Input = bolo_doubleInput()
        self.s2_bias_Input = bolo_doubleInput()
        self.s2_bias_Input.setSingleStep(0.01)
        self.s2_fb_Input = bolo_doubleInput()
        self.s1_bias_Input = bolo_doubleInput()
        self.s1_fb_Input = bolo_doubleInput()
        self.tes_bias_Input = bolo_doubleInput()
        self.rs_channel_Input = QtGui.QSpinBox()
        self.rs_channel_Input.setRange(0,33)

        self.bias_layout.addWidget(self.ssa_bias_Input,1,1,1,1)
        self.bias_layout.addWidget(self.ssa_fb_Input,2,1,1,1)
        self.bias_layout.addWidget(self.s2_bias_Input,4,1,1,1)
        self.bias_layout.addWidget(self.s2_fb_Input,5,1,1,1)
        self.bias_layout.addWidget(self.rs_channel_Input,7,1,1,1)
        self.bias_layout.addWidget(self.s1_bias_Input,8,1,1,1)
        self.bias_layout.addWidget(self.s1_fb_Input,9,1,1,1)
        self.bias_layout.addWidget(self.tes_bias_Input,11,1,1,1)
        

        #Now do the buttons and set them up here....
        self.ssa_bias_Button = bolo_switch(True)
        self.ssa_bias_ext_Button = bolo_switch(True)
        self.ssa_fb_Button = bolo_switch(True)
        self.s2_bias_Button = bolo_switch(True)
        self.s2_fb_Button = bolo_switch(True)
        self.rs_channel_Button = bolo_switch()
        self.s1_bias_Button = bolo_switch(True)
        self.s1_fb_Button = bolo_switch(True)
        self.tes_bias_Button = bolo_switch(True)
        self.tes_bias_ext_Button = bolo_switch(True)

        self.bias_layout.addWidget(self.ssa_bias_Button,1,2,1,1)
        self.bias_layout.addWidget(self.ssa_bias_ext_Button,1,3,1,1)      
        self.bias_layout.addWidget(self.ssa_fb_Button,2,2,1,1)    
        self.bias_layout.addWidget(self.s2_bias_Button,4,2,1,1)      
        self.bias_layout.addWidget(self.s2_fb_Button,5,2,1,1)       
        self.bias_layout.addWidget(self.rs_channel_Button,7,2,1,1)     
        self.bias_layout.addWidget(self.s1_bias_Button,8,2,1,1)       
        self.bias_layout.addWidget(self.s1_fb_Button,9,2,1,1)     
        self.bias_layout.addWidget(self.tes_bias_Button,11,2,1,1)    
        self.bias_layout.addWidget(self.tes_bias_ext_Button,11,3,1,1)
        
        self.zero_switch = bolo_switch(False,15,15,"Zero Voltages")
        self.bias_layout.addWidget(self.zero_switch,12,2,1,-1)

        self.bias_group.setLayout(self.bias_layout)

        #Now do the heater box
        self.heater_layout = QtGui.QGridLayout()
        self.heater_group = QtGui.QGroupBox("Heaters")

        self.heater_label = QtGui.QLabel("Heater")
        self.AUX_label = QtGui.QLabel("AUX")
        self.heater_layout.addWidget(self.heater_label,0,0,1,1)
        self.heater_layout.addWidget(self.AUX_label,1,0,1,1)

        self.heater_Input = bolo_doubleInput()
        self.AUX_Input = bolo_doubleInput() 
        self.heater_layout.addWidget(self.heater_Input,0,1,1,1)
        self.heater_layout.addWidget(self.AUX_Input,1,1,1,1)

        self.heater_switch = bolo_switch(True)
        self.heater_ext_switch = bolo_switch(True)
        self.AUX_switch = bolo_switch(True)
        self.heater_layout.addWidget(self.heater_switch,0,2,1,1)
        self.heater_layout.addWidget(self.heater_ext_switch,0,3,1,1)
        self.heater_layout.addWidget(self.AUX_switch,1,2,1,1)

        self.heater_group.setLayout(self.heater_layout)

        #Next the PI Loop
        self.pi_layout = QtGui.QGridLayout()
        self.pi_group = QtGui.QGroupBox("PI Loop")

        self.pgain_label = QtGui.QLabel("Prop Gain")
        self.Ims_label = QtGui.QLabel("Tc (ms)")
        self.setpoint_label = QtGui.QLabel("Setpoint")
        self.enablefb_label = QtGui.QLabel("Enable FB")
        self.shortint_label = QtGui.QLabel("Short Int")
        
        self.pi_layout.addWidget(self.pgain_label,0,0,1,1)
        self.pi_layout.addWidget(self.Ims_label,1,0,1,1)
        self.pi_layout.addWidget(self.setpoint_label,2,0,1,1)
        self.pi_layout.setRowMinimumHeight(3,15)
        self.pi_layout.addWidget(self.enablefb_label,4,1,1,1)
        self.pi_layout.addWidget(self.shortint_label,5,1,1,1)

        gains = [5,10,15,20,25,30,35,40,45,50,55,60,65,70,75]
        time_constants = [18.4,9.4,6.2,4.7,3.7,3.1,2.7]

        self.pgain_Input = QtGui.QComboBox()
        for g in gains:
            self.pgain_Input.addItem(str(g))
        self.Ims_Input = QtGui.QComboBox()
        for i in time_constants:
             self.Ims_Input.addItem(str(i))
        self.setpoint_Input = bolo_doubleInput()
        self.setpoint_Input.setDecimals(4)
        self.setpoint_Input.setSingleStep(0.0005)
        self.pi_layout.addWidget(self.pgain_Input,0,1,1,1)
        self.pi_layout.addWidget(self.Ims_Input,1,1,1,1)
        self.pi_layout.addWidget(self.setpoint_Input,2,1,1,1)

        self.pgain_switch =  bolo_switch(True)
        self.Ims_switch =  bolo_switch(True)
        self.enablefb_switch =  bolo_switch(True)
        self.shortint_switch =  bolo_switch(True)
        self.pi_layout.addWidget(self.pgain_switch,0,2,1,1)
        self.pi_layout.addWidget(self.Ims_switch,1,2,1,1)
        self.pi_layout.addWidget(self.enablefb_switch,4,2,1,1)
        self.pi_layout.addWidget(self.shortint_switch,5,2,1,1)

        self.pi_group.setLayout(self.pi_layout)

        #Add the sweep section
        self.sweep_layout = QtGui.QGridLayout()
        self.sweep_group = QtGui.QGroupBox("Sweep")

        self.start_label = QtGui.QLabel("Start")
        self.stop_label = QtGui.QLabel("Stop")
        self.step_label = QtGui.QLabel("Step")
        self.channel_label = QtGui.QLabel("channel")
        self.count_label = QtGui.QLabel("count")

        self.sweep_layout.addWidget(self.start_label,1,0,1,1)
        self.sweep_layout.addWidget(self.stop_label,1,1,1,1)
        self.sweep_layout.addWidget(self.step_label,1,2,1,1)
        self.sweep_layout.addWidget(self.channel_label,0,0,1,1)
        self.sweep_layout.addWidget(self.count_label,3,0,1,1)

        self.start_input = bolo_doubleInput()
        self.stop_input = bolo_doubleInput()
        self.step_input = bolo_doubleInput()
        self.start_input.setProperty("value", -5.0)
        self.stop_input.setProperty("value", 5.0)
        self.step_input.setProperty("value", 0.001)

        self.sweep_layout.addWidget(self.start_input,2,0,1,1)
        self.sweep_layout.addWidget(self.stop_input,2,1,1,1)
        self.sweep_layout.addWidget(self.step_input,2,2,1,1)

        sweep_inputs = ["ssa_bias", "ssa_fb", "s2_bias", "s2_fb", 
                        "s1_bias", "s1_fb", "tes_bias", "heater", "AUX"]
        self.sweep_cb = QtGui.QComboBox()
        self.sweep_switch = bolo_switch(False,15,15,"Start")
        for i in sweep_inputs:
            self.sweep_cb.addItem(i)            

        self.sweep_layout.addWidget(self.sweep_cb,0,1,1,1)
        self.sweep_layout.addWidget(self.sweep_switch,0,2,1,1)

        self.count_input = QtGui.QSpinBox()
        self.count_input.setRange(1,10)
        self.mod_type_cb  = QtGui.QComboBox()
        self.mod_type_cb.addItem("lin")
        self.mod_type_cb.addItem("saw")
        self.mod_type_cb.addItem("sin")

        self.sweep_pb = QtGui.QProgressBar()
        self.sweep_pb.setProperty("value", 0)

        self.sweep_layout.addWidget(self.count_input,3,1,1,1)
        self.sweep_layout.addWidget(self.mod_type_cb,3,2,1,1)
        self.sweep_layout.addWidget(self.sweep_pb,4,0,1,-1)

        self.sweep_group.setLayout(self.sweep_layout)

        #main layout section
        self.left_layout = QtGui.QVBoxLayout()
        self.left_layout.addWidget(self.heater_group)
        self.left_layout.addWidget(self.pi_group)
        self.left_layout.addWidget(self.sweep_group)

        self.main_layout = QtGui.QHBoxLayout()
        self.main_layout.addWidget(self.bias_group)
        self.main_layout.addLayout(self.left_layout)

      
        self.setLayout(self.main_layout)

class bolo_switch(QtGui.QPushButton):
    def __init__(self,checkable=False,ic_x=20,ic_y=20,text=None,gui_parent=None):
        QtGui.QPushButton.__init__(self, gui_parent)

        icon_switch = QtGui.QIcon()
        if checkable is True:
            icon_switch.addPixmap(QtGui.QPixmap("red_button.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            icon_switch.addPixmap(QtGui.QPixmap("green_button.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
            self.setCheckable(True)
        else:
            icon_switch.addPixmap(QtGui.QPixmap("blue_button.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        if text is not None:
            self.setText(text)


        self.setIcon(icon_switch)
        self.setIconSize(QtCore.QSize(ic_x,ic_y))

class bolo_doubleInput(QtGui.QDoubleSpinBox):
    def __init__(self,gui_parent=None):
        QtGui.QDoubleSpinBox.__init__(self, gui_parent)

        self.setRange(-5,4.999)
        self.setDecimals(3)
        self.setSingleStep(0.001)

   
