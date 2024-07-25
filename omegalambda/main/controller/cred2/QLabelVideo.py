from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets

class CustomMenu(QtWidgets.QMenu):
    signalSaveImage = pyqtSignal()
    signalDisplayInfos = pyqtSignal(int)
#-------------------------------------------------------------------#
    def __init__(self):
        super(CustomMenu, self).__init__()
        self.saveImage = self.addAction("Save image")
        self.displayInfos = self.addAction("Display infos")
        self.displayInfos.setCheckable(True)
        self.displayInfos.setChecked(False)

        self.saveImage.triggered.connect(self.OnSaveImage)
        self.displayInfos.triggered.connect(self.OnDisplayInfos)

#-------------------------------------------------------------------#
    def showMenu(self, pos):
        self.exec(QCursor.pos())

#-------------------------------------------------------------------#
    def OnSaveImage(self):
        self.signalSaveImage.emit()

#-------------------------------------------------------------------#
    def OnDisplayInfos(self):
        self.signalDisplayInfos.emit(self.displayInfos.isChecked())

#-------------------------------------------------------------------#
class QLabelVideo(QtWidgets.QLabel):
    signalFireSelection = pyqtSignal(QRect)
    signalDisplayInfos = pyqtSignal(int)
#-------------------------------------------------------------------#
    def __init__(self):
        super(QLabelVideo, self).__init__()

        self.setMinimumWidth(640)
        self.setMinimumHeight(512)

        self.origin = QPoint(0,0)

        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberBand.setStyleSheet("selection-background-color: blue")
        self.setContextMenuPolicy(Qt.CustomContextMenu);
        self.customMenu = CustomMenu()
        self.customContextMenuRequested.connect(self.customMenu.showMenu)
        self.customMenu.signalSaveImage.connect(self.OnSaveImage)
        self.customMenu.signalDisplayInfos.connect(self.OnSignalDisplayInfos)

#-------------------------------------------------------------------#
    def mousePressEvent(self,event):
        if Qt.LeftButton == event.button():
            self.origin = event.pos();
            self.rubberBand.hide();
            self.rubberBand.setGeometry(QRect(self.origin, QSize()));
            self.rubberBand.show();

#-------------------------------------------------------------------#
    def mouseMoveEvent(self,event):
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

#-------------------------------------------------------------------#
    def mouseReleaseEvent(self,event):
        lPositionX = 0
        lPositionY = 0
        lLenghtX = 0
        lLenghtY = 0
        if event.button() == Qt.LeftButton:
            if self.rubberBand.x() >= 0:
                lPositionX = min(self.rubberBand.x(), self.width() - 1)
                lLenghtX = min(self.rubberBand.width(), self.width() - lPositionX)
            else:
                lPositionX = 0;
                lLenghtX = self.rubberBand.width() + self.rubberBand.x() - 1

            if self.rubberBand.y() >= 0:
                lPositionY = min(self.rubberBand.y(), self.height() - 1)
                lLenghtY = min(self.rubberBand.height(), self.height() - lPositionY)
            else:
                lPositionY = 0;
                lLenghtY = self.rubberBand.height() + self.rubberBand.y() - 1

            sel = QRect(lPositionX, lPositionY, lLenghtX, lLenghtY)
            self.signalFireSelection.emit(sel)
            self.rubberBand.hide()
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))

#-------------------------------------------------------------------#
    def OnSaveImage(self):
        saveFilename = QFileDialog.getSaveFileName(self, "Save as", "capture", "PNG(*.png);; TIFF(*.tiff *.tif);; JPEG(*.jpg *.jpeg)");

        saveExtension = "PNG"
        pos = saveFilename[0].find('.')
        if pos >= 0:
            saveExtension = saveFilename[0][pos + 1:]

        if not self.grab().save(saveFilename[0], saveExtension):
            QMessageBox.warning(self, "File could not be saved", "ok", QMessageBox.Ok)

#-------------------------------------------------------------------#
    def OnSignalDisplayInfos(self, enable):
        self.signalDisplayInfos.emit(enable)
