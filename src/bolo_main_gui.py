from PyQt4 import QtCore, QtGui,Qt

class bolo_main_gui(QtGui.QWidget):
    def __init__(self,parent,gui_parent=None):
        QtGui.QWidget.__init__(self, gui_parent)

        self.p = parent
        self.setupUI()
        self.setupSlots()

    def setupUI(self):
        self.button_layout = QtGui.QVBoxLayout()
        self.boardButton = QtGui.QPushButton("Board Control")
        self.adcButton = QtGui.QPushButton("ADC Control")
        self.squidButton = QtGui.QPushButton("Squid Control")
        self.dataButton = QtGui.QPushButton("Data Logging")

        self.button_layout.addWidget(self.boardButton)
        self.button_layout.addWidget(self.adcButton)
        self.button_layout.addWidget(self.squidButton)
        self.button_layout.addWidget(self.dataButton)

        self.setLayout(self.button_layout)

    def setupSlots(self):
          QtCore.QObject.connect(self.boardButton,QtCore.SIGNAL("clicked()"), self.show_board)
          QtCore.QObject.connect(self.adcButton,QtCore.SIGNAL("clicked()"), self.show_adc)
          QtCore.QObject.connect(self.squidButton,QtCore.SIGNAL("clicked()"), self.show_squid)
          QtCore.QObject.connect(self.dataButton,QtCore.SIGNAL("clicked()"), self.show_data)

    def show_board(self):
        self.p.bb_gui.show()

    def show_adc(self):
        self.p.adc_gui.show()

    def show_squid(self):
        self.p.squid_gui.show()

    def show_data(self):
        self.p.data_gui.show()