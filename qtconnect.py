import sys
import os
import pydicom
import numpy as np
import PyQt5.QtCore as QtCore
from PIL import Image, ImageDraw 
from PyQt5.QtCore import Qt
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWidgets import QFileDialog, QDialog, QLabel
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen

form_class = uic.loadUiType("./qtdesigner.ui")[0]

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


class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setMouseTracking(True)

        #UI connection
        self.select_folder.clicked.connect(self.selectfolder)
        self.slider.valueChanged.connect(self.update_image)
        self.slider2.setDisabled(True)
        self.slider2.valueChanged.connect(self.selected_image)
        self.white_s.clicked.connect(self.whitestart)
        self.white_e.clicked.connect(self.whiteend)
        self.black_s.clicked.connect(self.blackstart)
        self.black_e.clicked.connect(self.blackend)
        self.add_crop.clicked.connect(self.cropimage)
        self.submit.clicked.connect(self.submitted)
        self.white_pen.clicked.connect(self.whitecrop)
        self.black_pen.clicked.connect(self.blackcrop)
        self.crop.clicked.connect(self.cropbutton)

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
        self.black=False
        self.tempcrop=[]
        self.crop_rw=[]
        self.crop_rb=[]
        self.posx=0
        self.posy=0

        #images with pixmap
        self.pixmap=QPixmap()

        # mouse tracking
        tracker = MouseTracker(self.image)
        tracker.positionChanged.connect(self.on_positionChanged)
        self.label_position = QLabel(
            self.image, alignment=QtCore.Qt.AlignCenter
        )
        self.label_position.setStyleSheet('background-color: white; border: 1px solid black')
        

    def selectfolder(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        self.folder = QFileDialog.getExistingDirectory(self, "Select Folder", options=options)
        self.files = [f for f in os.listdir(self.folder) if f.endswith(".dcm")]
        self.files = sorted(self.files)
        self.slider.setRange(0, len(self.files)-1)
        self.foldername.append(self.folder)
        self.update_image()
    
    def update_image(self):
        self.current_index=self.slider.value()
        file_path = os.path.join(self.folder, self.files[self.current_index])
        dicom_data = pydicom.dcmread(file_path)
        image = dicom_data.pixel_array.astype(float)
        image = (np.maximum(image,0)/image.max())*255
        image = np.uint8(image)
        height, width = image.shape
        bytes_per_line = width
        qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        self.pixmap=QPixmap.fromImage(qimage)
        self.image.setPixmap(self.pixmap)

    def whitestart(self):
        self.white_start.append(self.files[self.current_index])
        self.result.append(self.files[self.current_index])
    
    def whiteend(self):
        self.white_end.append(self.files[self.current_index])
        self.result.append(self.files[self.current_index])

    def blackstart(self):
        self.black_start.append(self.files[self.current_index])
        self.result.append(self.files[self.current_index])

    def blackend(self):
        self.black_end.append(self.files[self.current_index])
        self.result.append(self.files[self.current_index])

    def cropimage(self):
        self.crop_image.append(self.files[self.current_index])
        self.result.append(self.files[self.current_index])

    def submitted(self):
        if len(self.crop_image)!=0 and len(self.white_start)==1 and len(self.white_end)==1 and len(self.black_start)==1 and len(self.black_end)==1:
            self.white_s.setDisabled(True)
            self.white_e.setDisabled(True)
            self.black_s.setDisabled(True)
            self.black_e.setDisabled(True)
            self.add_crop.setDisabled(True)
            self.current_index=0
            self.slider2.setRange(0, len(self.crop_image)-1)
            self.slider2.setEnabled(True)
            self.slider.setDisabled(True)
            self.selected_image()
        else:
            self.white_start.clear()
            self.white_end.clear()
            self.black_start.clear()
            self.black_end.clear()
            self.crop_image.clear()
            self.result.clear()
            dlg = QDialog(self)
            dlg.setWindowTitle("Error")
            dlg.exec()

    def selected_image(self):
        self.current_index=self.slider2.value()
        file_path = os.path.join(self.folder, self.crop_image[self.current_index])
        dicom_data = pydicom.dcmread(file_path)
        image = dicom_data.pixel_array.astype(float)
        image = (np.maximum(image,0)/image.max())*255
        image = np.uint8(image)
        print(type(image))
        height, width = image.shape
        bytes_per_line = width
        qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        self.pixmap=QPixmap.fromImage(qimage)
        self.image.setPixmap(self.pixmap)

    def mousePressEvent(self, e):
        if self.white==True or self.black==True:
            self.tempcrop.append((self.posx, self.posy))
        else:
            pass

    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_positionChanged(self, pos):
        delta = QtCore.QPoint(30, -15)
        self.label_position.show()
        self.label_position.move(pos + delta)
        self.label_position.setText("(%d, %d)" % (pos.x(), pos.y()))
        self.label_position.adjustSize()
        self.posx=pos.x()
        self.posy=pos.y()  

    def whitecrop(self):
        self.white=True
    
    def blackcrop(self):
        self.black=True
    
    def cropbutton(self):
        if self.white==True:
            self.crop_rw.append(self.tempcrop)
            self.tempcrop=[]
            self.white=False
            self.croped_image_show(True, False, self.current_index)
        if self.black==True:
            self.crop_rb.append(self.tempcrop)
            self.tempcrop=[]
            self.black=False
            self.croped_image_show(False, True, self.current_index)
        print(self.crop_rw)

    def croped_image_show(self, white, black, index):
        if white==True:
            file_path = os.path.join(self.folder, self.crop_image[index])
            dicom_data = pydicom.dcmread(file_path)
            image = dicom_data.pixel_array.astype(float)
            image = (np.maximum(image,0)/image.max())*255
            image = np.uint8(image)

            maskIm =Image.new('L', (image.shape[1], image.shape[0]), 0)
            ImageDraw.Draw(maskIm).polygon(self.crop_rw[0], outline=1, fill=1)
            mask=np.array(maskIm)
            newImArray=np.empty(image.shape, dtype='uint8')
            newImArray[:, :]=image[:, :]
            newImArray[:,:]=mask*newImArray[:, :]

            height, width = newImArray.shape
            bytes_per_line = width
            qimage = QImage(newImArray.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
            pixmap=QPixmap.fromImage(qimage)
            self.Showcroped.setPixmap(pixmap)
            self.crop_rw.clear()
            
        if black==True:
            file_path = os.path.join(self.folder, self.crop_image[index])
            dicom_data = pydicom.dcmread(file_path)
            image = dicom_data.pixel_array.astype(float)
            image = (np.maximum(image,0)/image.max())*255
            image = np.uint8(image)

            maskIm =Image.new('L', (image.shape[1], image.shape[0]), 0)
            ImageDraw.Draw(maskIm).polygon(self.crop_rb[0], outline=1, fill=1)
            mask=np.array(maskIm)
            newImArray=np.empty(image.shape, dtype='uint8')
            newImArray[:, :]=image[:, :]
            newImArray[:,:]=mask*newImArray[:, :]

            height, width = newImArray.shape
            bytes_per_line = width
            qimage = QImage(newImArray.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
            pixmap=QPixmap.fromImage(qimage)
            self.Showcroped_2.setPixmap(pixmap)
            self.crop_rb.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()