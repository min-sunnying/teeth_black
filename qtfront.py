import sys
import os
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from watchpoints import watch
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from typing import List, Tuple
from collections import deque
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import PyQt5.QtCore as QtCore
from PIL import Image, ImageDraw 
from PyQt5.QtCore import Qt
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox
from PyQt5.QtWidgets import QFileDialog, QLabel
from PyQt5.QtGui import QImage, QPixmap
import qtback as back

form_class = uic.loadUiType("./qtui.ui")[0]

#main window class
class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setMouseTracking(True)
        self.initui()
        self.image=back.ImageControl(self)
    
    def initui(self):
        #UI connection
        self.select_folder.triggered.connect(self.selectfolder)

        # mouse tracking
        tracker = back.MouseTracker(self.transparent)
        tracker.positionChanged.connect(self.on_positionChanged)
        self.label_position = QLabel(
            self.transparent, alignment=QtCore.Qt.AlignCenter
        )
        self.label_position.setStyleSheet('background-color: white; border: 1px solid black')

    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_positionChanged(self, pos):
        scale=self.getScale()
        delta = QtCore.QPoint(30, -15)
        self.label_position.show()
        self.label_position.move(pos + delta)
        self.label_position.setText("(%d, %d)" % (pos.x()/scale, pos.y()/scale))
        self.label_position.adjustSize()
        self.posx=pos.x()/scale
        self.posy=pos.y()/scale

    def selectfolder(self):
        self.image.selectfolder()
        self.image.imageLoad()
    
    def getScale(self):
        return self.image.setScale()
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()