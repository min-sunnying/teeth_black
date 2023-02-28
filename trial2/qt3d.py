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

class Show3d:
    def __init__(self, data, parents, folder):
        self.data=data
        self.imagearray=[]
        self.parents=parents
        self.folder=folder

    # draw 3d plot
    def show3d(self):
        fig = plt.figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(projection="3d")
        x=[]
        y=[]
        z=[]
        for e in self.imagearray:
            for idx1, e1 in enumerate(e[1]):
                for idx2, e2 in enumerate(e1):
                    if e2==0:
                        x.append(idx1)
                        y.append(idx2)
                        z.append(-self.parents.slicegap*e[0])
        ax.scatter(x,y,z, marker='o', s=15, c='darkgreen', alpha=.25)
        ax.axis('off')
        canvas.draw()
        width, height = fig.figbbox.width, fig.figbbox.height
        img = QImage(canvas.buffer_rgba(), width, height, QImage.Format_ARGB32)
        pixmap = QPixmap(img)
        plt.close(fig)

    def cropingimage(self):
        for i, d in self.data.iterrows():
            file_path = os.path.join(self.folder, self.data['filename'][i])
            dicom_data = pydicom.dcmread(file_path)
            image = dicom_data.pixel_array.astype(float)
            image = (np.maximum(image,0)/image.max())*255
            image = np.uint8(image)
            height, width= image.shape
            image = Image.fromarray(image)
            image = image.resize((height*2, width*2), Image.BICUBIC)
            image = np.array(image)
            image = np.uint8(image)
            height, width= image.shape
            maskIm =Image.new('L', (image.shape[1], image.shape[0]), 0)
            ImageDraw.Draw(maskIm).polygon(self.data['polygon'][i], outline=1, fill=1)
            mask=np.array(maskIm)
            newImArray=np.empty(image.shape, dtype='uint8')
            newImArray[:, :]=image[:, :]
            newImArray[:,:]=mask*newImArray[:, :]
            #add shade
            shade=0
            for m in self.data['shade'][i]:
                shade+=newImArray[m[1]][m[0]]
            shade/=len(self.data['shade'][i])
            shade=int(shade)
            for idx1, e1 in enumerate(newImArray):
                for idx2, e2 in enumerate(e1):
                    if e2<=shade:
                        newImArray[idx1][idx2]=1
                    else:
                        newImArray[idx1][idx2]=0
            self.imagearray.append((i, newImArray))