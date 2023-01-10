import sys
import os
import pydicom
import numpy as np
import PyQt5.QtCore as QtCore

from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QHBoxLayout, QVBoxLayout, QLabel, QScrollBar, QStackedWidget, QCheckBox, QGridLayout, QPushButton, QGraphicsScene, QGraphicsView, QAction, QMainWindow
from PyQt5.QtGui import QPixmap, QImage, QColor, QPolygon, QPainter, QBrush, QPen, QMouseEvent
from PyQt5.QtCore import Qt, QPoint

selected_images=[]
initial_teeth=[]
final_teeth=[]
initial_void=[]
final_void=[]

class DicomViewer(QWidget):
    def __init__(self):
        super().__init__()

        # Initialize variables
        self.folder = ""
        self.files = []
        self.current_index = 0
        self.pixmap = QPixmap()
        self.selected_images=[]

        self.checkbox1 = QCheckBox('initial teeth')
        self.checkbox2 = QCheckBox('final teeth')
        self.checkbox3 = QCheckBox('initial void teeth')
        self.checkbox4 = QCheckBox('final void teeth')
        self.checkbox = QCheckBox('add image lasso')

        self.button = QPushButton('Next', self)
        self.button.clicked.connect(self.nextPage)
        self.buttonconfirm = QPushButton('Add image', self)
        self.buttonconfirm.clicked.connect(self.update_image)

        # Set up the user interface
        self.label = QLabel('Page Dicom Viewer', self)
        self.scroll_bar = QScrollBar(Qt.Horizontal)
        self.scroll_bar.valueChanged.connect(self.update_image)
        self.grid_layout = QGridLayout()
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.scroll_bar)
        layout.addLayout(self.grid_layout)
        layout.addWidget(self.button)
        layout.addWidget(self.buttonconfirm)
        layout.addWidget(self.checkbox)
        layout.addWidget(self.checkbox1)
        layout.addWidget(self.checkbox2)
        layout.addWidget(self.checkbox3)
        layout.addWidget(self.checkbox4)
        self.setLayout(layout)
        self.select_folder()

    def select_folder(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        self.folder = QFileDialog.getExistingDirectory(self, "Select Folder", options=options)
        self.files = [f for f in os.listdir(self.folder) if f.endswith(".dcm")]
        self.files = sorted(self.files)
        self.scroll_bar.setRange(0, len(self.files)-1)
        self.update_image()

    def update_image(self):
        self.current_index = self.scroll_bar.value()
        file_path = os.path.join(self.folder, self.files[self.current_index])
        dicom_data = pydicom.dcmread(file_path)
        image = dicom_data.pixel_array.astype(float)
        image = (np.maximum(image,0)/image.max())*255
        image = np.uint8(image)
        height, width = image.shape
        bytes_per_line = width
        qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        self.pixmap = QPixmap.fromImage(qimage)
        self.pixmap=self.pixmap.scaled(900, 900)
        self.label.setPixmap(self.pixmap)
        self.checkbox_state_changed(image)
        self.checkbox.setChecked(False)
        self.checkbox1.setChecked(False)
        self.checkbox2.setChecked(False)
        self.checkbox3.setChecked(False)
        self.checkbox4.setChecked(False)

    def checkbox_state_changed(self, image):
        if self.checkbox.isChecked():
            # Update the image based on the checked state of the checkbox
            self.selected_images.append(image)

        if self.checkbox1.isChecked():
            initial_teeth.append(image)
        
        if self.checkbox2.isChecked():
            final_teeth.append(image)

        if self.checkbox3.isChecked():
            initial_void.append(image)
        
        if self.checkbox4.isChecked():
            final_void.append(image)

        print(self.selected_images,initial_teeth,final_teeth,initial_void,final_void)

    def nextPage(self):
        self.stack.setCurrentIndex(1)

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
    


class Lasso(QMainWindow):
    def __init__(self, page1):
        super().__init__()
        self.page1 = page1
        self.current_index = 0

        self.button = QPushButton('Previous', self)
        self.button.clicked.connect(self.prevPage)
        self.button_n = QPushButton('Next', self)
        self.button_n.clicked.connect(self.nextPage)

        self.folder=self.page1.folder
        self.files=self.page1.files
        self.images=self.page1.selected_images

        self.scroll_bar = QScrollBar(Qt.Horizontal)
        self.scroll_bar.valueChanged.connect(self.update_image)

        layout = QHBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.button_n)
        layout.addWidget(self.scroll_bar)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.painter=QPainter()

    def update_image(self):
        if len(self.images)!=0:
            self.scroll_bar.setRange(0, len(self.images)-1)
            self.current_index = self.scroll_bar.value()
            image = self.images[self.current_index]
            height, width = image.shape
            bytes_per_line = width
            qimage = QImage(image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
            self.painter=QPainter(qimage)
    
    def paintEvent(self, event, qimage):
        self.painter.drawImage(self.rect(), qimage, qimage.rect())

    def mouseMoveEvent(self, event):
        # Draw a line from the previous mouse position to the current mouse position
        self.painter.drawLine(self.prev_pos, event.pos())

        # Update the previous mouse position
        self.prev_pos = event.pos()

        # Update the widget to show the new line
        self.update()

    def mousePressEvent(self, event):
        # Set the initial mouse position
        self.prev_pos = event.pos()

    def prevPage(self):
        self.stack.setCurrentIndex(0)
    
    def nextPage(self):
        self.stack.setCurrentIndex(2)

class Draw(QWidget):
    def __init__(self, image):
        super().__init__()

        self.image=image

        self.painter=QPainter(self.image)
        self.painter.setPen(QPen(Qt.red, 5))

    def paintEvent(self, event):
        # Draw the QImage onto the widget
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.image, self.image.rect())

    def mouseMoveEvent(self, event):
        # Draw a line from the previous mouse position to the current mouse position
        self.painter.drawLine(self.prev_pos, event.pos())

        # Update the previous mouse position
        self.prev_pos = event.pos()

        # Update the widget to show the new line
        self.update()

    def mousePressEvent(self, event):
        # Set the initial mouse position
        self.prev_pos = event.pos()

class Result(QWidget):
    def __init__(self):
        super().__init__()
        
        self.button=QPushButton('prev')
        self.button.clicked.connect(self.prevPage)

        self.grid_layout = QGridLayout()
        layout = QHBoxLayout()
        layout.addWidget(self.button)
        self.setLayout(layout)
    
    def prevPage(self):
        self.stack.setCurrentIndex(1)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.stack = QStackedWidget(self)
        self.page1 = DicomViewer()
        self.page1.stack = self.stack
        self.page2 = Lasso(self.page1)
        self.page2.stack = self.stack
        self.page3 = Result()
        self.page3.stack=self.stack

        self.stack.addWidget(self.page1)
        self.stack.addWidget(self.page2)
        self.stack.addWidget(self.page3)
        
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.stack)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())