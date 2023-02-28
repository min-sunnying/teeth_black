import pandas as pd
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
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox, QWidget
from PyQt5.QtWidgets import QFileDialog, QLabel
from PyQt5.QtGui import QImage, QPixmap
import qtback as back


class MaskImage:
    def __init__(self, parents):
        self.ic=back.ImageControl(parents)

    def nextImage(self):
        if self.ic.length!=self.ic.current_index:
            self.ic.current_index+=1
            if self.ic.parents.maskstatus==False:
                self.imageLoad_nomask()
            else:
                self.imageLoad_mask()
    
    def prevImage(self):
        if self.ic.current_index!=1:
            self.ic.current_index-=1
            if self.ic.parents.maskstatus==False:
                self.imageLoad_nomask()
            else:
                self.imageLoad_mask()

    def changeSliderValue(self):
        self.ic.current_index=self.ic.parents.slider.value()
        if self.ic.parents.maskstatus==False:
            self.imageLoad_nomask()
        else:
            self.imageLoad_mask()

    def imageLoad_nomask(self):
        image=self.ic.imagecall()
        # for tup in self.ic.cutout:
        #     image[tup[1], tup[0]]=[0, 0, 255]
        self.ic.imageshow(image)

    def imageLoad_mask(self):
        image=self.ic.imagecall()
        for tup in self.ic.data['polygon'][self.ic.row_index]:
            image[tup[1]][tup[0]]=[255, 0, 0]
        for tup in self.ic.data['shade'][self.ic.row_index]:
            image[tup[1]][tup[0]]=[0, 255, 0]
        self.ic.imageshow(image)
    
    def cutoutdraw(self, posx, posy):
        self.ic.cutout=(posx, posy)
        # self.ic.defaultscale=self.ic.scale
        self.imageLoad_nomask()
    
    def savemask(self, posx, posy):
        self.ic.data['polygon'][self.ic.row_index].append((posx, posy))
        self.imageLoad_mask()
        self.updatechart()
    
    def saveshade(self, posx, posy):
        self.ic.data['shade'][self.ic.row_index].append((posx, posy))
        self.imageLoad_mask()
        self.updatechart()

    def updatechart(self):
        datatrue=self.ic.data.loc[self.ic.data['slice']==True]
        self.ic.parents.masktable.setRowCount(0)
        for i, r in datatrue.iterrows():
            row=self.ic.parents.masktable.rowCount()
            self.ic.parents.masktable.insertRow(row)
            self.ic.parents.masktable.setItem(row, 0, QTableWidgetItem(str(r[1])))
            self.ic.parents.masktable.setItem(row, 1, QTableWidgetItem(str(r[3])))
            self.ic.parents.masktable.setItem(row, 2, QTableWidgetItem(str(r[4])))

    def tabledoubleclickchange(self):
        row=self.ic.parents.masktable.currentRow()
        index=int(self.ic.parents.masktable.item(row, 0).text())
        self.ic.current_index=index
        self.ic.parents.slider.setValue(self.ic.current_index)
        self.imageLoad_mask()
    
    def addslice(self):
        self.ic.data['slice'][self.ic.row_index]=True
        self.updatechart()

    def deleteimage(self):
        if self.ic.parents.masktable.currentRow()<0:
            return QMessageBox.warning(self, 'Warning', 'Please select the record to delete!')
        row=self.ic.parents.masktable.currentRow()
        index=self.ic.parents.masktable.item(row, 0).text()
        self.ic.data['slice'][int(index)]=False
        self.ic.data['polygon'][int(index)]=[]
        self.ic.data['shade'][int(index)]=[]
        self.ic.parents.masktable.removeRow(row)
        self.imageLoad_mask()
    
    def setslicedatareturn(self):
        datatrue=self.ic.data.loc[self.ic.data['slice']==True]
        return datatrue