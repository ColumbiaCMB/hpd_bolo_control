#GUI to control fridge cycle and temperature setpoint
#Authors - Joshua Sobrin & Ross Williamson
#Last Date Modified - 8/27/2012

#Import modules
import sys
from PyQt4 import QtGui,QtCore
import pygcp.servers.sim900.sim900Client as sc
from time import sleep
import logging

class Fridge_GUI(QtGui.QDialog):

    def __init__(self, gui_parent=None):
        QtGui.QDialog.__init__(self, gui_parent)

        #Set Variables
        self.WAITTIME = 20
        self.TEMP_SETPOINT = 0.1

        #Set Flags
        self.REMAG = True
        self.RAMPING = 2 #(Don't Change This!)
        self.FULL_CYCLE = True

        #Set Parameters (These have already been tuned)
        self.RAMP_UP = 0.01
        self.RAMP_DOWN = 0.005
        self.MIN_CURR = 0.01
        self.MAX_CURR = 9.4
        self.MIN_OUTPUT = -10.0
        self.MAX_OUTPUT = 0.02
        self.RAMP_P_GAIN = -1.6
        self.REG_P_GAIN = -11.0
        self.I_GAIN = 0.07

        #Create methods to communicate with sim900, and connect to adc
        self.sim900 = sc.sim900Client(hostname="192.168.1.152")
        
        #setup log
        logging.basicConfig()
        self.logger = logging.getLogger('Fridge Cycle')
        self.logger.setLevel(logging.DEBUG)

        #Initialize GUI
        self.initUI()

    def initUI(self):
        #Create Window and its Geometry
        #Center Method is created at Line 224 to center window on screen
        self.setWindowTitle("Fridge Control")
        self.resize(700,500)
        self.center()

        #Create Groups
        self.setpoints_group = QtGui.QGroupBox("Setpoints")
        self.readings_group = QtGui.QGroupBox("Current Readings")
        self.PID_group = QtGui.QGroupBox("PID Control Settings")
        self.procedures_group = QtGui.QGroupBox("Procedures")
        self.status_group = QtGui.QGroupBox("Current Status")

        #Create Layouts
        self.setpoints_layout = QtGui.QGridLayout()
        self.readings_layout = QtGui.QGridLayout()
        self.PID_layout = QtGui.QGridLayout()
        self.procedures_layout = QtGui.QGridLayout()
        self.status_layout = QtGui.QGridLayout()

        #Create labels
        self.temp_setpoint_label = QtGui.QLabel("Temp (K)")
        self.current_setpoint_label = QtGui.QLabel("Current (A)")

        self.current_current_label = QtGui.QLabel("Current (A)")
        self.output_voltage_label = QtGui.QLabel("Output (V)")
        self.salt_temp_label = QtGui.QLabel("Salt Temp  (K)")
        self.PT4K_temp_label = QtGui.QLabel("4K-Stage Temp (K)")

        self.PID_state_label = QtGui.QLabel("PID State")
        self.ramp_state_label = QtGui.QLabel("Ramp State")
        self.ramp_rate_label = QtGui.QLabel("Ramp Rate")
        self.min_current_label = QtGui.QLabel("Min Current")
        self.max_current_label = QtGui.QLabel("Max Current")
        self.min_output_label = QtGui.QLabel("Min Ouput")
        self.max_output_label = QtGui.QLabel("Max Output")
        self.proportional_state_label = QtGui.QLabel("P-State")
        self.proportional_gain_label = QtGui.QLabel("P-Gain")
        self.integral_state_label = QtGui.QLabel("I-State")
        self.integral_gain_label = QtGui.QLabel("I-Gain")
        self.derivative_state_label = QtGui.QLabel("D-State")
        self.derivative_gain_label = QtGui.QLabel("D-Gain")

        self.status_label = QtGui.QLabel("Status")

        #Create value boxes

        #DoubleSpinBoxes are created to control setpoints
        #When setpoint values are set/changed, signals are automatically emitted
        #Signals are connected to slots on lines 234 and 237
        self.temp_setpoint_value = QtGui.QDoubleSpinBox(self)
        self.temp_setpoint_value.setRange(0.0,3.0)
        self.temp_setpoint_value.setSingleStep(0.1)
        self.temp_setpoint_value.setDecimals(3)
        self.temp_setpoint_value.valueChanged.connect(self.set_temp)
        self.current_setpoint_value = QtGui.QDoubleSpinBox(self)
        self.current_setpoint_value.setRange(0.0,9.4)
        self.current_setpoint_value.setSingleStep(0.1)
        self.current_setpoint_value.setDecimals(3)
        self.current_setpoint_value.valueChanged.connect(self.set_current)

        #All other value boxes are created as ReadOnly LineEdits
        #Values are inserted as procedures run
        self.current_current_value = QtGui.QLineEdit(self)
        self.current_current_value.setReadOnly(True)
        self.output_voltage_value = QtGui.QLineEdit(self)
        self.output_voltage_value.setReadOnly(True)
        self.salt_temp_value = QtGui.QLineEdit(self)
        self.salt_temp_value.setReadOnly(True)
        self.PT4K_temp_value = QtGui.QLineEdit(self)
        self.PT4K_temp_value.setReadOnly(True)

        self.PID_state_value = QtGui.QLineEdit(self)
        self.PID_state_value.setReadOnly(True)
        self.ramp_state_value = QtGui.QLineEdit(self)
        self.ramp_state_value.setReadOnly(True)
        self.ramp_rate_value = QtGui.QLineEdit(self)
        self.ramp_rate_value.setReadOnly(True)
        self.min_current_value = QtGui.QLineEdit(self)
        self.min_current_value.setReadOnly(True)
        self.max_current_value = QtGui.QLineEdit(self)
        self.max_current_value.setReadOnly(True)
        self.min_output_value = QtGui.QLineEdit(self)
        self.min_output_value.setReadOnly(True)
        self.max_output_value = QtGui.QLineEdit(self)
        self.max_output_value.setReadOnly(True)
        self.proportional_state_value = QtGui.QLineEdit(self)
        self.proportional_state_value.setReadOnly(True)
        self.proportional_gain_value = QtGui.QLineEdit(self)
        self.proportional_gain_value.setReadOnly(True)
        self.integral_state_value = QtGui.QLineEdit(self)
        self.integral_state_value.setReadOnly(True)
        self.integral_gain_value = QtGui.QLineEdit(self)
        self.integral_gain_value.setReadOnly(True)
        self.derivative_state_value = QtGui.QLineEdit(self)
        self.derivative_state_value.setReadOnly(True)
        self.derivative_gain_value = QtGui.QLineEdit(self)
        self.derivative_gain_value.setReadOnly(True)

        self.status_value = QtGui.QLineEdit(self)
        self.status_value.setReadOnly(True)
        self.status_value.setText("Ready")

        #Create Buttons For Custom and Full Procedures
        self.warmup_button = QtGui.QPushButton("Warm Up",self)
        self.warmup_button.clicked.connect(self.warmup)
        self.dumpheat_button = QtGui.QPushButton("Dump Heat",self)
        self.dumpheat_button.clicked.connect(self.dumpheat)
        self.cooldown_button = QtGui.QPushButton("Cool Down",self)
        self.cooldown_button.clicked.connect(self.cooldown)
        self.regulate_button = QtGui.QPushButton("Regulate",self)
        self.regulate_button.clicked.connect(self.regulate)
        self.monitor_button = QtGui.QPushButton("dummy",self)
        self.monitor_button.clicked.connect(self.dummyfunction)
        self.completecycle_button = QtGui.QPushButton("Complete Cycle",self)
        self.completecycle_button.clicked.connect(self.fullcycle)

        #Add Widgets to layout
        self.setpoints_layout.addWidget(self.temp_setpoint_label,0,0,1,1)
        self.setpoints_layout.addWidget(self.temp_setpoint_value,0,1,1,1)
        self.setpoints_layout.addWidget(self.current_setpoint_label,0,2,1,1)
        self.setpoints_layout.addWidget(self.current_setpoint_value,0,3,1,1)

        self.readings_layout.addWidget(self.current_current_label,0,0,1,1)
        self.readings_layout.addWidget(self.current_current_value,1,0,1,1)
        self.readings_layout.addWidget(self.output_voltage_label,0,1,1,1)
        self.readings_layout.addWidget(self.output_voltage_value,1,1,1,1)
        self.readings_layout.addWidget(self.salt_temp_label,0,2,1,1)
        self.readings_layout.addWidget(self.salt_temp_value,1,2,1,1)
        self.readings_layout.addWidget(self.PT4K_temp_label,0,3,1,1)
        self.readings_layout.addWidget(self.PT4K_temp_value,1,3,1,1)

        self.PID_layout.addWidget(self.PID_state_label,0,0,1,1)
        self.PID_layout.addWidget(self.PID_state_value,0,1,1,1)
        self.PID_layout.addWidget(self.ramp_state_label,1,0,1,1)
        self.PID_layout.addWidget(self.ramp_state_value,1,1,1,1)
        self.PID_layout.addWidget(self.ramp_rate_label,1,2,1,1)
        self.PID_layout.addWidget(self.ramp_rate_value,1,3,1,1)
        self.PID_layout.addWidget(self.min_current_label,2,0,1,1)
        self.PID_layout.addWidget(self.min_current_value,2,1,1,1)
        self.PID_layout.addWidget(self.max_current_label,2,2,1,1)
        self.PID_layout.addWidget(self.max_current_value,2,3,1,1)
        self.PID_layout.addWidget(self.min_output_label,3,0,1,1)
        self.PID_layout.addWidget(self.min_output_value,3,1,1,1)
        self.PID_layout.addWidget(self.max_output_label,3,2,1,1)
        self.PID_layout.addWidget(self.max_output_value,3,3,1,1)
        self.PID_layout.addWidget(self.proportional_state_label,4,0,1,1)
        self.PID_layout.addWidget(self.proportional_state_value,4,1,1,1)
        self.PID_layout.addWidget(self.proportional_gain_label,4,2,1,1)
        self.PID_layout.addWidget(self.proportional_gain_value,4,3,1,1)
        self.PID_layout.addWidget(self.integral_state_label,5,0,1,1)
        self.PID_layout.addWidget(self.integral_state_value,5,1,1,1)
        self.PID_layout.addWidget(self.integral_gain_label,5,2,1,1)
        self.PID_layout.addWidget(self.integral_gain_value,5,3,1,1)
        self.PID_layout.addWidget(self.derivative_state_label,6,0,1,1)
        self.PID_layout.addWidget(self.derivative_state_value,6,1,1,1)
        self.PID_layout.addWidget(self.derivative_gain_label,6,2,1,1)
        self.PID_layout.addWidget(self.derivative_gain_value,6,3,1,1)

        self.procedures_layout.addWidget(self.warmup_button,1,0,1,1)
        self.procedures_layout.addWidget(self.dumpheat_button,1,1,1,1)
        self.procedures_layout.addWidget(self.cooldown_button,1,2,1,1)
        self.procedures_layout.addWidget(self.regulate_button,1,3,1,1)
        self.procedures_layout.addWidget(self.monitor_button,1,4,1,1)
        self.procedures_layout.addWidget(self.completecycle_button,0,0,1,5)

        self.status_layout.addWidget(self.status_label,0,0,1,1)
        self.status_layout.addWidget(self.status_value,0,1,1,6)

        #Add layouts to group
        self.setpoints_group.setLayout(self.setpoints_layout)
        self.readings_group.setLayout(self.readings_layout)
        self.PID_group.setLayout(self.PID_layout)
        self.procedures_group.setLayout(self.procedures_layout)
        self.status_group.setLayout(self.status_layout)

        #Add groups to window
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.setpoints_group)
        vbox.addWidget(self.readings_group)
        vbox.addWidget(self.PID_group)
        vbox.addWidget(self.procedures_group)
        vbox.addWidget(self.status_group)

        self.setLayout(vbox)

        #Display Fridge Cycle Window
        #self.show()

        #Create Timer
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def center(self):
        #Creates a method for centering the Fridge Cycle GUI
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def set_current(self):
        #Sends command to change Current Setpoint
        self.sim900.setPIDSetpoint(self.current_setpoint_value.value())

    def set_temp(self):
        #Sends command to change Temperature Setpoint
        self.sim900.setSetpoint(self.temp_setpoint_value.value())

    def update(self):
        #Fetches values from sim900 and updates GUI values
        self.sim900.fetchDict()
        pid_output = self.sim900.data["pid_output_mon"]
        self.output_voltage_value.setText(str(pid_output))
        curr_now = self.sim900.data["pid_measure_mon"]
        self.current_current_value.setText(str(curr_now))
        temp_pil = self.sim900.data["bridge_temp_value"]
        self.salt_temp_value.setText(str(temp_pil))
        temp_fourk = self.sim900.data["therm_temperature"][2]
        self.PT4K_temp_value.setText(str(temp_fourk))
        #app.processEvents()
        #app.processEvents()

    def fullcycle(self):
        #Completes all 4 procedures, sequentially
        self.warmup()
        self.dumpheat()
        self.cooldown()
        self.regulate()

    def warmup(self):
        #We use this procedure to warm up the salt pills by increasing the magnetic field
        #We begin by killing off any residual Current, and then ramping up from 0.0 to 9.4, smoothly

        #First send commands to make sure that sim900 is set to sensible values
        self.status_value.setText("Setting sim900 to properly-tuned values")
        #app.processEvents()
        #app.processEvents()
        self.sim900.setLimLow(self.MIN_OUTPUT)
        self.min_output_value.setText(str(self.MIN_OUTPUT))
        self.sim900.setLimHigh(self.MAX_OUTPUT)
        self.max_output_value.setText(str(self.MAX_OUTPUT))
        self.min_current_value.setText(str(self.MIN_CURR))
        self.max_current_value.setText(str(self.MAX_CURR))
        self.sim900.setPropGain(self.RAMP_P_GAIN)
        self.proportional_gain_value.setText(str(self.RAMP_P_GAIN))
        self.sim900.setIntGain(self.I_GAIN)
        self.integral_gain_value.setText(str(self.I_GAIN))
        self.sim900.setPropOn(True)
        self.proportional_state_value.setText("ON")
        self.sim900.setIntOn(True)
        self.integral_state_value.setText("ON")
        self.sim900.setDerivOn(False)
        self.derivative_state_value.setText("OFF")
        self.derivative_gain_value.setText("N/A")
        self.sim900.setRampRate(self.RAMP_DOWN)
        self.ramp_rate_value.setText(str(self.RAMP_DOWN))
        self.sim900.setRampOn(False)
        self.ramp_state_value.setText("OFF")
        #app.processEvents()
        #app.processEvents()

        #Switch PID Output to Manual Mode
        self.status_value.setText("Switching PID to Manual Mode")
        #app.processEvents()
        #app.processEvents()
        self.sim900.fetchDict()
        pid_output = self.sim900.data["pid_output_mon"]
        self.sim900.setManualOutput(pid_output)
        self.output_voltage_value.setText(str(pid_output))
        self.sim900.setPIDControl(False)
        self.PID_state_value.setText("MANUAL")
        #app.processEvents()
        #app.processEvents()

        #Have user set PID input to measure Current
        response = ""
        while response != "yes":
            self.status_value.setText("Waiting for user to set PID input to measure Magnet Current")
            response = raw_input("Is the PID input set to measure Magnet Current? - Type 'yes' to continue: ")

        ##Have user power-up the heatswitch
        response = ""
        while response != "yes":
            sleep(3)
            self.update()
            self.status_value.setText("Waiting for user power-up the heatswitch")
            response = raw_input("Is the heatswitch powered-up? - Type 'yes' to continue: ")

        #Set the Current-Setpoint to current value to prevent jumping
        self.status_value.setText("Setting Current_Setpoint to current value")
        #app.processEvents()
        #app.processEvents()
        self.sim900.fetchDict()
        curr_now = self.sim900.data["pid_measure_mon"]
        self.current_setpoint_value.setValue(curr_now)
        self.sim900.setRampRate(self.RAMP_DOWN)
        self.ramp_rate_value.setText(str(self.RAMP_DOWN))
        self.sim900.setRampOn(True)
        self.ramp_state_value.setText("ON")
        #app.processEvents()
        #app.processEvents()

        #Set Current-Setpoint to 0.0, and then turn on the PID to begin ramping
        self.status_value.setText("Starting Rampdown to Zero Current")
        #app.processEvents()
        #app.processEvents()
        self.current_setpoint_value.setValue(0.0)
        self.sim900.setPIDControl(True)
        self.PID_state_value.setText("AUTO")
        #app.processEvents()
        #app.processEvents()

        #Wait until Current is below required value (MIN_CURR)
        self.sim900.fetchDict()
        curr_now = self.sim900.data["pid_measure_mon"]
        while curr_now > self.MIN_CURR:
            self.status_value.setText("Waiting for Current to fall below MIN_CURR")
            sleep(5)
            self.update()
            self.sim900.fetchDict()
            curr_now = self.sim900.data["pid_measure_mon"]
            disp_msg = "Current current : %f" % curr_now
            self.logger.info(disp_msg)

        #Once Current falls close enough to Zero, set Manual Output to Zero
        self.status_value.setText("Setting Manual Output to Zero")
        #app.processEvents()
        #app.processEvents()
        self.sim900.setRampOn(False)
        self.ramp_state_value.setText("OFF")
        self.sim900.setManualOutput(0.0)
        self.output_voltage_value.setText("0.0")
        self.sim900.setPIDControl(False)
        self.PID_state_value.setText("MANUAL")

        #Have user switch to Mag_Cycle
        response = ""
        while response != "yes":
            sleep(3)
            self.update()
            self.status_value.setText("Waiting for user to switch to Mag Cycle")
            #app.processEvents()
            #app.processEvents()
            response = raw_input("Is it switched to Mag Cycle? - Type 'yes' to continue: ")

        #Double-check that PID settings are correct for ramping up
        self.update()
        self.status_value.setText("Preparing to ramp up Current")
        #app.processEvents()
        #app.processEvents()
        self.current_setpoint_value.setValue(0.0)
        self.sim900.setRampRate(self.RAMP_UP)
        self.ramp_rate_value.setText(str(self.RAMP_UP))
        self.sim900.setRampOn(True)
        self.ramp_state_value.setText("ON")
        self.sim900.setPIDControl(True)
        self.PID_state_value.setText("AUTO")
        #app.processEvents()
        #app.processEvents()

        #Begin to ramp up Current to MAX_CURR
        self.update()
        self.status_value.setText("Ramping Current up to 9.4")
        #app.processEvents()
        #app.processEvents()
        self.current_setpoint_value.setValue(self.MAX_CURR)

        #If self.REMAG is set to "True", we will monitor when the salt temperature equals the 4K-stage temperature
        #Once the two temperatures are equal, we will close the heatswitch
        #This will allow the 4K-stage to absorb heat from the salts
        if self.REMAG is True:
            self.update()
            self.logger.info("Waiting for PIL temperature > PT 4K temp (about 2 min)")
            self.sim900.fetchDict()
            temp_pil = self.sim900.data["bridge_temp_value"]
            temp_fourk = self.sim900.data["therm_temperature"][2]
            while temp_pil < temp_fourk:
                self.status_value.setText("Waiting for salt temperature to exceed 4K-stage temperature")
                #app.processEvents()
                #app.processEvents()
                sleep(20)
                self.update()
                self.sim900.fetchDict()
                temp_pil = self.sim900.data["bridge_temp_value"]
                temp_fourk = self.sim900.data["therm_temperature"][2]
                disp_msg = "PIL Temp : %f, 4K Temp : %f " % (temp_pil,temp_fourk)
                self.logger.info(disp_msg)
            response = ""
            while response != "yes":
                sleep(3)
                self.update()
                self.status_value.setText("Waiting for user to close the heatswitch")
                #app.processEvents()
                #app.processEvents()
                response = raw_input("Is the heatswitch closed? - Type 'yes' to continue: ")

        #When the PID is ramping, the ramp_status = 2
        #Therefore, when the ramp_status no longer equals 2, we know that we are very close to our Current Setpoint
        self.update()
        self.sim900.fetchDict()
        ramp_status = self.sim900.data["pid_ramp_status"]
        curr_now = self.sim900.data["pid_measure_mon"]
        while ramp_status == self.RAMPING:
            self.status_value.setText("Ramping Current up to 9.4")
            #app.processEvents()
            #app.processEvents()
            sleep(60)
            self.update()
            self.sim900.fetchDict()
            ramp_status = self.sim900.data["pid_ramp_status"]
            curr_now = self.sim900.data["pid_measure_mon"]
            disp_msg = "Ramping Current to %f, Now at %f" % (self.MAX_CURR,curr_now)
            self.logger.info(disp_msg)

        #Open and Close heat switch to relieve mechanical stresses
        response = ""
        while response != "yes":
                sleep(3)
                self.update()
                self.status_value.setText("Waiting for user to open then close heatswitch")
                #app.processEvents()
                #app.processEvents()
                response = raw_input("Has the heatswitch been opened, then closed? - Type 'yes' to continue: ")

        #Tell user that warmup procedure is complete
        self.logger.info("Magup Cycle Complete")
        self.status_value.setText("Warmup is Complete!")

    def dumpheat(self):
        #We use this procedure to wait the required amount of time
        #This allows the salt pills to dump heat onto the 4K-stage
        #If we want to wait longer than 30 minutes, we open and close the heatswitch
        #This is done to relieve mechanical stresses
        #Heatswitch should be operated 30 minutes prior to cooling down

        if self.FULL_CYCLE != True:
            #First send commands to make sure that sim900 is set to sensible values
            self.status_value.setText("Setting sim900 to properly-tuned values")
            #app.processEvents()
            #app.processEvents()
            self.sim900.setLimLow(self.MIN_OUTPUT)
            self.min_output_value.setText(str(self.MIN_OUTPUT))
            self.sim900.setLimHigh(self.MAX_OUTPUT)
            self.max_output_value.setText(str(self.MAX_OUTPUT))
            self.min_current_value.setText(str(self.MIN_CURR))
            self.max_current_value.setText(str(self.MAX_CURR))
            self.sim900.setPropGain(self.RAMP_P_GAIN)
            self.proportional_gain_value.setText(str(self.RAMP_P_GAIN))
            self.sim900.setIntGain(self.I_GAIN)
            self.integral_gain_value.setText(str(self.I_GAIN))
            self.sim900.setPropOn(True)
            self.proportional_state_value.setText("ON")
            self.sim900.setIntOn(True)
            self.integral_state_value.setText("ON")
            self.sim900.setDerivOn(False)
            self.derivative_state_value.setText("OFF")
            self.derivative_gain_value.setText("N/A")
            self.sim900.setRampRate(self.RAMP_UP)
            self.ramp_rate_value.setText(str(self.RAMP_UP))
            self.sim900.setRampOn(True)
            self.ramp_state_value.setText("ON")
            self.current_setpoint_value.setValue(self.MAX_CURR)
            self.sim900.setPIDControl(True)
            self.PID_state_value.setText("AUTO")
            #app.processEvents()
            #app.processEvents()
            
            #Make sure heatswitch is closed
            response = ""
            while response != "yes":
                sleep(3)
                self.update()
                self.status_value.setText("Waiting for user to check heatswitch")
                #app.processEvents()
                #app.processEvents()
                response = raw_input("Is the heatswitch closed? - Type 'yes' to continue: ")

        #Check to see whether it will be necessary to operate the heatswitch
        self.update()
        self.status_value.setText("Initiating Dump Heat Procedure")
        #app.processEvents()
        #app.processEvents()
        pre_wait_time = self.WAITTIME - 30
        if pre_wait_time < 0:
            self.logger.info("Wait time is less than 30 min... Don't operate the heatswitch")
            pre_wait_time = self.WAITTIME
            post_wait_time = 0
        else:
            post_wait_time = 30

        #Handle case in which user did not have to operate heatswitch
        #IMPORTANT: Even if user has to operate heatswitch, the execution passes through this section,
        #           just with a pre_wait_time equal to the total wait time minus 30
        for i in xrange(pre_wait_time):
            self.update()
            self.status_value.setText("Dumping heat... %f complete" % (i*100.0/self.WAITTIME))
            #app.processEvents()
            #app.processEvents()
            disp_msg = "Waiting %i of %i minutes... %f complete" % (i,self.WAITTIME,i*100.0/self.WAITTIME)
            self.logger.info(disp_msg)
            sleep(60)

        #Handle case in which user has to operate heatswitch
        #Execution only pases through this section if self.WAITTIME was greater than 30
        if post_wait_time != 0:
            response = ""
            while response != "yes":
                sleep(3)
                self.update()
                self.status_value.setText("Waiting for user to open then close heatswitch")
                #app.processEvents()
                #app.processEvents()
                response = raw_input("Has the heatswitch been opened, then closed? - Type 'yes' to continue: ")

            for i in xrange(pre_wait_time,self.WAITTIME):
                self.update()
                self.status_value.setText("Dumping heat... %5.2f complete" % (i*100.0/self.WAITTIME))
                #app.processEvents()
                #app.processEvents()
                disp_msg = "Waiting %i of %i minutes... %5.2f complete" % (i,self.waittime,i*100.0/self.WAITTIME)
                self.logger.info(disp_msg)
                sleep(60)

        #Tell user that dumpheat procedure is complete
        self.logger.info("Wait period over - Demag when ready")
        self.status_value.setText("Finished dumping heat!")
        #app.processEvents()
        #app.processEvents()

    def cooldown(self):
        #This procedure slowly ramps down the Magnet Current to 0.0
        #We go all the way to zero because before regulating the temperature, we will need to change resistors
        #For this reason, we go all the way to 0.0 current, and then we'll increase the current slowly during the regulate procedure

        #Make sure that the heatswitch has been opened
        response = ""
        while response != "yes":
                sleep(3)
                self.update()
                self.status_value.setText("Waiting for user to open heatswitch")
                #app.processEvents()
                #app.processEvents()
                response = raw_input("Has the heatswitch been opened? - Type 'yes' to continue: ")

        #Make sure that sim900 is set to sensible values
        self.status_value.setText("Setting sim900 to properly-tuned values")
        #app.processEvents()
        #app.processEvents()
        self.sim900.setLimLow(self.MIN_OUTPUT)
        self.min_output_value.setText(str(self.MIN_OUTPUT))
        self.sim900.setLimHigh(self.MAX_OUTPUT)
        self.max_output_value.setText(str(self.MAX_OUTPUT))
        self.min_current_value.setText(str(self.MIN_CURR))
        self.max_current_value.setText(str(self.MAX_CURR))
        self.sim900.setPropGain(self.RAMP_P_GAIN)
        self.proportional_gain_value.setText(str(self.RAMP_P_GAIN))
        self.sim900.setIntGain(self.I_GAIN)
        self.integral_gain_value.setText(str(self.I_GAIN))
        self.sim900.setPropOn(True)
        self.proportional_state_value.setText("ON")
        self.sim900.setIntOn(True)
        self.integral_state_value.setText("ON")
        self.sim900.setDerivOn(False)
        self.derivative_state_value.setText("OFF")
        self.derivative_gain_value.setText("N/A")
        #app.processEvents()
        #app.processEvents()

        #Set PID to ramp Current down to 0.0
        self.update()
        self.status_value.setText("Beginning to ramp down Current to 0.0")
        #app.processEvents()
        #app.processEvents()
        self.sim900.fetchDict()
        faa_pil_temp = self.sim900.data["bridge_temp_value"]
        self.sim900.setRampRate(self.RAMP_DOWN)
        self.ramp_rate_value.setText(str(self.RAMP_DOWN))
        self.sim900.setRampOn(True)
        self.ramp_state_value.setText("ON")
        self.sim900.setPIDControl(True)
        self.PID_state_value.setText("AUTO")
        self.current_setpoint_value.setValue(0.0)
        #app.processEvents()
        #app.processEvents()

        #We can check whether we are close to 0.0 Current by checking the ramp_status
        self.update()
        self.sim900.fetchDict()
        ramp_status = self.sim900.data["pid_ramp_status"]
        curr_now = self.sim900.data["pid_measure_mon"]
        while ramp_status == self.RAMPING:
            self.status_value.setText("Ramping Current down to 0.0")
            #app.processEvents()
            #app.processEvents()
            sleep(60)
            self.update()
            self.sim900.fetchDict()
            ramp_status = self.sim900.data["pid_ramp_status"]
            curr_now = self.sim900.data["pid_measure_mon"]
            disp_msg = "Ramping to %f, Now at %f" % (self.MIN_CURR,curr_now)
            self.logger.info(disp_msg)

        #And now doublecheck that the current is actually zero
        self.update()
        self.sim900.fetchDict()
        curr_now = self.sim900.data["pid_measure_mon"]
        while curr_now > self.MIN_CURR:
            self.status_value.setText("Checking to make sure Current is below MIN_CURR")
            #app.processEvents()
            #app.processEvents()
            sleep(5)
            self.update()
            self.sim900.fetchDict()
            curr_now = self.sim900.data["pid_measure_mon"]
            disp_msg = "Current current : %f" % curr_now
            self.logger.info(disp_msg)

        #Set manual output to Zero
        self.sim900.setRampOn(False)
        self.ramp_state_value.setText("OFF")
        self.sim900.setManualOutput(0.0)
        self.output_voltage_value.setText(0.0)
        self.sim900.setPIDControl(False)
        self.PID_state_value.setText("MANUAL")
        #app.processEvents()
        #app.processEvents()

        #Notify user that cooldown procedure is complete
        self.logger.info("Demag Complete")
        self.status_value.setText("Finished Cooling Down!")
        #app.processEvents()
        #app.processEvents()

    def regulate(self):
        #In this procedure, we maintain the temperature setpoint of the salt pills
        #This requires us to first change some settings manually
        #We then tell the PID to maintain a temperature setpoint

        self.update()

        #Disconnect heatswitchpower to cut down on noise
        response = ""
        while response != "yes":
                sleep(3)
                self.status_value.setText("Waiting for user to disconnect heatswitch power")
                #app.processEvents()
                #app.processEvents()
                response = raw_input("Is the heatswitch powered down and disconnected? - Type 'yes' to continue: ")

        #Switch PID input to measure Bridge(salt) temperature
        response = ""
        while response != "yes":
                sleep(3)
                self.status_value.setText("Waiting for user to to set PID input to measure Bridge Temperature")
                #app.processEvents()
                #app.processEvents()
                response = raw_input("Is the PID input set to measure Bridge Temperature? - Type 'yes' to continue: ")

        #Switch to Regulate
        response = ""
        while response != "yes":
                sleep(3)
                self.status_value.setText("Waiting for user to switch to Regulate")
                #app.processEvents()
                #app.processEvents()
                response = raw_input("Is it switched to Regulate? - Type 'yes' to continue: ")

        #Set PID to begin regulating bridge temperature
        self.update()
        self.sim900.setRampOn(False)
        self.ramp_state_value.setText("OFF")
        self.sim900.setPropGain(self.REG_P_GAIN)
        self.proportional_gain_value.setText(str(self.REG_P_GAIN))
        self.temp_setpoint_value.setValue(self.SETPOINT)
        self.sim900.setPIDControl(True)
        self.PID_state_value.setText("AUTO")
        #app.processEvents()
        #app.processEvents()

        #Notify user that the PID is now regulating temperature
        self.logger.info("Now Regulating")
        self.status_value.setText("Now regulating salt temperature")
        #app.processEvents()
        #app.processEvents()

        #Update GUI every 5 seconds
        response = ""
        while response != "yes":
            sleep(5)
            self.update()
            #app.processEvents()
            #app.processEvents()
            response = raw_input("Are you finished regulating? - Type 'yes' to terminate procedure: ")

    def dummyfunction(self):
        self.status_value.setText("starting dummy function")
        print str(self.status_value.text())
        #app.processEvents()
        #app.processEvents()
        sleep(2)
        for i in xrange(1,4):
            self.status_value.setText("doing dummy function %i" % (i))
            print str(self.status_value.text())
            #app.processEvents()
            #app.processEvents()
            sleep(2)
        self.status_value.setText("Ready")

#app = QtGui.QApplication(sys.argv)

def main():
    app = QtGui.QApplication(sys.argv)
    fg = Fridge_GUI()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
