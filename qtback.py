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

#mouse location track class
class MouseTracker(QtCore.QObject):
    positionChanged = QtCore.pyqtSignal(QtCore.QPoint)

    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self.widget.setMouseTracking(True)
        self.widget.installEventFilter(self)

    @property
    def widget(self):
        return self._widget

    def eventFilter(self, o, e):
        if o is self.widget and e.type() == QtCore.QEvent.MouseMove:
            self.positionChanged.emit(e.pos())
        return super().eventFilter(o, e)


class ImageSet:
    def __init__(self, parents):
        self.folder=""
        self.files=[]
        self.currentindex=0
        self.length=0
        self.parents=parents
        self.pixmap=QPixmap()
        self.rawData={
            'filename':[],
            'slicenum':[],
            'canine start':[],
            'canine end':[],
            'cavity start':[],
            'cavity end':[],
            'slice':[],
        }
        self.data=pd.DataFrame(self.rawData)

    def selectfolder(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        self.folder = QFileDialog.getExistingDirectory(self.parents, "Select Folder", options=options)
        self.files = [f for f in os.listdir(self.folder) if f.endswith(".dcm")]
        self.files = sorted(self.files)
        self.data['filename']=self.files
        self.length=len(self.files)
        
    
    def setSliderRange(self):
        self.parents.slider.setRange(1, self.length)
    
    def setImageIndex(self, frame, elem, exeinfo):
        self.parents.slider.setValue(self.current_index)
        self.parents.currentindex.clear()
        self.parents.currentindex.append(str(self.current_index))

class ImageControl(ImageSet):
    def __init__(self, parents):
        super().__init__(parents)
        self.hu=False
        self.scale=0.5
    
    def transform_to_hu(self, image, level, window):
        max=level+window/2
        min=level-window/2
        image=image.clip(min, max)
        return image

    def setScale(self):
        return self.scale
    
    def zoomin(self):
        self.scale*=1.5
    
    def zoomout(self):
        self.scale=0.5

    def resizeimage(self):
        size = self.pixmap.size()
        self.parents.scrollAreaWidgetContents.resize(self.scale*size)
        self.parents.transparent.resize(self.scale*size)
        self.parents.imageshow.resize(self.scale*size)
    
    def imagecall(self):
        file_path = os.path.join(self.folder, self.data['filename'][self.currentindex])
        dicom_data = pydicom.dcmread(file_path)
        image = dicom_data.pixel_array.astype(float)
                #HU
        image = (np.maximum(image,0)/image.max())*255
        image = np.uint8(image)
        height, width= image.shape
        image = Image.fromarray(image)
        image = image.resize((height*2, width*2), Image.BICUBIC)
        image = np.array(image)
        image = np.uint8(image)
        height, width= image.shape
        image = np.repeat(image[..., np.newaxis], 3, -1)
        return image

    def imageshow(self, image):
        height, width, rgb = image.shape
        bytes_per_line = width*3
        qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.pixmap=QPixmap.fromImage(qimage)
        self.parents.imageshow.setPixmap(self.pixmap)
        self.resizeimage()

    def cropingimage(self, white, index):
        if white==True:
            file_path = os.path.join(self.folder, self.crop_image[index][0])
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
            ImageDraw.Draw(maskIm).polygon(self.crop_rw[0], outline=1, fill=1)
            mask=np.array(maskIm)
            newImArray=np.empty(image.shape, dtype='uint8')
            newImArray[:, :]=image[:, :]
            newImArray[:,:]=mask*newImArray[:, :]
            #add shade
            for m in self.mean:
                self.shade+=newImArray[m[1]][m[0]]
            self.shade/=len(self.mean)
            self.shade=int(self.shade)
            self.mean=[]
            for idx1, e1 in enumerate(newImArray):
                for idx2, e2 in enumerate(e1):
                    if e2<=self.shade:
                        newImArray[idx1][idx2]=1
                    else:
                        newImArray[idx1][idx2]=0
            self.shade=0
            self.save_croped.append(newImArray)
            self.crop_rw.clear()
            if index+1==len(self.crop_image):
                self.show3d()