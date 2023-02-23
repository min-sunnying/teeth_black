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


class NoMaskImage:
    def __init__(self, parents):
        self.ic=back.ImageControl(parents)
        self.mask=False

    def nextImage(self):
        if self.length!=self.currentindex:
            self.currentindex+=1
            self.imageLoad()
    
    def prevImage(self):
        if self.currentindex!=1:
            self.currentindex-=1
            self.imageLoad()

    def changeSliderValue(self):
        self.currentindex=self.slider.value()
        self.imageLoad()

    def imageLoad_nomask(self):
        image=self.ic.imagecall()
        #Mask, Shade
        #not rgb image
        self.ic.imageshow(image)

    def imageLoad_mask(self):
        image=self.ic.imagecall()
        if self.tempcrop!=[]:
            i=0
            for tup in self.tempcrop:
                image[tup[1]][tup[0]]=[255, 0, 0]
                self.masktable.setItem(i, self.current_index, QTableWidgetItem(str(tup)))
                i=i+1
        if self.mean!=[]: #fix
            for tup in self.mean:
                image[tup[1]][tup[0]]=[0, 255, 0]
        self.ic.imageshow(image)
