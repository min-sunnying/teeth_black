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
        self.cutout=[]
        self.current_index=0
        self.parents=parents
        self.rawData={
            'filename':[],
            'slicenum':[],
            'slice':[],
            'polygon':[],
            'shade':[]
        }

        watch(self.current_index, callback=self.setImageIndex)

    def selectfolder(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        self.folder = QFileDialog.getExistingDirectory(self.parents, "Select Folder", options=options)
        self.files = [f for f in os.listdir(self.folder) if f.endswith(".dcm")]
        self.files = sorted(self.files)
        self.rawData['filename']=self.files
        self.length=len(self.files)
        for i in range(self.length):
            self.rawData['slicenum'].append(int(self.files[i][0:5]))
            self.rawData['slice'].append(False)
            self.rawData['polygon'].append([])
            self.rawData['shade'].append([])
        self.data=pd.DataFrame(self.rawData)
        print(self.data)
        self.setSliderRange()
        
    def gapchange(self):
        pass

    def setSliderRange(self):
        self.current_index=1
        self.parents.slider.setRange(1, self.length+1)
    
    def setImageIndex(self, frame, elem, exeinfo):
        self.row_index=self.current_index-1
        self.parents.slider.setValue(int(self.data['slicenum'][self.row_index]))
        self.parents.currentindex.clear()
        self.parents.currentindex.append(str(self.current_index))

    #save the starting and ending points of teeth
    def whitestart(self):
        self.parents.whitestartbox.setValue(self.current_index)
    
    def whiteend(self):
        self.parents.whiteendbox.setValue(self.current_index)

    def blackstart(self):
        self.parents.blackstartbox.setValue(self.current_index)

    def blackend(self):
        self.parents.blackendbox.setValue(self.current_index)
    
    def submit2next(self):
        if self.parents.whitestartbox.value()!=0 and self.parents.whiteendbox.value()!=0 and self.parents.blackstartbox.value()!=0 and self.parents.blackendbox.value()!=0 and len(self.cutout)==2:
            self.canine_start=self.parents.whitestartbox.value()
            self.canine_end= self.parents.whiteendbox.value()
            self.cavity_start=self.parents.blackstartbox.value()
            self.cavity_end=self.parents.blackendbox.value()
            self.uichange()
            self.maskset()
        else:
            return QMessageBox.warning(self.parents, 'Warning', 'Please set proper values.')
    
    def uichange(self):
        self.parents.add_slice.setEnabled(True)
        self.parents.delete_slice.setEnabled(True)
        self.parents.red_mask.setEnabled(True)
        self.parents.blue_shade.setEnabled(True)
        self.parents.masktable.setEnabled(True)
        self.parents.caninevolume.setEnabled(True)
        self.parents.cavityvolume.setEnabled(True)
        self.parents.volumeratio.setEnabled(True)
        self.parents.resultcanine.setEnabled(True)
        self.parents.resultcavity.setEnabled(True)
        self.parents.resultratio.setEnabled(True)

        self.parents.white_s.setDisabled(True)
        self.parents.white_e.setDisabled(True)
        self.parents.black_s.setDisabled(True)
        self.parents.black_e.setDisabled(True)
        self.parents.whitestartbox.setDisabled(True)
        self.parents.whiteendbox.setDisabled(True)
        self.parents.blackstartbox.setDisabled(True)
        self.parents.blackendbox.setDisabled(True)
        self.parents.submit.setDisabled(True)
        self.parents.cutout.setDisabled(True)

    def maskset(self):
        self.data=self.data.loc[self.parents.whitestartbox.value():self.parents.whiteendbox.value()]
        self.length=len(self.data['slicenum'])
        self.current_index=int(self.data['slicenum'][1])

        

class ImageControl(ImageSet):
    def __init__(self, parents):
        super().__init__(parents)
        self.hu=False
        self.scale=0.5
    
    def transform_to_hu(self, image):
        if self.hu==True:
            level=400
            window=1800
            max=level+window/2
            min=level-window/2
            image=image.clip(min, max)
            return image
        else:
            return image

    def setScale(self):
        return self.scale
    
    def zoomin(self):
        self.scale*=1.5
        self.resizeimage()
    
    def zoomout(self):
        self.scale=0.5
        self.resizeimage()

    def resizeimage(self):
        size = self.pixmap.size()
        self.parents.scrollAreaWidgetContents.resize(self.scale*size)
        self.parents.transparent.resize(self.scale*size)
        self.parents.imageshow.resize(self.scale*size)
    
    def imagecall(self):
        file_path = os.path.join(self.folder, self.data['filename'][self.current_index-1])
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
        image = np.repeat(image[..., np.newaxis], 3, -1)
                #HU
        image = self.transform_to_hu(image)
                #HU
        return image

    def imageshow(self, image):
        height, width, rgb = image.shape
        bytes_per_line = width*3
        qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.pixmap=QPixmap.fromImage(qimage)
        self.parents.imageshow.setPixmap(self.pixmap)
        self.resizeimage()

    def cropingimage(self):
        image=self.imagecall()
        maskIm =Image.new('L', (image.shape[1], image.shape[0]), 0)
        ImageDraw.Draw(maskIm).polygon(self.data['polygon'][self.current_index], outline=1, fill=1)
        mask=np.array(maskIm)
        newImArray=np.empty(image.shape, dtype='uint8')
        newImArray[:, :]=image[:, :]
        newImArray[:,:]=mask*newImArray[:, :]
        #add shade
        shade=0
        for m in self.data['shade'][self.current_index]:
            shade+=newImArray[m[1]][m[0]]
        shade/=len(self.data['shade'][self.current_index])
        shade=int(shade)
        for idx1, e1 in enumerate(newImArray):
            for idx2, e2 in enumerate(e1):
                if e2<=self.shade:
                    newImArray[idx1][idx2]=1
                else:
                    newImArray[idx1][idx2]=0
        self.data['shade'][self.current_index]=newImArray