#General Widget to be used for GUI Plots
#Curves are set up by the calling class
#Author: Ross Williamson
#Edited by: Joshua Sobrin & Glenn Jones
#Last Date Modified - 10/11/12

from PyQt4 import QtCore, QtGui,Qt
import PyQt4.Qwt5 as Qwt

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class plot_template(QtGui.QWidget):
    def __init__(self, x_log=False, y_log=False, legend=False, gui_parent=None):
        QtGui.QWidget.__init__(self, gui_parent)
        self.x_log = x_log
        self.y_log = y_log

        self.setupUI()
        self.setupPlot()
        self.setupZoomer()
        if legend is True:
            self.setupLegend()
        self.setupSlots()

    def setupUI(self):
        self.autoscale_button = QtGui.QPushButton("Autoscale")
        self.commit_button = QtGui.QPushButton("Commit")
        self.x_min_label = QtGui.QLabel("x-min")
        self.x_min_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.x_max_label = QtGui.QLabel("x-max")
        self.x_max_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.y_min_label = QtGui.QLabel("y-min")
        self.y_min_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.y_max_label = QtGui.QLabel("y-max")
        self.y_max_label.setAlignment(QtCore.Qt.AlignVCenter|QtCore.Qt.AlignRight)
        self.x_min_value = QtGui.QDoubleSpinBox()
        self.x_min_value.setRange(-10000,10000)
        self.x_min_value.setSingleStep(1)
        self.x_min_value.setDecimals(6)
        self.x_max_value = QtGui.QDoubleSpinBox()
        self.x_max_value.setRange(-10000,10000)
        self.x_max_value.setSingleStep(1)
        self.x_max_value.setDecimals(6)
        self.y_min_value = QtGui.QDoubleSpinBox()
        self.y_min_value.setRange(-10000,10000)
        self.y_min_value.setSingleStep(1)
        self.y_min_value.setDecimals(6)
        self.y_max_value = QtGui.QDoubleSpinBox()
        self.y_max_value.setRange(-10000,10000)
        self.y_max_value.setSingleStep(1)
        self.y_max_value.setDecimals(6)

        self.h_control_layout = QtGui.QHBoxLayout()
        self.h_control_layout.addWidget(self.autoscale_button)
        self.h_control_layout.addStretch(1)
        self.h_control_layout.addWidget(self.commit_button)
        self.h_control_layout.addWidget(self.x_min_label)
        self.h_control_layout.addWidget(self.x_min_value)
        self.h_control_layout.addWidget(self.x_max_label)
        self.h_control_layout.addWidget(self.x_max_value)
        self.h_control_layout.addWidget(self.y_min_label)
        self.h_control_layout.addWidget(self.y_min_value)
        self.h_control_layout.addWidget(self.y_max_label)
        self.h_control_layout.addWidget(self.y_max_value)

        self.plot_region = Qwt.QwtPlot()

        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.addLayout(self.h_control_layout)
        self.verticalLayout.addWidget(self.plot_region)

        self.setLayout(self.verticalLayout)

    def setupPlot(self):
        #Note we don't setup any curves here - that is the job of the
        #the calling class - We do setup the pickers though
        self.plot_region.setCanvasBackground(Qt.Qt.darkBlue)
        if self.x_log is True:
            self.plot_region.setAxisScaleEngine(Qwt.QwtPlot.xBottom, Qwt.QwtLog10ScaleEngine())
        if self.y_log is True:
            self.plot_region.setAxisScaleEngine(Qwt.QwtPlot.yLeft, Qwt.QwtLog10ScaleEngine())

    def setupZoomer(self):
        self.zoomer = Qwt.QwtPlotZoomer(Qwt.QwtPlot.xBottom,Qwt.QwtPlot.yLeft,Qwt.QwtPicker.DragSelection,Qwt.QwtPicker.AlwaysOn,self.plot_region.canvas())
        self.zoomer.setRubberBandPen(Qt.QPen(Qt.Qt.red))
        self.zoomer.setTrackerPen(Qt.QPen(Qt.Qt.cyan))
        self.zoomer.setZoomBase()

    def setupLegend(self):
        self.legend  = Qwt.QwtLegend()
        self.legend.setFrameStyle(Qt.QFrame.Box | Qt.QFrame.Sunken)
        self.legend.setItemMode(Qwt.QwtLegend.ClickableItem)
        self.plot_region.insertLegend(self.legend, Qwt.QwtPlot.BottomLegend)

    def setupSlots(self):
        QtCore.QObject.connect(self.autoscale_button,QtCore.SIGNAL("clicked()"),self.autoscale)
        QtCore.QObject.connect(self.commit_button,QtCore.SIGNAL("clicked()"),self.commit)

    def autoscale(self):
        self.plot_region.setAxisAutoScale(Qwt.QwtPlot.xBottom)
        self.plot_region.setAxisAutoScale(Qwt.QwtPlot.yLeft)

    def commit(self):
        if self.x_log is True:
            self.plot_region.setAxisScale(Qwt.QwtPlot.xBottom,pow(10,self.x_min_value.value()),pow(10,self.x_max_value.value()))
        else:
            self.plot_region.setAxisScale(Qwt.QwtPlot.xBottom,self.x_min_value.value(),self.x_max_value.value())
        if self.y_log is True:
            self.plot_region.setAxisScale(Qwt.QwtPlot.yLeft,pow(10,self.y_min_value.value()),pow(10,self.y_max_value.value()))
        else:
            self.plot_region.setAxisScale(Qwt.QwtPlot.yLeft,self.y_min_value.value(),self.y_max_value.value())
