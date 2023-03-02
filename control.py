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
            self.calculate,
            self.table_doubleclick_change,
            self.table_delete_row
        )
        self.init_variables()
        
    
    def init_variables(self):
        self.scale=0.5
        self.index=0
        self.hu=False
        self.slice=[]
        self.wide=[]
        self.dic_crop={}

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

    def table_doubleclick_change(self):
        i=self.view.current_row()
        self.index=i
        self.view.set_pixmap_image()
    def table_delete_row(self):
        i=self.view.current_row()
        self.model.set_slice_tf(i, False)
        self.model.data['polygon'][i]=[]
        self.model.data['shade'][i]=[]
        self.view.remove_row()
        self.view.set_pixmap_image()
        

    def plot_slice_image(self):
        self.slice=[]
        data=self.model.get_slice_data()
        self.croping_image(data, 's')
        self.make_3d_plot('s')
    def plot_wide_image(self):
        self.wide=[]
        data=self.model.get_wide_data()
        self.croping_image(data, 'w')
        self.make_3d_plot('w')
    def croping_image(self, data, str):
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

            if len(d['polygon'])!=0:
                ImageDraw.Draw(maskIm).polygon(data['polygon'][i], outline=1, fill=1)
                mask=np.array(maskIm)
                newImArray=np.empty(image.shape, dtype='uint8')
                newImArray[:, :]=image[:, :]
                newImArray[:,:]=mask*newImArray[:, :]
            else:
                newImArray=np.array(image)

            #add shade
            if len(d['shade'])!=0:
                shade=0
                for m in data['shade'][i]:
                    shade+=newImArray[m[1]][m[0]]
                shade/=len(data['shade'][i])
                shade=int(shade)
            else:
                shade=100

            for idx1, e1 in enumerate(newImArray):
                for idx2, e2 in enumerate(e1):
                    if e2<=shade:
                        newImArray[idx1][idx2]=1
                    else:
                        newImArray[idx1][idx2]=0
            if str=='s':
                self.slice.append((int(d['slicenum']), newImArray))
            else:
                self.wide.append((int(d['slicenum']), newImArray))
    def make_3d_plot(self, str):
        fig = plt.figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(projection="3d")
        x=[]
        y=[]
        z=[]
        if str=='s':
            imagearray=self.slice
        else:
            imagearray=self.wide
        for e in imagearray:
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
        pixmap=pixmap.scaled(241, 241)
        if str=='s':
            self.view.slice3d.setPixmap(pixmap)
        else:
            self.view.wide3d.setPixmap(pixmap)
        plt.close(fig)


    def calculate(self):
        for idx, e in enumerate(self.slice):
            e0=e[0]
            e1=e[1]
            outside_result=self.calculate_layer(np.array(e1).tolist())
            inside_result=e1.shape[0]*e1.shape[1]-outside_result
            all1s = np.count_nonzero(e==1)
            white_space=e1.shape[0]*e1.shape[1]-all1s
            black_space=inside_result-white_space
            slicenum=e0
            self.dic_crop[slicenum]=(inside_result, black_space)
        white_volume=self.dic_crop.copy()
        white_volume[self.model.canine_start]=(0, 0)
        white_volume[self.model.canine_end]=(0, 0)
        black_volume=self.dic_crop.copy()
        black_volume[self.model.cavity_start]=(0, 0)
        black_volume[self.model.cavity_end]=(0, 0)
        self.calculate_done(white_volume, black_volume)
    def calculate_layer(self, grid: List[List[int]]) -> int:
        m = len(grid)
        n = len(grid[0])

        # creating a queue that will help in bfs traversal
        q = deque()
        area = 0
        ans = 0
        for i in range(m):
            for j in range(n):
                # if the value at any particular cell is 1 then
                # from here we need to do the BFS traversal
                if grid[i][j] == 1:
                    ans = 0
                    # pushing the pair(i,j) in the queue
                    q.append((i, j))
                    # marking the value 1 to -1 so that we
                    # don't again push this cell in the queue
                    grid[i][j] = -1
                    while len(q) > 0:
                        t = q.popleft()
                        ans += 1
                        x, y = t[0], t[1]
                        # now we will check in all 8 directions
                        if x + 1 < m:
                            if grid[x + 1][y] == 1:
                                q.append((x + 1, y))
                                grid[x + 1][y] = -1
                        if x - 1 >= 0:
                            if grid[x - 1][y] == 1:
                                q.append((x - 1, y))
                                grid[x - 1][y] = -1
                        if y + 1 < n:
                            if grid[x][y + 1] == 1:
                                q.append((x, y + 1))
                                grid[x][y + 1] = -1
                        if y - 1 >= 0:
                            if grid[x][y - 1] == 1:
                                q.append((x, y - 1))
                                grid[x][y - 1] = -1
                        if x + 1 < m and y + 1 < n:
                            if grid[x + 1][y + 1] == 1:
                                q.append((x + 1, y + 1))
                                grid[x + 1][y + 1] = -1
                        if x - 1 >= 0 and y + 1 < n:
                            if grid[x - 1][y + 1] == 1:
                                q.append((x - 1, y + 1))
                                grid[x - 1][y + 1] = -1
                        if x - 1 >= 0 and y - 1 >= 0:
                            if grid[x - 1][y - 1] == 1:
                                q.append((x - 1, y - 1))
                                grid[x - 1][y - 1] = -1
                        if x + 1 < m and y - 1 >= 0:
                            if grid[x + 1][y - 1] == 1:
                                q.append((x + 1, y - 1))
                                grid[x + 1][y - 1] = -1
                    area = max(area, ans)
        return area
    def calculate_done(self, w, b):
        gap=self.model.get_gap()
        white_volume=0
        black_volume=0
        for key in iter(sorted(w.keys())):
            white_volume+=(key-next(iter(sorted(w.keys()))))*gap/3*(w[key][0]+w[next(iter(sorted(w.keys())))][0]+(w[key][0]*w[next(iter(sorted(w.keys())))][0])**(1/2))
        for key in iter(sorted(b.keys())):
            black_volume+=(key-next(iter(sorted(b.keys()))))*gap/3*(b[key][1]+b[next(iter(sorted(b.keys())))][1]+(b[key][1]*b[next(iter(sorted(b.keys())))][1])**(1/2))
        if (abs(white_volume)-abs(black_volume))==0:
            self.dic_crop={}
            return
        self.view.show_result(abs(white_volume), abs(black_volume), abs(black_volume)/(abs(white_volume)-abs(black_volume)))

if __name__ == "__main__":
    exitcode=ui.WindowClass.EXIT_CODE_REBOOT
    while exitcode==ui.WindowClass.EXIT_CODE_REBOOT:
        app = QApplication(sys.argv)
        c=Control()
        c.view.show()
        exitcode=app.exec_()
        app=None