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
        self.cutout=(0, 0)
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
        self.setSliderRange()
        
    def gapchange(self):
        pass

    def setSliderRange(self):
        self.current_index=1
        self.parents.slider.setRange(1, self.length)
    
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
            self.parents.maskstatus=True
            self.uichange()
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
        self.parents.wide3dshow.setEnabled(True)
        self.parents.select3dshow.setEnabled(True)

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

        

class ImageControl(ImageSet):
    def __init__(self, parents):
        super().__init__(parents)
        self.hu=False
        self.scale=0.5
        self.defaultscale=0.5
    
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
        self.scale=self.defaultscale
        self.resizeimage()

    def resizeimage(self):
        size = self.pixmap.size()
        self.parents.scrollAreaWidgetContents.resize(self.scale*size)
        self.parents.transparent.resize(self.scale*size)
        self.parents.imageshow.resize(self.scale*size)
    
    def image_call(self):
        file_path = os.path.join(self.folder, self.data['filename'][self.row_index])
        dicom_data = pydicom.dcmread(file_path)
        image = dicom_data.pixel_array.astype(float)
                #HU
        image = self.transform_to_hu(image)
                #HU
        image = (np.maximum(image,0)/image.max())*255
        image = np.uint8(image)
        height, width= image.shape
        image = Image.fromarray(image)
        image = image.resize((height*2, width*2), Image.BICUBIC)
        image = np.array(image)
        height, width= image.shape
        x1=int(self.cutout[0])
        x2=int(x1+height/(2*self.scale))
        y1=int(self.cutout[1])
        y2=int(x2-x1+y1)
        # image=image[ y1:y2, x1:x2]
        image = np.uint8(image)
        image = np.repeat(image[..., np.newaxis], 3, -1)
        return image

    def image_show(self, image):
        height, width, rgb = image.shape
        bytes_per_line = width*3
        qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.pixmap=QPixmap.fromImage(qimage)
        self.parents.imageshow.setPixmap(self.pixmap)
        self.resizeimage()