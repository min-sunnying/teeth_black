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


class Data:
    def __init__(self):
        self.gap=10
        self.rawData={
            'filename':[],
            'slicenum':[],
            'slice':[],
            'polygon':[],
            'shade':[]
        }
        self.canine_start=0
        self.canine_end=0
        self.cavity_start=0
        self.cavity_end=0
    
    def init_data(self, folder):
        self.folder=folder
        files = [f for f in os.listdir(self.folder) if f.endswith(".dcm")]
        files = sorted(files)
        self.rawData['filename']=files
        self.length=len(files)
        for i in range(self.length):
            self.rawData['slicenum'].append(int(files[i][0:5]))
            self.rawData['slice'].append(False)
            self.rawData['polygon'].append([])
            self.rawData['shade'].append([])
        self.data=pd.DataFrame(self.rawData)

    #update function
    def set_slice_tf(self, index, tf):
        self.data['slice'][index]=tf

    def set_polygon(self, index, tup):
        self.data['polygon'][index].append(tup)

    def set_shade(self, index, tup):
        self.data['shade'][index].append(tup)
    
    def set_gap(self, gap):
        self.gap=gap
    
    def set_canine_start(self, index):
        self.canine_start=index
    
    def set_canine_end(self, index):
        self.canine_end=index

    def set_cavity_start(self, index):
        self.cavity_start=index
    
    def set_cavity_end(self, index):
        self.canine_end=index
    
    #get function
    def get_length(self):
        return self.length

    def get_folder(self):
        return self.folder
    
    def get_filename(self, index):
        return self.data['filename'][index]
    
    def get_slice_data(self):
        return self.data.loc[self.data['slice']==True]
    
    def get_polygon(self, index):
        return self.data['polygon'][index]
    
    def get_shade(self, index):
        return self.data['shade'][index]

    def get_gap(self):
        return self.gap
    
    def get_wide_data(self):
        return self.data.iloc[:, self.canine_start:self.canine_end]