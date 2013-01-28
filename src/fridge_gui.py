#GUI to control HPD fridge, cycles, and setpoints
#Designed to be a a child of bolo_main.py
#Authors - Joshua Sobrin & Glenn Jones
#Last Date Modified - 10/10/12

#Import modules
import sys
from PyQt4 import QtGui, QtCore, Qt
import pygcp.servers.sim900.sim900Client as sc
from time import sleep
from plot_template import plot_template
import PyQt4.Qwt5 as Qwt
from numpy import arange

class fridge_gui(QtGui.QDialog):

    def __init__(self, simclient=None, gui_parent=None):
        QtGui.QDialog.__init__(self, gui_parent)
        if simclient is None:
            self.sim900 = sc.sim900Client(hostname="192.168.1.152")
        else:
            self.sim900 = simclient
        self.setupUI()
        self.setupList()
        self.setupPlot()
        self.setupSlots()
        self.setupTimer()

        #Creates an empty dictionary for data_logging, fetches sim900 data, and then updates the dictionary
        #This is the dictionary that is looked at by data_logging
        #The timer triggers the update method, which updates this dictionary
        self.registers = {}
        self.sim900.fetchDict()
        self.registers.update(self.sim900.data)

    def setupUI(self):
        #Create Window and its Geometry
        self.setWindowTitle("Fridge Controls")
        self.resize(1200,550)
        self.centerUI()
        self.organizeUI()

    def centerUI(self):
        #Centers the GUI on the screen
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def organizeUI(self):
        #Create Widgets
        self.top_widget = QtGui.QTabWidget()
        self.readings_widget = QtGui.QWidget()
        self.commands_widget = QtGui.QWidget()
        self.bottom_widget = QtGui.QWidget()

        #Create Groups
        self.measurements_group = QtGui.QGroupBox("Measurements")
        self.pid_readout_group = QtGui.QGroupBox("PID Readout")
        self.procedures_group = QtGui.QGroupBox("Procedures")
        self.pid_commands_group = QtGui.QGroupBox("PID Commands")
        self.plot_group = QtGui.QGroupBox("Temperature v. Time")

        #Create Layouts
        self.measurements_layout = QtGui.QGridLayout()
        self.pid_readout_layout = QtGui.QGridLayout()
        self.procedures_layout = QtGui.QVBoxLayout()
        self.pid_commands_layout = QtGui.QGridLayout()
        self.plot_layout = QtGui.QGridLayout()

        #Create Labels
        self.bridge_setpoint_label = QtGui.QLabel("Bridge Setpoint")
        self.bridge_setpoint_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.temp_bridge_label = QtGui.QLabel("Bridge Temperature")
        self.temp_bridge_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.temp_3K_label = QtGui.QLabel("3K Temperature")
        self.temp_3K_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.temp_50K_label = QtGui.QLabel("50K Temperature")
        self.temp_50K_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.current_label = QtGui.QLabel("Magnet Current")
        self.current_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)

        self.setpoint_readout_label = QtGui.QLabel("Setpoint")
        self.setpoint_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.measure_readout_label = QtGui.QLabel("Measure")
        self.measure_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.error_readout_label = QtGui.QLabel("Error")
        self.error_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.output_readout_label = QtGui.QLabel("Output")
        self.output_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.p_status_readout_label = QtGui.QLabel("P-Status")
        self.p_status_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.i_status_readout_label = QtGui.QLabel("I-Status")
        self.i_status_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.d_status_readout_label = QtGui.QLabel("D-Status")
        self.d_status_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.o_status_readout_label = QtGui.QLabel("Offset Status")
        self.o_status_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.p_gain_readout_label = QtGui.QLabel("P-Gain")
        self.p_gain_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.i_gain_readout_label = QtGui.QLabel("I-Gain")
        self.i_gain_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.d_gain_readout_label = QtGui.QLabel("D-Gain")
        self.d_gain_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.o_readout_label = QtGui.QLabel("Offset")
        self.o_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.ramp_readout_label = QtGui.QLabel("Ramping")
        self.ramp_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.ramp_rate_readout_label = QtGui.QLabel("Ramp Rate")
        self.ramp_rate_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.ramp_status_readout_label = QtGui.QLabel("Ramp Status")
        self.ramp_status_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.pid_status_readout_label = QtGui.QLabel("PID Control")
        self.pid_status_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.manual_output_readout_label = QtGui.QLabel("Manual Output")
        self.manual_output_readout_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)

        self.bridge_setpoint_command_label = QtGui.QLabel("Bridge Setpoint (Direct)")
        self.bridge_setpoint_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.pid_setpoint_command_label = QtGui.QLabel("PID Setpoint")
        self.pid_setpoint_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.pid_status_command_label = QtGui.QLabel("PID Status")
        self.pid_status_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.manual_output_command_label = QtGui.QLabel("Manual Output")
        self.manual_output_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.ramp_command_label = QtGui.QLabel("Ramping")
        self.ramp_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.ramp_rate_command_label = QtGui.QLabel("Ramp Rate")
        self.ramp_rate_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.p_status_command_label = QtGui.QLabel("Proportional Status")
        self.p_status_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.i_status_command_label = QtGui.QLabel("Integral Status")
        self.i_status_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.d_status_command_label = QtGui.QLabel("Derivative Status")
        self.d_status_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.o_status_command_label = QtGui.QLabel("Offset Status")
        self.o_status_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.p_gain_command_label = QtGui.QLabel("Proportional Gain")
        self.p_gain_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.i_gain_command_label = QtGui.QLabel("Integral Gain")
        self.i_gain_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.d_gain_command_label = QtGui.QLabel("Derivative Gain")
        self.d_gain_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.o_command_label = QtGui.QLabel("Offset")
        self.o_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)

        self.status_label = QtGui.QLabel("Status:")
        self.status_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.status_bridge_setpoint_command_label = QtGui.QLabel("Bridge Setpoint Control:")
        self.status_bridge_setpoint_command_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)

        #Create Value Boxes
        self.bridge_setpoint_value = QtGui.QLineEdit()
        self.bridge_setpoint_value.setReadOnly(True)
        self.temp_bridge_value = QtGui.QLineEdit()
        self.temp_bridge_value.setReadOnly(True)
        self.temp_3K_value = QtGui.QLineEdit()
        self.temp_3K_value.setReadOnly(True)
        self.temp_50K_value = QtGui.QLineEdit()
        self.temp_50K_value.setReadOnly(True)
        self.current_value = QtGui.QLineEdit()
        self.current_value.setReadOnly(True)

        self.setpoint_readout_value = QtGui.QLineEdit()
        self.setpoint_readout_value.setReadOnly(True)
        self.measure_readout_value = QtGui.QLineEdit()
        self.measure_readout_value.setReadOnly(True)
        self.error_readout_value = QtGui.QLineEdit()
        self.error_readout_value.setReadOnly(True)
        self.output_readout_value = QtGui.QLineEdit()
        self.output_readout_value.setReadOnly(True)
        self.p_status_readout_value = QtGui.QLineEdit()
        self.p_status_readout_value.setReadOnly(True)
        self.i_status_readout_value = QtGui.QLineEdit()
        self.i_status_readout_value.setReadOnly(True)
        self.d_status_readout_value = QtGui.QLineEdit()
        self.d_status_readout_value.setReadOnly(True)
        self.o_status_readout_value = QtGui.QLineEdit()
        self.o_status_readout_value.setReadOnly(True)
        self.p_gain_readout_value = QtGui.QLineEdit()
        self.p_gain_readout_value.setReadOnly(True)
        self.i_gain_readout_value = QtGui.QLineEdit()
        self.i_gain_readout_value.setReadOnly(True)
        self.d_gain_readout_value = QtGui.QLineEdit()
        self.d_gain_readout_value.setReadOnly(True)
        self.o_readout_value = QtGui.QLineEdit()
        self.o_readout_value.setReadOnly(True)
        self.ramp_readout_value = QtGui.QLineEdit()
        self.ramp_readout_value.setReadOnly(True)
        self.ramp_rate_readout_value = QtGui.QLineEdit()
        self.ramp_rate_readout_value.setReadOnly(True)
        self.ramp_status_readout_value = QtGui.QLineEdit()
        self.ramp_status_readout_value.setReadOnly(True)
        self.pid_status_readout_value = QtGui.QLineEdit()
        self.pid_status_readout_value.setReadOnly(True)
        self.manual_output_readout_value = QtGui.QLineEdit()
        self.manual_output_readout_value.setReadOnly(True)

        self.enabled_command_check = QtGui.QCheckBox("Enabled")
        self.enabled_command_check.setChecked(False)
        self.bridge_setpoint_command_value = QtGui.QDoubleSpinBox()
        self.bridge_setpoint_command_value.setEnabled(False)
        self.bridge_setpoint_command_value.setRange(0.0,0.5)
        self.bridge_setpoint_command_value.setSingleStep(0.1)
        self.bridge_setpoint_command_value.setDecimals(6)
        self.pid_setpoint_command_value = QtGui.QDoubleSpinBox()
        self.pid_setpoint_command_value.setEnabled(False)
        self.pid_setpoint_command_value.setRange(0.0,9.4)
        self.pid_setpoint_command_value.setSingleStep(0.1)
        self.pid_setpoint_command_value.setDecimals(3)
        self.pid_status_command_value = QtGui.QComboBox()
        self.pid_status_command_value.setEnabled(False)
        self.pid_status_command_value.addItem(" ")
        self.pid_status_command_value.addItem("ON")
        self.pid_status_command_value.addItem("OFF")
        self.manual_output_command_value = QtGui.QDoubleSpinBox()
        self.manual_output_command_value.setEnabled(False)
        self.manual_output_command_value.setRange(-10.0,0.02)
        self.manual_output_command_value.setSingleStep(0.1)
        self.manual_output_command_value.setDecimals(3)
        self.ramp_command_value = QtGui.QComboBox()
        self.ramp_command_value.setEnabled(False)
        self.ramp_command_value.addItem(" ")
        self.ramp_command_value.addItem("ON")
        self.ramp_command_value.addItem("OFF")
        self.ramp_rate_command_value = QtGui.QDoubleSpinBox()
        self.ramp_rate_command_value.setEnabled(False)
        self.ramp_rate_command_value.setRange(0.0,0.01)
        self.ramp_rate_command_value.setSingleStep(0.001)
        self.ramp_rate_command_value.setDecimals(3)
        self.p_status_command_value = QtGui.QComboBox()
        self.p_status_command_value.setEnabled(False)
        self.p_status_command_value.addItem(" ")
        self.p_status_command_value.addItem("ON")
        self.p_status_command_value.addItem("OFF")
        self.i_status_command_value = QtGui.QComboBox()
        self.i_status_command_value.setEnabled(False)
        self.i_status_command_value.addItem(" ")
        self.i_status_command_value.addItem("ON")
        self.i_status_command_value.addItem("OFF")
        self.d_status_command_value = QtGui.QComboBox()
        self.d_status_command_value.setEnabled(False)
        self.d_status_command_value.addItem(" ")
        self.d_status_command_value.addItem("ON")
        self.d_status_command_value.addItem("OFF")
        self.o_status_command_value = QtGui.QComboBox()
        self.o_status_command_value.setEnabled(False)
        self.o_status_command_value.addItem(" ")
        self.o_status_command_value.addItem("ON")
        self.o_status_command_value.addItem("OFF")
        self.p_gain_command_value = QtGui.QDoubleSpinBox()
        self.p_gain_command_value.setEnabled(False)
        self.p_gain_command_value.setRange(-15.0,15.0)
        self.p_gain_command_value.setSingleStep(0.1)
        self.i_gain_command_value = QtGui.QDoubleSpinBox()
        self.i_gain_command_value.setEnabled(False)
        self.i_gain_command_value.setRange(-15.0,15.0)
        self.i_gain_command_value.setSingleStep(0.1)
        self.d_gain_command_value = QtGui.QDoubleSpinBox()
        self.d_gain_command_value.setEnabled(False)
        self.d_gain_command_value.setRange(-15.0,15.0)
        self.d_gain_command_value.setSingleStep(0.1)
        self.o_command_value = QtGui.QDoubleSpinBox()
        self.o_command_value.setEnabled(False)
        self.o_command_value.setRange(-15.0,15.0)
        self.o_command_value.setSingleStep(0.1)

        self.status_value = QtGui.QLineEdit()
        self.status_value.setReadOnly(True)
        self.status_value.setText("Ready")
        self.status_bridge_setpoint_command_value = QtGui.QDoubleSpinBox()
        self.status_bridge_setpoint_command_value.setEnabled(True)
        self.status_bridge_setpoint_command_value.setRange(0.0,0.5)
        self.status_bridge_setpoint_command_value.setSingleStep(0.1)
        self.status_bridge_setpoint_command_value.setDecimals(6)

        #Create PushButtons
        self.setup_button = QtGui.QPushButton("Set Up")
        self.warmup_button = QtGui.QPushButton("Warm Up")
        self.dumpheat_button = QtGui.QPushButton("Dump Heat")
        self.cooldown_button = QtGui.QPushButton("Cool Down")
        self.regulate_button = QtGui.QPushButton("Regulate")

        #Create Plot Background
        self.temp_plot = plot_template()

        #Add Objects to Layouts
        self.measurements_layout.addWidget(self.bridge_setpoint_label,0,0,1,1)
        self.measurements_layout.addWidget(self.bridge_setpoint_value,0,1,1,1)
        self.measurements_layout.addWidget(self.temp_bridge_label,1,0,1,1)
        self.measurements_layout.addWidget(self.temp_bridge_value,1,1,1,1)
        self.measurements_layout.addWidget(self.temp_3K_label,2,0,1,1)
        self.measurements_layout.addWidget(self.temp_3K_value,2,1,1,1)
        self.measurements_layout.addWidget(self.temp_50K_label,3,0,1,1)
        self.measurements_layout.addWidget(self.temp_50K_value,3,1,1,1)
        self.measurements_layout.addWidget(self.current_label,4,0,1,1)
        self.measurements_layout.addWidget(self.current_value,4,1,1,1)

        self.pid_readout_layout.addWidget(self.setpoint_readout_label,0,0,1,1)
        self.pid_readout_layout.addWidget(self.setpoint_readout_value,0,1,1,1)
        self.pid_readout_layout.addWidget(self.measure_readout_label,0,2,1,1)
        self.pid_readout_layout.addWidget(self.measure_readout_value,0,3,1,1)
        self.pid_readout_layout.addWidget(self.error_readout_label,0,4,1,1)
        self.pid_readout_layout.addWidget(self.error_readout_value,0,5,1,1)
        self.pid_readout_layout.addWidget(self.output_readout_label,0,6,1,1)
        self.pid_readout_layout.addWidget(self.output_readout_value,0,7,1,1)
        self.pid_readout_layout.addWidget(self.p_status_readout_label,1,0,1,1)
        self.pid_readout_layout.addWidget(self.p_status_readout_value,1,1,1,1)
        self.pid_readout_layout.addWidget(self.i_status_readout_label,1,2,1,1)
        self.pid_readout_layout.addWidget(self.i_status_readout_value,1,3,1,1)
        self.pid_readout_layout.addWidget(self.d_status_readout_label,1,4,1,1)
        self.pid_readout_layout.addWidget(self.d_status_readout_value,1,5,1,1)
        self.pid_readout_layout.addWidget(self.o_status_readout_label,1,6,1,1)
        self.pid_readout_layout.addWidget(self.o_status_readout_value,1,7,1,1)
        self.pid_readout_layout.addWidget(self.p_gain_readout_label,2,0,1,1)
        self.pid_readout_layout.addWidget(self.p_gain_readout_value,2,1,1,1)
        self.pid_readout_layout.addWidget(self.i_gain_readout_label,2,2,1,1)
        self.pid_readout_layout.addWidget(self.i_gain_readout_value,2,3,1,1)
        self.pid_readout_layout.addWidget(self.d_gain_readout_label,2,4,1,1)
        self.pid_readout_layout.addWidget(self.d_gain_readout_value,2,5,1,1)
        self.pid_readout_layout.addWidget(self.o_readout_label,2,6,1,1)
        self.pid_readout_layout.addWidget(self.o_readout_value,2,7,1,1)
        self.pid_readout_layout.addWidget(self.ramp_readout_label,3,2,1,1)
        self.pid_readout_layout.addWidget(self.ramp_readout_value,3,3,1,1)
        self.pid_readout_layout.addWidget(self.ramp_rate_readout_label,3,4,1,1)
        self.pid_readout_layout.addWidget(self.ramp_rate_readout_value,3,5,1,1)
        self.pid_readout_layout.addWidget(self.ramp_status_readout_label,3,6,1,1)
        self.pid_readout_layout.addWidget(self.ramp_status_readout_value,3,7,1,1)
        self.pid_readout_layout.addWidget(self.pid_status_readout_label,4,4,1,1)
        self.pid_readout_layout.addWidget(self.pid_status_readout_value,4,5,1,1)
        self.pid_readout_layout.addWidget(self.manual_output_readout_label,4,6,1,1)
        self.pid_readout_layout.addWidget(self.manual_output_readout_value,4,7,1,1)

        self.procedures_layout.addWidget(self.setup_button)
        self.procedures_layout.addWidget(self.warmup_button)
        self.procedures_layout.addWidget(self.dumpheat_button)
        self.procedures_layout.addWidget(self.cooldown_button)
        self.procedures_layout.addWidget(self.regulate_button)

        self.pid_commands_layout.addWidget(self.enabled_command_check,0,0,1,1)
        self.pid_commands_layout.addWidget(self.bridge_setpoint_command_label,0,2,1,1)
        self.pid_commands_layout.addWidget(self.bridge_setpoint_command_value,0,3,1,2)
        self.pid_commands_layout.addWidget(self.pid_setpoint_command_label,0,5,1,1)
        self.pid_commands_layout.addWidget(self.pid_setpoint_command_value,0,6,1,2)
        self.pid_commands_layout.addWidget(self.pid_status_command_label,1,2,1,1)
        self.pid_commands_layout.addWidget(self.pid_status_command_value,1,3,1,2)
        self.pid_commands_layout.addWidget(self.manual_output_command_label,1,5,1,1)
        self.pid_commands_layout.addWidget(self.manual_output_command_value,1,6,1,2)
        self.pid_commands_layout.addWidget(self.ramp_command_label,2,2,1,1)
        self.pid_commands_layout.addWidget(self.ramp_command_value,2,3,1,2)
        self.pid_commands_layout.addWidget(self.ramp_rate_command_label,2,5,1,1)
        self.pid_commands_layout.addWidget(self.ramp_rate_command_value,2,6,1,2)
        self.pid_commands_layout.addWidget(self.p_status_command_label,3,0,1,1)
        self.pid_commands_layout.addWidget(self.p_status_command_value,3,1,1,1)
        self.pid_commands_layout.addWidget(self.i_status_command_label,3,2,1,1)
        self.pid_commands_layout.addWidget(self.i_status_command_value,3,3,1,1)
        self.pid_commands_layout.addWidget(self.d_status_command_label,3,4,1,1)
        self.pid_commands_layout.addWidget(self.d_status_command_value,3,5,1,1)
        self.pid_commands_layout.addWidget(self.o_status_command_label,3,6,1,1)
        self.pid_commands_layout.addWidget(self.o_status_command_value,3,7,1,1)
        self.pid_commands_layout.addWidget(self.p_gain_command_label,4,0,1,1)
        self.pid_commands_layout.addWidget(self.p_gain_command_value,4,1,1,1)
        self.pid_commands_layout.addWidget(self.i_gain_command_label,4,2,1,1)
        self.pid_commands_layout.addWidget(self.i_gain_command_value,4,3,1,1)
        self.pid_commands_layout.addWidget(self.d_gain_command_label,4,4,1,1)
        self.pid_commands_layout.addWidget(self.d_gain_command_value,4,5,1,1)
        self.pid_commands_layout.addWidget(self.o_command_label,4,6,1,1)
        self.pid_commands_layout.addWidget(self.o_command_value,4,7,1,1)

        self.plot_layout.addWidget(self.temp_plot,0,0,1,4)
        self.plot_layout.addWidget(self.status_label,1,0,1,1)
        self.plot_layout.addWidget(self.status_value,1,1,1,1)
        self.plot_layout.addWidget(self.status_bridge_setpoint_command_label,1,2,1,1)
        self.plot_layout.addWidget(self.status_bridge_setpoint_command_value,1,3,1,1)

        #Add Layouts to Groups
        self.measurements_group.setLayout(self.measurements_layout)
        self.pid_readout_group.setLayout(self.pid_readout_layout)
        self.procedures_group.setLayout(self.procedures_layout)
        self.pid_commands_group.setLayout(self.pid_commands_layout)
        self.plot_group.setLayout(self.plot_layout)

        #Add Groups to Widgets
        hbox1 = QtGui.QHBoxLayout()
        hbox1.addWidget(self.measurements_group)
        hbox1.addWidget(self.pid_readout_group)
        self.readings_widget.setLayout(hbox1)

        hbox2 = QtGui.QHBoxLayout()
        hbox2.addWidget(self.procedures_group)
        hbox2.addWidget(self.pid_commands_group)
        self.commands_widget.setLayout(hbox2)

        vbox1 = QtGui.QVBoxLayout()
        vbox1.addWidget(self.plot_group)
        self.bottom_widget.setLayout(vbox1)

        #Add Widgets to TabWidget
        self.top_widget.addTab(self.readings_widget, "Readings")
        self.top_widget.addTab(self.commands_widget, "Commands")

        #Add TabWidget and PlotWidget to Window
        vbox2 = QtGui.QVBoxLayout()
        vbox2.addWidget(self.top_widget)
        vbox2.addWidget(self.bottom_widget)
        self.setLayout(vbox2)

    def setupList(self):
        #Create lists in which bridge-temperature and bridge-setpoint values will be stored
        self.temp_list = []
        self.bridge_setpoint_list = []

    def setupPlot(self):
        #Create plot lines for both the temperature(yellow) and setpoint(green)
        #We poplulate them with data in the timer's update function
        self.temp_curve = Qwt.QwtPlotCurve("Bridge Temperature")
        self.temp_curve.attach(self.temp_plot.plot_region)
        self.temp_curve.setPen(Qt.QPen(Qt.Qt.yellow))

        self.bridge_setpoint_curve = Qwt.QwtPlotCurve("Bridge Setpoint")
        self.bridge_setpoint_curve.attach(self.temp_plot.plot_region)
        self.bridge_setpoint_curve.setPen(Qt.QPen(Qt.Qt.green))

    def setupSlots(self):
        QtCore.QObject.connect(self.enabled_command_check,QtCore.SIGNAL("stateChanged(int)"),self.blur_commands)
        QtCore.QObject.connect(self.bridge_setpoint_command_value,QtCore.SIGNAL("editingFinished()"),self.set_bridge_setpoint)
        QtCore.QObject.connect(self.pid_setpoint_command_value,QtCore.SIGNAL("editingFinished()"),self.set_pid_setpoint)
        QtCore.QObject.connect(self.pid_status_command_value,QtCore.SIGNAL("activated(const QString&)"),self.set_pid_status)
        QtCore.QObject.connect(self.manual_output_command_value,QtCore.SIGNAL("editingFinished()"),self.set_manual_output)
        QtCore.QObject.connect(self.ramp_command_value,QtCore.SIGNAL("activated(const QString&)"),self.set_ramp)
        QtCore.QObject.connect(self.ramp_rate_command_value,QtCore.SIGNAL("editingFinished()"),self.set_ramp_rate)
        QtCore.QObject.connect(self.p_status_command_value,QtCore.SIGNAL("activated(const QString&)"),self.set_p_status)
        QtCore.QObject.connect(self.i_status_command_value,QtCore.SIGNAL("activated(const QString&)"),self.set_i_status)
        QtCore.QObject.connect(self.d_status_command_value,QtCore.SIGNAL("activated(const QString&)"),self.set_d_status)
        QtCore.QObject.connect(self.o_status_command_value,QtCore.SIGNAL("activated(const QString&)"),self.set_o_status)
        QtCore.QObject.connect(self.p_gain_command_value,QtCore.SIGNAL("editingFinished()"),self.set_p_gain)
        QtCore.QObject.connect(self.i_gain_command_value,QtCore.SIGNAL("editingFinished()"),self.set_i_gain)
        QtCore.QObject.connect(self.d_gain_command_value,QtCore.SIGNAL("editingFinished()"),self.set_d_gain)
        QtCore.QObject.connect(self.o_command_value,QtCore.SIGNAL("editingFinished()"),self.set_o)
        QtCore.QObject.connect(self.status_bridge_setpoint_command_value,QtCore.SIGNAL("editingFinished()"),self.set_status_bridge_setpoint)

    def blur_commands(self, state):
        #Blurs Commands
        self.bridge_setpoint_command_value.setEnabled(state)
        self.pid_setpoint_command_value.setEnabled(state)
        self.pid_status_command_value.setEnabled(state)
        self.manual_output_command_value.setEnabled(state)
        self.ramp_command_value.setEnabled(state)
        self.ramp_rate_command_value.setEnabled(state)
        self.p_status_command_value.setEnabled(state)
        self.i_status_command_value.setEnabled(state)
        self.d_status_command_value.setEnabled(state)
        self.o_status_command_value.setEnabled(state)
        self.p_gain_command_value.setEnabled(state)
        self.i_gain_command_value.setEnabled(state)
        self.d_gain_command_value.setEnabled(state)
        self.o_command_value.setEnabled(state)

    def set_bridge_setpoint(self):
        #Changes the Bridge Setpoint
        self.sim900.setBridgeSetpoint(self.bridge_setpoint_command_value.value())

    def set_pid_setpoint(self):
        #Changes the PID Setpoint
        self.sim900.setPIDSetpoint(self.pid_setpoint_command_value.value())

    def set_pid_status(self):
        #Toggles whether the PID Loop controls the output
        if self.pid_status_command_value.currentText()=="ON":
            self.sim900.setPIDControl(True)
        elif self.pid_status_command_value.currentText()=="OFF":
            self.sim900.setPIDControl(False)

    def set_manual_output(self):
        #Sets the Manual Output
        self.sim900.setManualOutput(self.manual_output_command_value.value())

    def set_ramp(self):
        #Toggles whether Ramping is on or off
        if self.ramp_command_value.currentText()=="ON":
            self.sim900.setRampOn(True)
        elif self.ramp_command_value.currentText()=="OFF":
            self.sim900.setRampOn(False)

    def set_ramp_rate(self):
        #Sets the Ramp Rate
        self.sim900.setRampRate(self.ramp_rate_command_value.value())

    def set_p_status(self):
        #Toggles whether Proportional Error Contributes to PID Output
        if self.p_status_command_value.currentText()=="ON":
            self.sim900.setPropOn(True)
        elif self.p_status_command_value.currentText()=="OFF":
            self.sim900.setPropOn(False)

    def set_i_status(self):
        #Toggles whether Integral Error Contributes to PID Output
        if self.i_status_command_value.currentText()=="ON":
            self.sim900.setIntOn(True)
        elif self.i_status_command_value.currentText()=="OFF":
            self.sim900.setIntOn(False)

    def set_d_status(self):
        #Toggles whether Derivative Error Contributes to PID Output
        if self.d_status_command_value.currentText()=="ON":
            self.sim900.setDerivOn(True)
        elif self.d_status_command_value.currentText()=="OFF":
            self.sim900.setDerivOn(False)

    def set_o_status(self):
        #Toggles whether Offset Contributes to PID Output
        if self.o_status_command_value.currentText()=="ON":
            self.sim900.setOffsetOn(True)
        elif self.o_status_command_value.currentText()=="OFF":
            self.sim900.setOffsetOn(False)

    def set_p_gain(self):
        #Sets the Proportional Gain
        self.sim900.setPropGain(self.p_gain_command_value.value())

    def set_i_gain(self):
        #Sets the Integral Gain
        self.sim900.setIntGain(self.i_gain_command_value.value())

    def set_d_gain(self):
        #Sets the Derivative Gain
        self.sim900.setDerivGain(self.d_gain_command_value.value())

    def set_o(self):
        #Sets the Offset
        self.sim900.setOffset(self.o_command_value.value())

    def set_status_bridge_setpoint(self):
        #Changes the Bridge Setpoint Gradually
        self.sim900.setSetpoint(self.status_bridge_setpoint_command_value.value())

    def setupTimer(self):
        #Create a QT Timer that will timeout every half-a-second
        #The timeout is connected to the update function
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(500)

    def update(self):
        #Fetches values from sim900 and updates value boxes
        #Also updates the dictionary that data_logging is looking at
        self.sim900.fetchDict()
        self.registers.update(self.sim900.data)
        bridge_setpoint = self.sim900.data["bridge_temperature_setpoint"]
        self.bridge_setpoint_value.setText(str(bridge_setpoint))
        temp_bridge = self.sim900.data["bridge_temp_value"]
        self.temp_bridge_value.setText(str(temp_bridge))
        temp_3K = self.sim900.data["therm_temperature"][2]
        self.temp_3K_value.setText(str(temp_3K))
        temp_50K = self.sim900.data["therm_temperature"][0]
        self.temp_50K_value.setText(str(temp_50K))
        current = self.sim900.data["dvm_volts"][1]
        self.current_value.setText(str(current))
        setpoint = self.sim900.data["pid_setpoint"]
        self.setpoint_readout_value.setText(str(setpoint))
        measure = self.sim900.data["pid_measure_mon"]
        self.measure_readout_value.setText(str(measure))
        error = self.sim900.data["pid_error_mon"]
        self.error_readout_value.setText(str(error))
        output = self.sim900.data["pid_output_mon"]
        self.output_readout_value.setText(str(output))
        p_status = self.sim900.data["pid_propor_on"]
        if p_status==0.0:
            self.p_status_readout_value.setText("OFF")
        elif p_status==1.0:
            self.p_status_readout_value.setText("ON")
        i_status = self.sim900.data["pid_integral_on"]
        if i_status==0.0:
            self.i_status_readout_value.setText("OFF")
        elif i_status==1.0:
            self.i_status_readout_value.setText("ON")
        d_status = self.sim900.data["pid_deriv_on"]
        if d_status==0.0:
            self.d_status_readout_value.setText("OFF")
        elif d_status==1.0:
            self.d_status_readout_value.setText("ON")
        o_status = self.sim900.data["pid_offset_on"]
        if o_status==0.0:
            self.o_status_readout_value.setText("OFF")
        elif o_status==1.0:
            self.o_status_readout_value.setText("ON")
        p_gain = self.sim900.data["pid_propor_gain"]
        self.p_gain_readout_value.setText(str(p_gain))
        if p_status==0.0:
            self.p_gain_readout_value.setEnabled(False)
        elif p_status==1.0:
            self.p_gain_readout_value.setEnabled(True)
        i_gain = self.sim900.data["pid_integral_gain"]
        self.i_gain_readout_value.setText(str(i_gain))
        if i_status==0.0:
            self.i_gain_readout_value.setEnabled(False)
        elif i_status==1.0:
            self.i_gain_readout_value.setEnabled(True)
        d_gain = self.sim900.data["pid_deriv_gain"]
        self.d_gain_readout_value.setText(str(d_gain))
        if d_status==0.0:
            self.d_gain_readout_value.setEnabled(False)
        elif d_status==1.0:
            self.d_gain_readout_value.setEnabled(True)
        o = self.sim900.data["pid_offset"]
        self.o_readout_value.setText(str(o))
        if o_status==0.0:
            self.o_readout_value.setEnabled(False)
        elif o_status==1.0:
            self.o_readout_value.setEnabled(True)
        ramp = self.sim900.data["pid_ramp_on"]
        if ramp==0.0:
            self.ramp_readout_value.setText("OFF")
        elif ramp==1.0:
            self.ramp_readout_value.setText("ON")
        ramp_rate = self.sim900.data["pid_ramp_rate"]
        self.ramp_rate_readout_value.setText(str(ramp_rate))
        if ramp==0.0:
            self.ramp_rate_readout_value.setEnabled(False)
        elif ramp==1.0:
            self.ramp_rate_readout_value.setEnabled(True)
        ramp_status = self.sim900.data["pid_ramp_status"]
        if ramp_status==0.0:
            self.ramp_status_readout_value.setText("IDLE")
        elif ramp_status==1.0:
            self.ramp_status_readout_value.setText("PENDING")
        elif ramp_status==2.0:
            self.ramp_status_readout_value.setText("RAMPING")
        elif ramp_status==3.0:
            self.ramp_status_readout_value.setText("PAUSED")
        if ramp==0.0:
            self.ramp_status_readout_value.setEnabled(False)
        elif ramp==1.0:
            self.ramp_status_readout_value.setEnabled(True)
        pid_status = self.sim900.data["pid_manual_status"]
        if pid_status==0.0:
            self.pid_status_readout_value.setText("OFF")
        elif pid_status==1.0:
            self.pid_status_readout_value.setText("ON")
        manual_output = self.sim900.data["pid_manual_out"]
        self.manual_output_readout_value.setText(str(manual_output))
        if pid_status==1.0:
            self.manual_output_readout_value.setEnabled(False)
        elif pid_status==0.0:
            self.manual_output_readout_value.setEnabled(True)
            
        for k in range(4):
            self.sim900.data['therm_temperature_%d' % k] = self.sim900.data['therm_temperature'][k]
            self.sim900.data['therm_volts_%d' % k] = self.sim900.data['therm_volts'][k]
            self.sim900.data['dvm_volts_%d' % k] = self.sim900.data['dvm_volts'][k]
            self.sim900.data['dvm_ref_%d' % k] = self.sim900.data['dvm_ref'][k]
            self.sim900.data['dvm_gnd_%d' % k] = self.sim900.data['dvm_gnd'][k]
            
        self.registers.update(self.sim900.data)


        #Update Temperature and Setpoint Lists
        if len(self.temp_list) < 500:
            self.temp_list.append(temp_bridge)
        elif len(self.temp_list) >= 500:
            del self.temp_list[0]
            self.temp_list.append(temp_bridge)

        if len(self.bridge_setpoint_list) < 500:
            self.bridge_setpoint_list.append(bridge_setpoint)
        elif len(self.bridge_setpoint_list) >= 500:
            del self.bridge_setpoint_list[0]
            self.bridge_setpoint_list.append(bridge_setpoint)

        #Update Plots
        temp_x1 = arange(len(self.temp_list))
        self.temp_curve.setData(temp_x1,self.temp_list)

        temp_x2 = arange(len(self.bridge_setpoint_list))
        self.bridge_setpoint_curve.setData(temp_x2,self.bridge_setpoint_list)

        #Replot
        self.temp_plot.plot_region.replot()

def main():
    app = QtGui.QApplication(sys.argv)
    fg = fridge_gui()
    fg.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
