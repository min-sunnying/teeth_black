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
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox
from PyQt5.QtWidgets import QFileDialog, QLabel
from PyQt5.QtGui import QImage, QPixmap

#qtdesigner import
form_class = uic.loadUiType("./qtdesigner.ui")[0]

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

#main window class
class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setMouseTracking(True)

        #UI connection
        self.select_folder.clicked.connect(self.selectfolder)
        self.slider.valueChanged.connect(self.sliderchange)
        self.white_s.clicked.connect(self.whitestart)
        self.white_e.clicked.connect(self.whiteend)
        self.black_s.clicked.connect(self.blackstart)
        self.black_e.clicked.connect(self.blackend)
        self.add_slice.clicked.connect(self.cropimage)
        self.delete_slice.clicked.connect(self.deleteimage)
        self.submit.clicked.connect(self.progress5)
        self.white_pen.clicked.connect(self.whitecrop)
        self.crop.clicked.connect(self.cropbutton)
        self.zoomin.clicked.connect(self.zoom_in)
        self.zoomout.clicked.connect(self.zoom_out)
        self.image.setScaledContents(True)
        self.gap.setRange(0,100)
        self.gap.setSingleStep(0.5)
        self.gap.valueChanged.connect(self.progress4)
        self.ratio.clicked.connect(self.calculate)
        self.shade_button.clicked.connect(self.shadeclick)
        self.whitestartbox.setSingleStep(1)
        self.whiteendbox.setSingleStep(1)
        self.blackstartbox.setSingleStep(1)
        self.blackendbox.setSingleStep(1)
        self.prev.pressed.connect(self.prevchange)
        self.next.pressed.connect(self.nextchange)
        self.slicetable.doubleClicked.connect(self.tabledoubleclickchange)
        self.whitestartbox.valueChanged.connect(self.progress2)
        self.whiteendbox.valueChanged.connect(self.progress2)
        self.blackstartbox.valueChanged.connect(self.progress2)
        self.blackendbox.valueChanged.connect(self.progress2)
        self.submit_point.clicked.connect(self.progress2submit)
        self.slicebox.valueChanged.connect(self.slicenum)
        self.image_control.clicked.connect(self.imagecontrol)
        self.delete_mask.clicked.connect(self.deletemask)

        #variables
        self.folder=""
        self.files=[]
        self.current_index=0
        self.white_start=[]
        self.white_end=[]
        self.black_start=[]
        self.black_end=[]
        self.crop_image=[]
        self.white=False
        self.shadeb=False
        self.tempcrop=[]
        self.crop_rw=[]
        self.crop_poly=[]
        self.posx=0
        self.posy=0
        self.scale=0.5
        self.save_croped=[]
        self.shade=0
        self.mean=[]
        self.dic_crop={}
        self.temp=[]
        watch(self.current_index, callback=self.cindex)
        self.hu=False
        self.progress5_start=False
        self.col_label=[]

        #images with pixmap
        self.pixmap=QPixmap()

        # mouse tracking
        tracker = MouseTracker(self.transparent)
        tracker.positionChanged.connect(self.on_positionChanged)
        self.label_position = QLabel(
            self.transparent, alignment=QtCore.Qt.AlignCenter
        )
        self.label_position.setStyleSheet('background-color: white; border: 1px solid black')
        
    #selected folder read images
    def selectfolder(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        self.folder = QFileDialog.getExistingDirectory(self, "Select Folder", options=options)
        self.files = [f for f in os.listdir(self.folder) if f.endswith(".dcm")]
        self.files = sorted(self.files)
        self.slider.setRange(0, len(self.files)-1)
        self.foldername.append(self.folder)
        self.progress1()
        self.update_image()
    
    def cindex(self, frame, elem, exeinfo):
        self.slider.setValue(self.current_index)
        self.slicebox.setValue(self.current_index)
        self.currentindex.clear()
        self.currentindex.append(str(self.current_index))

    def sliderchange(self):
        self.current_index=self.slider.value()
        if self.progress5_start==False:
            self.update_image()
        else:
            self.selected_image()
    
    def prevchange(self):
        if self.current_index!=0:
            self.current_index-=1
        self.slider.setValue(self.current_index)
        if self.progress5_start==False:
            self.update_image()
        else:
            self.selected_image()

    def nextchange(self):
        if self.current_index!=len(self.files):
            self.current_index+=1
        self.slider.setValue(self.current_index)
        if self.progress5_start==False:
            self.update_image()
        else:
            self.selected_image()

    def tabledoubleclickchange(self):
        row=self.slicetable.currentRow()
        index=int(self.slicetable.item(row, 0).text())
        self.current_index=index
        self.slider.setValue(self.current_index)
        self.update_image()

    #read images and show on the label with qpixmap + resolution *2
    def update_image(self):
        file_path = os.path.join(self.folder, self.files[self.current_index])
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
        bytes_per_line = width
        qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        self.pixmap=QPixmap.fromImage(qimage)
        self.image.setPixmap(self.pixmap)

    def slicenum(self):
        self.current_index=self.slicebox.value()
        self.slider.setValue(self.current_index)
        self.update_image()

    #save the starting and ending points of teeth
    def whitestart(self):
        self.whitestartbox.setValue(self.current_index)
    
    def whiteend(self):
        self.whiteendbox.setValue(self.current_index)

    def blackstart(self):
        self.blackstartbox.setValue(self.current_index)

    def blackend(self):
        self.blackendbox.setValue(self.current_index)

    def progress2submit(self):
        self.white_start.append((self.files[self.whitestartbox.value()], self.whitestartbox.value()))
        self.white_end.append((self.files[self.whiteendbox.value()], self.whiteendbox.value()))
        self.black_start.append((self.files[self.blackstartbox.value()], self.blackstartbox.value()))
        self.black_end.append((self.files[self.blackendbox.value()], self.blackendbox.value()))
        self.progress3()

    #save the images to crop
    def cropimage(self):
        self.crop_image.append((self.files[self.slicebox.value()], self.slicebox.value()))
        row=self.slicetable.rowCount()
        self.slicetable.insertRow(row)
        self.slicetable.setItem(row, 0, QTableWidgetItem(str(self.current_index)))
        #print(self.slicetable.rowCount())
    
    def deleteimage(self):
        if self.slicetable.currentRow()<0:
            return QMessageBox.warning(self, 'Warning', 'Please select the record to delete!')
        row=self.slicetable.currentRow()
        index=self.slicetable.item(row, 0).text()
        self.crop_image=list(filter(lambda x: x[1]!=int(index), self.crop_image))
        self.slicetable.removeRow(row)

    def deletemask(self):
        if self.masktable.currentRow()<0:
            return QMessageBox.warning(self, 'Warning', 'Please select the record to delete!')
        row=self.masktable.currentRow()
        tup=self.masktable.item(row, self.current_index).text()
        print(tup)
        self.tempcrop=list(filter(lambda x: x!=tup, self.tempcrop))
        print(self.tempcrop)
        self.selected_image()

    def progress1(self):
        #disable
        self.foldername.setDisabled(True)
        self.select_folder.setDisabled(True)
        #enable
        self.currentindex.setEnabled(True)
        self.image_control.setEnabled(True)
        self.zoomin.setEnabled(True)
        self.zoomout.setEnabled(True)
        self.slider.setEnabled(True)
        self.prev.setEnabled(True)
        self.next.setEnabled(True)
        self.white_s.setEnabled(True)
        self.white_e.setEnabled(True)
        self.black_s.setEnabled(True)
        self.black_e.setEnabled(True)
        self.whitestartbox.setEnabled(True)
        self.whiteendbox.setEnabled(True)
        self.blackstartbox.setEnabled(True)
        self.blackendbox.setEnabled(True)
    
    def progress2(self):
        if self.whitestartbox.value()!=0 and self.whiteendbox.value()!=0 and self.blackstartbox.value()!=0 and self.blackendbox.value()!=0:
            #enable
            self.submit_point.setEnabled(True)

    def progress3(self):
        #disable
        self.white_s.setDisabled(True)
        self.white_e.setDisabled(True)
        self.black_s.setDisabled(True)
        self.black_e.setDisabled(True)
        self.whitestartbox.setDisabled(True)
        self.whiteendbox.setDisabled(True)
        self.blackstartbox.setDisabled(True)
        self.blackendbox.setDisabled(True)
        self.submit_point.setDisabled(True)
        #enable
        self.slicetable.setEnabled(True)
        self.slicebox.setEnabled(True)
        self.add_slice.setEnabled(True)
        self.delete_slice.setEnabled(True)
        self.slicegap.setEnabled(True)
        self.gap.setEnabled(True)
    
    def progress4(self):
        #enable
        if self.gap.value()!=0:
            self.submit.setEnabled(True)
    
    def progress5(self):
        #disable
        self.slicetable.setDisabled(True)
        self.slicebox.setDisabled(True)
        self.add_slice.setDisabled(True)
        self.delete_slice.setDisabled(True)
        self.slicegap.setDisabled(True)
        self.gap.setDisabled(True)   
        self.submit.setDisabled(True)  
        self.currentindex.setDisabled(True)   
        self.next.setDisabled(True)
        self.slider.setDisabled(True)
        self.prev.setDisabled(True)
        #enable
        self.white_pen.setEnabled(True)
        self.shade_button.setEnabled(True)
        self.croped_result.setEnabled(True)
        self.image3d.setEnabled(True)
        self.masktable.setEnabled(True)
        self.delete_mask.setEnabled(True)
        #else
        self.current_index=0
        self.slider.setRange(0, len(self.crop_image)-1)
        self.selected_image()
        self.progress5_start=True
        for i in self.crop_image:
            col=self.masktable.columnCount()
            self.masktable.insertColumn(col)

    def progress6(self):
        if self.white==True and self.shadeb==True:
            #enable
            self.crop.setEnabled(True)
        else:
            self.crop.setDisabled(True)
        if len(self.save_croped)==len(self.crop_image):
            self.ratio.setEnabled(True)
            self.caninevolume.setEnabled(True)
            self.cavityvolume.setEnabled(True)
            self.volumeratio.setEnabled(True)
            self.resultcanine.setEnabled(True)
            self.resultcavity.setEnabled(True)
            self.resultratio.setEnabled(True)

    def selected_image(self):
        #self.current_index=self.slider.value()
        file_path = os.path.join(self.folder, self.crop_image[self.current_index][0])
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
        row=self.masktable.rowCount()
        if row<len(self.tempcrop):
            for i in range(len(self.tempcrop)-row):
                row=self.masktable.rowCount()
                self.masktable.insertRow(row)
        if self.tempcrop!=[]:
            i=0
            for tup in self.tempcrop:
                image[tup[1]][tup[0]]=[255, 0, 0]
                self.masktable.setItem(i, self.current_index, QTableWidgetItem(str(tup)))
                i=i+1
        if self.mean!=[]: #fix
            for tup in self.mean:
                image[tup[1]][tup[0]]=[0, 255, 0]
        height, width, rgb = image.shape
        bytes_per_line = width*3
        qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.pixmap=QPixmap.fromImage(qimage)
        self.image.setPixmap(self.pixmap)
        self.resizeimage()
        self.progress6()

    def mousePressEvent(self, e):
        if self.white==True and self.shadeb==False:
            self.tempcrop.append((int(self.posx), int(self.posy)))
            self.selected_image()
        elif self.shadeb==True:
            self.mean.append((int(self.posx), int(self.posy)))
            self.selected_image()
        pass

    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_positionChanged(self, pos):
        delta = QtCore.QPoint(30, -15)
        self.label_position.show()
        self.label_position.move(pos + delta)
        self.label_position.setText("(%d, %d)" % (pos.x()/self.scale, pos.y()/self.scale))
        self.label_position.adjustSize()
        self.posx=pos.x()/self.scale
        self.posy=pos.y()/self.scale

    def whitecrop(self):
        self.white=True
    
    def cropbutton(self):
        if self.white==True:
            self.crop_rw.append(self.tempcrop)
            self.croped_result.append('|'.join(str(e) for e in self.tempcrop))
            self.crop_poly.append((self.tempcrop, self.current_index))
            self.tempcrop=[]
            self.white=False
            self.shadeb=False
            self.croped_image_show(True, self.current_index)
            self.current_index=self.current_index+1
            self.selected_image()

    def croped_image_show(self, white, index):
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
    
    #zoom in out function
    def zoom_in(self, e):
        self.scale*=1.5
        self.resizeimage()
    
    def zoom_out(self, e):
        self.scale=0.5
        self.resizeimage()

    def resizeimage(self):
        size = self.pixmap.size()
        self.scrollAreaWidgetContents.resize(self.scale*size)
        self.transparent.resize(self.scale*size)
        self.image.resize(self.scale*size)
    
    #caculate shade(find contour)
    def shadeclick(self):
        self.shadeb=True
    
    def transform_to_hu(self, image, level, window):
        max=level+window/2
        min=level-window/2
        image=image.clip(min, max)
        return image

    def imagecontrol(self):
        if self.hu==True:
            self.hu=False
        else:
            self.hu=True
        if self.progress5_start==True:
            self.selected_image()
        else:
            self.update_image()

    # draw 3d plot
    def show3d(self):
        fig = plt.figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(projection="3d")
        x=[]
        y=[]
        z=[]
        for idx1, e1 in enumerate(self.save_croped):
            for idx2, e2 in enumerate(e1):
                for idx3, e3 in enumerate(e2):
                    if e3==0:
                        x.append(idx2)
                        y.append(idx3)
                        z.append(-self.gap.value()*int(self.crop_image[idx1][0][0:5]))
        ax.scatter(x,y,z, marker='o', s=15, c='darkgreen', alpha=.25)
        ax.axis('off')
        canvas.draw()
        width, height = fig.figbbox.width, fig.figbbox.height
        img = QImage(canvas.buffer_rgba(), width, height, QImage.Format_ARGB32)
        pixmap = QPixmap(img)
        self.image3d.setPixmap(pixmap)
        # ratio button enable
        self.ratio.setEnabled(True)
        self.progress6()
        self.resizeimage()
        plt.close(fig)
    
    #calculate the each volumn
    def calculate(self):
        # how to interpolate?
        for idx1, e1 in enumerate(self.save_croped):
            outside_result=self.calculate_layer(np.array(e1).tolist())
            inside_result=e1.shape[0]*e1.shape[1]-outside_result
            all1s = np.count_nonzero(e1==1)
            white_space=e1.shape[0]*e1.shape[1]-all1s
            black_space=inside_result-white_space
            slicenum=self.crop_image[idx1][1]
            self.dic_crop[slicenum]=(inside_result, black_space)
        white_volume=self.dic_crop.copy()
        white_volume[self.white_start[0][1]]=(0, 0)
        white_volume[self.white_end[0][1]]=(0, 0)
        black_volume=self.dic_crop.copy()
        black_volume[self.black_start[0][1]]=(0, 0)
        black_volume[self.black_end[0][1]]=(0, 0)
        # print(white_volume, black_volume)
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

    #fix the eq
    def calculate_done(self, w, b):
        white_volume=0
        black_volume=0
        for key in iter(sorted(w.keys())):
            white_volume+=(key-next(iter(sorted(w.keys()))))*self.gap.value()/3*(w[key][0]+w[next(iter(sorted(w.keys())))][0]+(w[key][0]*w[next(iter(sorted(w.keys())))][0])**(1/2))
        for key in iter(sorted(b.keys())):
            black_volume+=(key-next(iter(sorted(b.keys()))))*self.gap.value()/3*(b[key][1]+b[next(iter(sorted(b.keys())))][1]+(b[key][1]*b[next(iter(sorted(b.keys())))][1])**(1/2))
        self.resultcanine.append(str(abs(white_volume)))
        self.resultcavity.append(str(abs(black_volume)))
        if (abs(white_volume)-abs(black_volume))==0:
            return
        self.resultratio.append(str(abs(black_volume)/(abs(white_volume)-abs(black_volume))))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()