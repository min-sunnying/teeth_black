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
from PyQt5.QtCore import Qt, QThread
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox, QWidget
from PyQt5.QtWidgets import QFileDialog, QLabel
from PyQt5.QtGui import QImage, QPixmap
import db as db
import gui as ui

class Control:
    def __init__(self):
        self.model=db.Data(

        )
        self.view = ui.WindowClass(
            self.select_folder_click,
            self.get_scale,
            self.image_show,
            self.get_index,
            self.set_hu,
            self.zoom_in,
            self.zoom_out,
            self.get_length,
            self.go_next,
            self.go_prev,
            self.move_slider,
            self.set_cavity_start,
            self.set_canine_end,
            self.set_cavity_start,
            self.set_cavity_end,
            self.get_slice_data,
            self.set_slice,
            self.polygon_mask_draw,
            self.shade_point_draw,
            self.plot_slice_image,
            self.plot_wide_image,
        )
        self.init_variables()
        
    
    def init_variables(self):
        self.scale=0.5
        self.index=0
        self.hu=False
        self.imagearray=[]

    def select_folder_click(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        folder = QFileDialog.getExistingDirectory(self.view, "Select Folder", options=options)
        self.model.init_data(folder)
        self.view.set_pixmap_image()
        self.view.set_slider_range()
    

    def get_scale(self):
        return self.scale
    def get_index(self):
        return self.index
    def get_length(self):
        return self.model.get_length()
    

    def set_hu(self):
        if self.hu==True:
            self.hu=False
        else:
            self.hu=True
        self.view.set_pixmap_image()
    def transform_to_hu(self, image, level, window):
        max=level+window/2
        min=level-window/2
        image=image.clip(min, max)
        return image
    def image_show(self):
        file_path = os.path.join(self.model.get_folder(), self.model.get_filename(self.index))
        dicom_data = pydicom.dcmread(file_path)
        image = dicom_data.pixel_array.astype(float)
        if self.hu==True:
            image=self.transform_to_hu(image, 400, 1800)
        image = (np.maximum(image,0)/image.max())*255
        image = np.uint8(image)
        height, width= image.shape
        image = Image.fromarray(image)
        image = image.resize((height*2, width*2), Image.BICUBIC)
        image = np.array(image)
        image = np.uint8(image)
        height, width= image.shape
        image = np.repeat(image[..., np.newaxis], 3, -1)
        
        polygon=self.model.get_polygon(self.index)
        for t in polygon:
            image[t[1]][t[0]]=[255, 0, 0]
        shade=self.model.get_shade(self.index)
        for t in shade:
            image[t[1]][t[0]]=[0, 255, 0]

        height, width, rgb = image.shape
        bytes_per_line = width*3
        qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        return qimage


    
    def zoom_in(self):
        self.scale*=1.5
        self.view.resize_image()
    def zoom_out(self):
        self.scale=0.5
        self.view.resize_image()
    


    def go_next(self):
        self.index+=1
        self.view.set_pixmap_image()
    def go_prev(self):
        self.index-=1
        self.view.set_pixmap_image()
    def move_slider(self):
        self.index=self.view.slider.value()
        self.view.set_pixmap_image()
    

    def set_canine_start(self):
        self.model.set_canine_start(self.index)
    def set_canine_end(self):
        self.model.set_canine_end(self.index)
    def set_cavity_start(self):
        self.model.set_cavity_start(self.index)
    def set_cavity_end(self):
        self.model.set_cavity_end(self.index)
    

    def get_slice_data(self):
        data=self.model.get_slice_data()
        return data
    def set_slice(self):
        self.model.set_slice_tf(self.index, True)
        self.view.update_table()
    

    def polygon_mask_draw(self, tup):
        self.model.set_polygon(self.index, tup)
    def shade_point_draw(self, tup):
        self.model.set_shade(self.index, tup)

    


    def plot_slice_image(self):
        data=self.model.get_slice_data()
        self.croping_image(data)
        self.make_3d_plot('s')
    def plot_wide_image(self):
        data=self.model.get_wide_data()
        self.croping_image(data)
        self.make_3d_plot('w')
    def croping_image(self, data):
        for i, d in data.iterrows():
            file_path = os.path.join(self.model.get_folder(), self.model.get_filename(i))
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
            if data['polygon'][i]!=[]:
                ImageDraw.Draw(maskIm).polygon(data['polygon'][i], outline=1, fill=1)
            mask=np.array(maskIm)
            newImArray=np.empty(image.shape, dtype='uint8')
            newImArray[:, :]=image[:, :]
            newImArray[:,:]=mask*newImArray[:, :]
            #add shade
            shade=0
            if data['shade'][i]!=[]:
                for m in data['shade'][i]:
                    shade+=newImArray[m[1]][m[0]]
                shade/=len(data['shade'][i])
            shade=int(shade)
            for idx1, e1 in enumerate(newImArray):
                for idx2, e2 in enumerate(e1):
                    if e2<=shade:
                        newImArray[idx1][idx2]=1
                    else:
                        newImArray[idx1][idx2]=0
            self.imagearray.append((i, newImArray))
    def make_3d_plot(self, str):
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
                        z.append(-self.model.get_gap()*e[0])
        ax.scatter(x,y,z, marker='o', s=15, c='darkgreen', alpha=.25)
        ax.axis('off')
        canvas.draw()
        width, height = fig.figbbox.width, fig.figbbox.height
        qimage = QImage(canvas.buffer_rgba(), width, height, QImage.Format_ARGB32)
        pixmap=QPixmap(qimage)
        if str=='s':
            self.view.slice3d.setPixmap(pixmap)
        else:
            self.view.wide3d.setPixmap(pixmap)
        plt.close(fig)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    c=Control()
    c.view.show()
    app.exec_()