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
        self.fridgeButton = QtGui.QPushButton("Fridge Control")

        self.button_layout.addWidget(self.boardButton)
        self.button_layout.addWidget(self.adcButton)
        self.button_layout.addWidget(self.squidButton)
        self.button_layout.addWidget(self.dataButton)
        self.button_layout.addWidget(self.fridgeButton)

        self.setLayout(self.button_layout)

    def setupSlots(self):
          QtCore.QObject.connect(self.boardButton,QtCore.SIGNAL("clicked()"), self.show_board)
          QtCore.QObject.connect(self.adcButton,QtCore.SIGNAL("clicked()"), self.show_adc)
          QtCore.QObject.connect(self.squidButton,QtCore.SIGNAL("clicked()"), self.show_squid)
          QtCore.QObject.connect(self.dataButton,QtCore.SIGNAL("clicked()"), self.show_data)
          QtCore.QObject.connect(self.fridgeButton,QtCore.SIGNAL("clicked()"),self.show_fridge)

    def show_board(self):
        self.p.bb_gui.show()
        self.p.bb_gui.raise_()

    def show_adc(self):
        self.p.adc_gui.show()
        self.p.adc_gui.raise_()

    def show_squid(self):
        self.p.squid_gui.show()
        self.p.squid_gui.raise_()

    def show_data(self):
        self.p.data_gui.show()
        self.p.data_gui.raise_()

    def show_fridge(self):
        self.p.fridge_gui.show()
        self.p.fridge_gui.raise_()
