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
import qtmask as qmask
import qt3d as q3d

form_class = uic.loadUiType("./qtui.ui")[0]

#main window class
class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setMouseTracking(True)
        self.image=qmask.MaskImage(self)
        self.initui()
    
    def initui(self):
        #UI connection
        self.select_folder.triggered.connect(self.selectfolder)
        self.prev.clicked.connect(self.image.prevImage)
        self.next.clicked.connect(self.image.nextImage)
        self.slider.valueChanged.connect(self.image.changeSliderValue)
        self.white_s.clicked.connect(self.image.ic.whitestart)
        self.white_e.clicked.connect(self.image.ic.whiteend)
        self.black_s.clicked.connect(self.image.ic.blackstart)
        self.black_e.clicked.connect(self.image.ic.blackend)
        self.submit.clicked.connect(self.image.ic.submit2next)
        self.zoomin.clicked.connect(self.image.ic.zoomin)
        self.zoomout.clicked.connect(self.image.ic.zoomout)
        self.image_control.clicked.connect(self.imagehu)
        self.gap.triggered.connect(self.image.ic.gapchange)
        self.add_slice.clicked.connect(self.image.addslice)
        self.imageshow.setScaledContents(True)
        self.masktable.doubleClicked.connect(self.image.tabledoubleclickchange)
        self.delete_slice.clicked.connect(self.image.deleteimage)

        self.cutout.clicked.connect(self.cutoutdraw)
        self.red_mask.clicked.connect(self.polygondraw)
        self.blue_shade.clicked.connect(self.shadedraw)
        self.cutout.setCheckable(True)
        self.red_mask.setCheckable(True)
        self.blue_shade.setCheckable(True)
        self.cutout.setAutoExclusive(True)
        self.red_mask.setAutoExclusive(True)
        self.blue_shade.setAutoExclusive(True)

        self.wide3dshow.clicked.connect(self.getwide3d)
        self.select3dshow.clicked.connect(self.getslice3d)
        self.image3d.setScaledContents(True)
        self.full3d.setScaledContents(True)

        #status
        self.maskstatus=False
    
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
        self.position(pos, scale)
    
    def mousePressEvent(self, e):
        if self.cutout.isChecked()==True and len(self.image.ic.cutout)<1:
            self.image.cutoutdraw(int(self.posx), int(self.posy))
        else:
            self.cutout.setDisabled(True)
        if self.red_mask.isChecked()==True:
            self.image.savemask(int(self.posx), int(self.posy))
        if self.blue_shade.isChecked()==True:
            self.image.saveshade(int(self.posx), int(self.posy))
    
    def position(self, pos, scale):
        self.label_position.setText("(%d, %d)" % (pos.x()/scale, pos.y()/scale))
        self.label_position.adjustSize()
        self.posx=pos.x()/scale
        self.posy=pos.y()/scale

    def selectfolder(self):
        self.image.ic.selectfolder()
        self.image.imageLoad_nomask()
    
    def getScale(self):
        return self.image.ic.setScale()
    
    def imagehu(self):
        if self.image.ic.hu==False:
            self.image.ic.hu=True
        else:
            self.image.ic.hu=False
        if self.maskstatus==False:
            self.image.imageLoad_nomask()
        else:
            self.image.imageLoad_mask()
    
    def cutoutdraw(self):
        if self.cutout.isChecked()==True:
            #self.cutout.setChecked(True)
            pass
        else:
            self.cutout.setChecked(False)
    
    def polygondraw(self):
        if self.red_mask.isChecked()==True:
            self.red_mask.setChecked(True)
        else:
            self.red_mask.setChecked(False)
    
    def shadedraw(self):
        if self.blue_shade.isChecked()==True:
            self.blue_shade.setChecked(True)
        else:
            self.blue_shade.setChecked(False)
    
    def getslicedatareturn(self):
        data=self.image.setslicedatareturn()
        return data

    def getslice3d(self):
        data=self.getslicedatareturn()
        id=q3d.Show3d(data, self, self.image.ic.folder)
        id.cropingimage()
        id.show3d()
    
    def getwide3d(self):
        data=self.image.ic.data
        id=q3d.Show3d(data, self, self.image.ic.folder)
        id.cropingimage()
        id.show3d()

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()