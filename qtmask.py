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
        self.ic.imageshow(image)

    def imageLoad_mask(self):
        image=self.ic.imagecall()
        for tup in self.ic.data['polygon'][self.ic.current_index-1]:
            image[tup[1]][tup[0]]=[255, 0, 0]
        for tup in self.ic.data['shade'][self.ic.current_index-1]:
            image[tup[1]][tup[0]]=[0, 255, 0]
        image=image[self.ic.cutout[0][0]:self.ic.cutout[1][0]][self.ic.cutout[0][1]:self.ic.cutout[1][1]]
        self.ic.imageshow(image)
    
    def cutoutdraw(self, posx, posy):
        image=self.ic.imagecall()
        self.ic.cutout.append((posx, posy))
        print(self.ic.cutout)
        for tup in self.ic.cutout:
            image[tup[1], tup[0]]=[0, 0, 255]
        self.ic.imageshow(image)

    def updatechart(self):
        datatrue=self.ic.data.loc[self.ic.data['slice']==True]
        
        pass

    def tabledoubleclickchange(self):
        row=self.slicetable.currentRow()
        index=int(self.slicetable.item(row, 0).text())
        self.current_index=index
        self.slider.setValue(self.current_index)
        self.update_image()