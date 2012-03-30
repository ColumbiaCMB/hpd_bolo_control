from PyQt4 import QtCore, QtGui
from control_ui import Ui_RawControl

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class bolo_board_gui(QtGui.QDialog):
    def __init__(self,parent,gui_parent=None):
        QtGui.QDialog.__init__(self, gui_parent)
        self.p = parent
        self.ui = Ui_RawControl()
        self.ui.setupUi(self)
        self.sweep_timer = QtCore.QTimer()

        self.setup_slots()


    def setup_slots(self):
        #buttons
        QtCore.QObject.connect(self.ui.SSABIAS_Button,QtCore.SIGNAL("toggled(bool)"), self.ssa_switch)
        QtCore.QObject.connect(self.ui.SSABIAS_Ext_Button,QtCore.SIGNAL("toggled(bool)"), self.ssa_ext_switch)
        QtCore.QObject.connect(self.ui.SSAFB_Button,QtCore.SIGNAL("toggled(bool)"), self.p.ssa_fb_switch)
        QtCore.QObject.connect(self.ui.S2BIAS_Button,QtCore.SIGNAL("toggled(bool)"), self.p.s2_bias_switch)
        QtCore.QObject.connect(self.ui.S2FB_Button,QtCore.SIGNAL("toggled(bool)"), self.p.s2_fb_switch)
        QtCore.QObject.connect(self.ui.RSBIAS_Button,QtCore.SIGNAL("toggled(bool)"), self.p.rs_switch)
        QtCore.QObject.connect(self.ui.S1FB_Button,QtCore.SIGNAL("toggled(bool)"), self.s1_fb_m_switch)
        QtCore.QObject.connect(self.ui.TESBIAS_Button,QtCore.SIGNAL("toggled(bool)"), self.tes_switch)
        QtCore.QObject.connect(self.ui.TESBIAS_Ext_Button,QtCore.SIGNAL("toggled(bool)"), self.tes_ext_switch)

        QtCore.QObject.connect(self.ui.Heater_Button,QtCore.SIGNAL("toggled(bool)"), self.heater_switch)
        QtCore.QObject.connect(self.ui.Heater_Ext_Button,QtCore.SIGNAL("toggled(bool)"), self.heater_ext_switch)
        QtCore.QObject.connect(self.ui.AUX_Button,QtCore.SIGNAL("toggled(bool)"), self.p.aux_switch)

        QtCore.QObject.connect(self.ui.RSExec_Button,QtCore.SIGNAL("clicked()"), self.set_rs)
        QtCore.QObject.connect(self.ui.Sweep_Button,QtCore.SIGNAL("clicked()"), self.sweep_pressed)


        #voltages and RS
        QtCore.QObject.connect(self.ui.SSABIAS_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.ssa_bias_voltage)
        QtCore.QObject.connect(self.ui.SSAFB_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.ssa_fb_voltage)
        QtCore.QObject.connect(self.ui.S2BIAS_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.s2_bias_voltage)
        QtCore.QObject.connect(self.ui.S2FB_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.s2_fb_voltage)
        QtCore.QObject.connect(self.ui.RSBIAS_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.rs_voltage)
        QtCore.QObject.connect(self.ui.S1FB_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.s1_fb_voltage)
        QtCore.QObject.connect(self.ui.TESBIAS_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.tes_voltage)

        QtCore.QObject.connect(self.ui.Heater_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.htr_voltage)
        QtCore.QObject.connect(self.ui.AUX_Input,QtCore.SIGNAL("valueChanged(double)"), self.p.aux_voltage)

        #PI Loop
        QtCore.QObject.connect(self.ui.PGain_cb,QtCore.SIGNAL("currentIndexChanged(const QString)"), self.set_pgain)
        QtCore.QObject.connect(self.ui.PGain_Button,QtCore.SIGNAL("toggled(bool)"), self.p.pgain_switch)
        QtCore.QObject.connect(self.ui.TimeConstant_cb,QtCore.SIGNAL("currentIndexChanged(const QString)"), self.set_tconst)
        QtCore.QObject.connect(self.ui.TimeConstant_Button,QtCore.SIGNAL("toggled(bool)"), self.p.tconst_switch)
        QtCore.QObject.connect(self.ui.FeedBack_Button,QtCore.SIGNAL("toggled(bool)"), self.Feedback_switch)
        QtCore.QObject.connect(self.ui.ShortInt_Button,QtCore.SIGNAL("toggled(bool)"), self.p.short_int_switch)


        #Connect the timer function to the update 
        QtCore.QObject.connect(self.sweep_timer, QtCore.SIGNAL("timeout()"), self.update_sweep)

    def set_pgain(self,gain):
        self.p.set_pgain(gain.toInt()[0])

    def set_tconst(self,gain):
        self.p.set_tconst(int(gain.toFloat()[0]*10 + 0.5))

    def update_sweep(self):
        value = self.p.sweep_progress
        self.ui.Sweep_pb.setValue(value)
        if value == -1:
            self.sweep_timer.stop()
            self.ui.Sweep_pb.setValue(100)

    def sweep_pressed(self):
        #Starts sweep and update timer for progress bar
        start = self.ui.Start_Input.value()
        stop = self.ui.Stop_Input.value()
        step = self.ui.Step_Input.value()
        count = self.ui.No_Sweeps.value()
        loop = self.ui.Loop_rb.isChecked()
        name = str(self.ui.Sweep_cb.currentText())

        self.sweep_timer.start(500)
        self.p.wrapper_sweep_voltage(name,start,stop,step,count,loop)

    def set_rs(self):
        self.p.rs_channel(self.ui.RS_Channel.value())

    #Interlock functions
    def tes_switch(self,state):
        if state is True:
            self.ui.TESBIAS_Ext_Button.setChecked(False)
        self.p.tes_bias_switch(state)

    def tes_ext_switch(self,state):
        if state is True:
            self.ui.TESBIAS_Button.setChecked(False)
        self.p.tes_bias_ext_switch(state)

    def ssa_switch(self,state):
        if state is True:
            self.ui.SSABIAS_Ext_Button.setChecked(False)
        self.p.ssa_bias_switch(state)

    def ssa_ext_switch(self,state):
        if state is True:
            self.ui.SSABIAS_Button.setChecked(False)
        self.p.ssa_bias_ext_switch(state)
 
    def s1_fb_m_switch(self,state):
        if state is True:
            self.ui.FeedBack_Button.setChecked(False)
        self.p.s1_fb_m_switch(state)

    def Feedback_switch(self,state):
        if state is True:
            self.ui.S1FB_Button.setChecked(False)
        self.p.s1_fb_switch(state)

    def heater_switch(self,state):
        if state is True:
            self.ui.Heater_Ext_Button.setChecked(False)
        self.p.heater_switch(state)

    def heater_ext_switch(self,state):
        if state is True:
            self.ui.Heater_Button.setChecked(False)
        self.p.heater_ext_switch(state)
