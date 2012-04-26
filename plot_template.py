from PyQt4 import QtCore, QtGui,Qt
import PyQt4.Qwt5 as Qwt

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class plot_template(QtGui.QWidget):
    def __init__(self,x_log=False,y_log=False,gui_parent=None):
        QtGui.QWidget.__init__(self, gui_parent)
        self.plot_timer = QtCore.QTimer()
        self.x_log = x_log
        self.y_log = y_log

        self.setupUi()
        self.setupDefaults()
        self.setupZoomers()
        self.setup_legend()
        self.setup_plots()
        self.setup_slots()

    def setupUi(self):
        self.h_control_layout = QtGui.QHBoxLayout()
        self.zoomButton = QtGui.QPushButton("Zoom")
        self.zoomButton.setCheckable(True)
        self.xstart_label = QtGui.QLabel("xstart")
        self.xend_label = QtGui.QLabel("xend")
        self.ystart_label = QtGui.QLabel("ystart")
        self.yend_label = QtGui.QLabel("yend")
        self.auto_check = QtGui.QCheckBox("Auto")
        self.auto_check.setChecked(True)
        
        self.xs_Input = QtGui.QDoubleSpinBox()
        self.xe_Input = QtGui.QDoubleSpinBox()
        self.ys_Input = QtGui.QDoubleSpinBox()
        self.ye_Input = QtGui.QDoubleSpinBox()

        self.h_control_layout.addWidget(self.zoomButton)
        self.h_control_layout.addWidget(self.xstart_label)
        self.h_control_layout.addWidget(self.xs_Input)
        self.h_control_layout.addWidget(self.xend_label)
        self.h_control_layout.addWidget(self.xe_Input)
        self.h_control_layout.addWidget(self.ystart_label)
        self.h_control_layout.addWidget(self.ys_Input)
        self.h_control_layout.addWidget(self.yend_label)
        self.h_control_layout.addWidget(self.ye_Input)
        self.h_control_layout.addWidget(self.auto_check)

        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.addLayout(self.h_control_layout)

        self.plot_region = Qwt.QwtPlot()
        self.verticalLayout.addWidget(self.plot_region)
        
        self.setLayout(self.verticalLayout)

    def setupDefaults(self):
        #disable the resziers
        self.xs_Input.setEnabled(False)
        self.xe_Input.setEnabled(False)
        self.ys_Input.setEnabled(False)
        self.ye_Input.setEnabled(False)

        #Set range to something  - should be changed
        self.xs_Input.setRange(-1e3,1e3)
        self.xe_Input.setRange(-1e3,1e3)
        self.ys_Input.setRange(-1e3,1e3)
        self.ye_Input.setRange(-1e3,1e3)

    def setupZoomers(self):
        self.zoomer = Qwt.QwtPlotZoomer(
            Qwt.QwtPlot.xBottom,
            Qwt.QwtPlot.yLeft,
            Qwt.QwtPicker.DragSelection,
            Qwt.QwtPicker.AlwaysOff,
            self.plot_region.canvas())
        self.zoomer.setRubberBandPen(Qt.QPen(Qt.Qt.green))

        self.picker = Qwt.QwtPlotPicker(
            Qwt.QwtPlot.xBottom,
            Qwt.QwtPlot.yLeft,
            Qwt.QwtPicker.PointSelection | Qwt.QwtPicker.DragSelection,
            Qwt.QwtPlotPicker.CrossRubberBand,
            Qwt.QwtPicker.AlwaysOn,
            self.plot_region.canvas())
        self.picker.setRubberBandPen(Qt.QPen(Qt.Qt.green))
        self.picker.setTrackerPen(Qt.QPen(Qt.Qt.cyan))

    def setup_legend(self):
        self.legend  = Qwt.QwtLegend()
        self.legend.setFrameStyle(Qt.QFrame.Box | Qt.QFrame.Sunken)
        self.legend.setItemMode(Qwt.QwtLegend.ClickableItem)
        self.plot_region.insertLegend(self.legend, Qwt.QwtPlot.BottomLegend)

    def setup_plots(self):
        #Note we don't setup any curves here - that is the job of the
        #the calling class - We do setup the pickers though
        self.plot_region.setCanvasBackground(Qt.Qt.darkBlue)
        if self.x_log is True:
            self.plot_region.setAxisScaleEngine(Qwt.QwtPlot.xBottom, Qwt.QwtLog10ScaleEngine())
        if self.y_log is True:
            self.plot_region.setAxisScaleEngine(Qwt.QwtPlot.yLeft, Qwt.QwtLog10ScaleEngine())

    def setup_slots(self):
        QtCore.QObject.connect(self.zoomButton,QtCore.SIGNAL("toggled(bool)"), self.call_zoom)
        QtCore.QObject.connect(self.auto_check,QtCore.SIGNAL("toggled(bool)"), self.call_autoscale)
        QtCore.QObject.connect(self.xs_Input,QtCore.SIGNAL("valueChanged(double)"), self.call_set_range)
        QtCore.QObject.connect(self.xe_Input,QtCore.SIGNAL("valueChanged(double)"), self.call_set_range)
        QtCore.QObject.connect(self.ys_Input,QtCore.SIGNAL("valueChanged(double)"), self.call_set_range)
        QtCore.QObject.connect(self.ye_Input,QtCore.SIGNAL("valueChanged(double)"), self.call_set_range)

    def call_autoscale(self,state):
        self.xs_Input.setEnabled(not state)
        self.xe_Input.setEnabled(not state)
        self.ys_Input.setEnabled(not state)
        self.ye_Input.setEnabled(not state)

        if state is True:
            self.zoomButton.setChecked(False)
            self.plot_region.setAxisAutoScale(Qwt.QwtPlot.xBottom)
            self.plot_region.setAxisAutoScale(Qwt.QwtPlot.yLeft)
            self.zoomer.setZoomBase()


    def call_set_range(self,dummy_val):
        if self.x_log is True:
            self.plot_region.setAxisScale(Qwt.QwtPlot.xBottom, 
                                             pow(10,self.xs_Input.value()),
                                             pow(10,self.xe_Input.value()))
        else:
            self.plot_region.setAxisScale(Qwt.QwtPlot.xBottom, 
                                             self.xs_Input.value(),
                                             self.xe_Input.value())
        if self.y_log is True:
            self.plot_region.setAxisScale(Qwt.QwtPlot.yLeft, 
                                             pow(10,self.ys_Input.value()),
                                             pow(10,self.ye_Input.value()))
        else:
            self.plot_region.setAxisScale(Qwt.QwtPlot.yLeft, 
                                             self.ys_Input.value(),
                                             self.ye_Input.value())

    def call_zoom(self, on):
        self.zoomer.setEnabled(on)
        self.zoomer.zoom(0)

        if on:
            self.picker.setRubberBand(Qwt.QwtPicker.NoRubberBand)
        else:
            self.picker.setRubberBand(Qwt.QwtPicker.CrossRubberBand)

