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
from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox
from PyQt5.QtWidgets import QFileDialog, QLabel
from PyQt5.QtGui import QImage, QPixmap

form_class = uic.loadUiType("./qtui.ui")[0]

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
    EXIT_CODE_REBOOT=-123123  
    def __init__(
            self, 
            select_folder_click,
            get_scale,
            image_show,
            get_index,
            set_hu,
            zoom_in,
            zoom_out,
            get_length,
            go_next,
            go_prev,
            move_slider,
            set_canine_start,
            set_canine_end,
            set_cavity_start,
            set_cavity_end,
            get_slice_data,
            set_slice,
            polygon_mask_draw,
            shade_point_draw,
            plot_slice_image,
            plot_wide_image,
            calculate,
            table_doubleclick_change,
            table_delete_row
        ):
        super().__init__()
        #function callback
        self.select_folder_click = select_folder_click
        self.get_scale=get_scale
        self.image_show=image_show
        self.get_index=get_index
        self.set_hu=set_hu
        self.zoom_in=zoom_in
        self.zoom_out=zoom_out
        self.get_length=get_length
        self.go_next=go_next
        self.go_prev=go_prev
        self.move_slider=move_slider
        self.set_canine_start=set_canine_start
        self.set_canine_end=set_canine_end
        self.set_cavity_start=set_cavity_start
        self.set_cavity_end=set_cavity_end
        self.get_slice_data=get_slice_data
        self.set_slice=set_slice
        self.polygon_mask_draw=polygon_mask_draw
        self.shade_point_draw=shade_point_draw
        self.plot_slice_image=plot_slice_image
        self.plot_wide_image=plot_wide_image
        self.calculate=calculate
        self.table_doubleclick_change=table_doubleclick_change
        self.table_delete_row=table_delete_row

        #UI initiation
        self.setupUi(self)
        self.setMouseTracking(True)
        self.connect_ui()
    
    def connect_ui(self):
                        #UI connection
        #menu bar triggering
        self.selectfolder.triggered.connect(self.select_folder_click)
        self.reset.triggered.connect(self.restart_all)

        #button background environment
        self.imageshow.setScaledContents(True)
        self.redmask.setCheckable(True)
        self.blueshade.setCheckable(True)
        self.redmask.setAutoExclusive(True)
        self.blueshade.setAutoExclusive(True)

        #button callback connection
        self.imagecontrol.clicked.connect(self.set_hu)
        self.zoomin.clicked.connect(self.zoom_in)
        self.zoomout.clicked.connect(self.zoom_out)
        self.next.clicked.connect(self.go_next)
        self.prev.clicked.connect(self.go_prev)
        self.slider.valueChanged.connect(self.move_slider)
        self.whitestart.clicked.connect(self.canine_start)
        self.whiteend.clicked.connect(self.canine_end)
        self.blackstart.clicked.connect(self.cavity_start)
        self.blackend.clicked.connect(self.cavity_end)
        self.addslice.clicked.connect(self.set_slice)
        self.select3dshow.clicked.connect(self.plot_slice_image)
        self.wide3dshow.clicked.connect(self.plot_wide_image)
        self.ratio.clicked.connect(self.calculate)
        self.masktable.doubleClicked.connect(self.table_doubleclick_change)
        self.deleteslice.clicked.connect(self.table_delete_row)
        
        #other
        self.mouse_tracking()
        self.pixmap=QPixmap()

    def restart_all(self):
        QtGui.QGuiApplication.exit( WindowClass.EXIT_CODE_REBOOT )

    def mouse_tracking(self):
        tracker = MouseTracker(self.transparent)
        tracker.positionChanged.connect(self.on_positionChanged)
        self.label_position = QLabel(
            self.transparent, alignment=QtCore.Qt.AlignCenter
        )
        self.label_position.setStyleSheet('background-color: white; border: 1px solid black')
    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_positionChanged(self, pos):
        scale=self.get_scale()
        delta = QtCore.QPoint(30, -15)
        self.label_position.show()
        self.label_position.move(pos + delta)
        self.label_position.setText("(%d, %d)" % (pos.x()/scale, pos.y()/scale))
        self.label_position.adjustSize()
        self.posx=pos.x()/scale
        self.posy=pos.y()/scale
    
    def current_row(self):
        row=self.masktable.currentRow()
        if row<0:
            return QMessageBox.warning(self, 'Warning', 'Please select the record!')
        index=int(self.masktable.item(row, 0).text())-1
        return index
    def remove_row(self):
        row=self.masktable.currentRow()
        self.masktable.removeRow(row)

    
    def resize_image(self):
        scale=self.get_scale()
        size = self.pixmap.size()
        self.scrollAreaWidgetContents.resize(scale*size)
        self.transparent.resize(scale*size)
        self.imageshow.resize(scale*size)
    def set_pixmap_image(self):
        qimage=self.image_show()
        self.pixmap=QPixmap.fromImage(qimage)
        self.imageshow.setPixmap(self.pixmap)
        self.resize_image()
        self.set_index()

    def set_index(self):
        index=self.get_index()
        self.slider.setValue(index)
        self.currentindex.clear()
        self.currentindex.append(str(index+1))  
    def set_slider_range(self):
        length=self.get_length()
        self.slider.setRange(0, length)
    

    def canine_start(self):
        index=self.get_index()
        self.set_canine_start()
        self.whitestartbox.setValue(index+1)
    def canine_end(self):
        index=self.get_index()
        self.set_canine_end()
        self.whiteendbox.setValue(index+1)
    def cavity_start(self):
        index=self.get_index()
        self.set_cavity_start()
        self.blackstartbox.setValue(index+1)
    def cavity_end(self):
        index=self.get_index()
        self.set_cavity_end()
        self.blackendbox.setValue(index+1)    


    def update_table(self):
        data=self.get_slice_data()
        self.masktable.setRowCount(0)
        for i, r in data.iterrows():
            row=self.masktable.rowCount()
            self.masktable.insertRow(row)
            self.masktable.setItem(row, 0, QTableWidgetItem(str(r[1])))
            self.masktable.setItem(row, 1, QTableWidgetItem(str(r[3])))
            self.masktable.setItem(row, 2, QTableWidgetItem(str(r[4])))
    

    def mousePressEvent(self, e):
        if self.posx<=1024 and self.posy<=1024:
            if self.redmask.isChecked()==True:
                self.polygon_mask_draw((int(self.posx), int(self.posy)))
                self.update_table()
                self.set_pixmap_image()
            if self.blueshade.isChecked()==True:
                self.shade_point_draw((int(self.posx), int(self.posy)))
                self.update_table()
                self.set_pixmap_image()
    def red_pen(self):
        if self.redmask.isChecked()==True:
            self.redmask.setChecked(True)
        else:
            self.redmask.setChecked(False)
    def blue_pen(self):
        if self.blueshade.isChecked()==True:
            self.blueshade.setChecked(True)
        else:
            self.blueshade.setChecked(False)

    def show_result(self, w, b, r):
        self.resultcanine.append(str(w))
        self.resultcavity.append(str(b))
        self.resultratio.append(str(r))