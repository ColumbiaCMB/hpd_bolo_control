from PyQt4 import QtCore, QtGui,Qt

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class data_logging_gui(QtGui.QDialog):
    def __init__(self,parent,gui_parent=None):
        QtGui.QDialog.__init__(self, gui_parent)

        self.p = parent
        self.update_timer = QtCore.QTimer()
        self.update_timer.start(1000)
        self.setupUi()
        self.setupSlots()
        self.setup_init()
        self.setup_register_tree()

    def setupUi(self):
        self.setWindowTitle("Data Logging")
        self.button_layout = QtGui.QVBoxLayout()
        self.startstopButton = QtGui.QPushButton("Start")
        self.opencloseButton = QtGui.QPushButton("Open")
        self.temp = QtGui.QPushButton("temp")

        self.button_layout.addWidget(self.startstopButton)
        self.button_layout.addWidget(self.opencloseButton)
        self.button_layout.addWidget(self.temp)

        self.info_layout = QtGui.QGridLayout()
        self.prefix_label = QtGui.QLabel("Prefix")
        self.prefix_edit = QtGui.QLineEdit()
        self.fname_label = QtGui.QLabel("Filename")
        self.fsize_label = QtGui.QLabel("File Size")

        self.fname_ac = QtGui.QLabel("none")
        self.fsize_ac = QtGui.QLabel("0")
        
        self.standard_model = QtGui.QStandardItemModel()
        self.test_tree = QtGui.QTreeView()
        
        self.info_layout.addWidget(self.prefix_label,0,0,1,1)
        self.info_layout.addWidget(self.prefix_edit,0,1,1,1)
        self.info_layout.addWidget(self.fname_label,1,0,1,1)
        self.info_layout.addWidget(self.fname_ac,1,1,1,1)
        self.info_layout.addWidget(self.fsize_label,2,0,1,1)
        self.info_layout.addWidget(self.fsize_ac,2,1,1,1)

        
        self.main_layout = QtGui.QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addLayout(self.info_layout)
        self.uber_main_layout = QtGui.QVBoxLayout()
        self.uber_main_layout.addLayout(self.main_layout)
        self.uber_main_layout.addWidget(self.test_tree)

        self.setLayout(self.uber_main_layout)

    def setupSlots(self):
        QtCore.QObject.connect(self.startstopButton,QtCore.SIGNAL("clicked()"), self.startstop)
        QtCore.QObject.connect(self.opencloseButton,QtCore.SIGNAL("clicked()"), self.openclose)
        QtCore.QObject.connect(self.update_timer, QtCore.SIGNAL("timeout()"), self.update_gui)
        QtCore.QObject.connect(self.standard_model, QtCore.SIGNAL("itemChanged(QStandardItem *)"), self.model_changed)

    def setup_init(self):
        if self.p.file_name is None:
            #Disable the startstop button and set filename to None
            self.startstopButton.setEnabled(False)
            self.fsize_ac.setText("0")
            self.opencloseButton.setText("Open")
            self.fname_ac.setText("none")
        else:
            if not self.p.logging_event.isSet():
                #Then we are logging_events
                self.startstopButton.setText("Stop")
                if self.p.file_size > 1e3:
                    ftxt = ("%6.3f kB") % (self.p.file_size/1.0e3)
                if self.p.file_size > 1e6:
                    ftxt = ("%6.3f MB") % (self.p.file_size/1.0e6)
                if self.p.file_size > 1e9:
                    ftxt = ("%6.3f GB") % (self.p.file_size/1.0e9)
                self.fsize_ac.setText(ftxt)
            else:
                self.startstopButton.setText("Start")
            self.startstopButton.setEnabled(True)
            self.opencloseButton.setText("Close")
            self.fname_ac.setText(self.p.file_name)

    def update_gui(self):
        #Just run setup_init I think should do it
        self.setup_init()

    def setup_register_tree(self):
        #Do registers first
        for name in self.p.top_registers:
            reglist_item = QtGui.QStandardItem(name)
            reglist_item.setCheckable(True)
            reglist_item.setCheckState(True)
            reglist_item.setEditable(False)
            for i in self.p.top_registers[name]:
                print i
                freq_item = QtGui.QStandardItem("reg_1hz")
                freq_item.setEditable(False)
                reg_item = QtGui.QStandardItem(i)
                reg_item.setCheckable(True)
                reg_item.setCheckState(True)
                reg_item.setEditable(False)
                reglist_item.appendRow((reg_item,freq_item))
                              
            self.standard_model.appendRow(reglist_item)

        stream_item = QtGui.QStandardItem("Streams")
        stream_item.setCheckable(True)
        stream_item.setCheckState(True)
        stream_item.setEditable(False)
        
        for name in self.p.stream_sources:
            temp_item = QtGui.QStandardItem(name)
            freq_item = QtGui.QStandardItem(self.p.stream_sources[name]["speed"])
            freq_item.setEditable(False)

            temp_item.setCheckable(True)
            temp_item.setCheckState(True)
            temp_item.setEditable(False)
            
            stream_item.appendRow((temp_item,freq_item))

        self.standard_model.appendRow(stream_item)

        self.standard_model.setHorizontalHeaderItem(0, QtGui.QStandardItem("Register"))
        self.standard_model.setHorizontalHeaderItem(1, QtGui.QStandardItem("Frequency"))

        self.test_tree.setModel(self.standard_model)
        
    def startstop(self):
        if self.p.logging_event.isSet():
            #We need to start logging
            self.p.start_logging()
        else:
            self.p.stop_logging()
     
    def openclose(self):
        if self.p.file_name is None:
            #We need to open a file 
            print self.prefix_edit.text()
            if self.prefix_edit.text() == "":
                self.p.open_file()
            else:
                self.p.open_file(str(self.prefix_edit.text()))
        else:
            self.p.close_file()

    def model_changed(self,item):
        name = item.text()
        state = item.checkState()
        #We don't worry about partially checked stuff
        if state > 0:
            state = True
        else:
            state = False
        #We assume here we have only a parent and a child
        #first check to see if parent has been clicked
        parent = item.parent()
        if parent !=None:
            #set the flag for logging in  the top-level
            if parent.text() == "Streams":
                #We have a stream so update stream
                self.p.stream_sources[str(name)]["log"] = state
            else:
                print "Registers not yet implemented"
        else:
            print "Top level not yet implemented"

                               
