from PyQt4 import QtCore, QtGui,Qt

class small_text(QtGui.QLabel):
     def __init__(self,text,color,gui_parent=None):
        QtGui.QLabel.__init__(self, gui_parent)
        self.setText(text)
        self.setFont(QtGui.QFont( "lucida", 10 ));
        color_string = "QLabel {color : %s;}" % color
        self.setStyleSheet(color_string);

     def set_color_text(self,text,color):
         self.setText(text)
         color_string = "QLabel {color : %s;}" % color
         self.setStyleSheet(color_string);

   
class bolo_doubleInput(QtGui.QDoubleSpinBox):
    def __init__(self,gui_parent=None):
        QtGui.QDoubleSpinBox.__init__(self, gui_parent)

        self.setRange(-2000,2000)
        self.setDecimals(3)
        self.setSingleStep(0.001)
