import FliSdk_V2 as FliSdk
import FliConsole
import QLabelVideo
import resources
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import PYQT_VERSION_STR
import sys
import time
import datetime
import os
from PIL import Image
import ctypes
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import CblueOne_enum as CblueOne

class Ui(QtWidgets.QMainWindow):
#-------------------------------------------------------------------#
    def __init__(self):
        super(Ui, self).__init__()
        self.ui = uic.loadUi('FliSdkDemo.ui', self)
        print("PyQt version:", PYQT_VERSION_STR)
        self.layout().setSizeConstraint(QLayout.SetFixedSize)

        self.displayFps = 0
        self.nbFrames = 0
        self.startTime = datetime.datetime.now()

        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.OnRefresh)

        #all connections
        self.ui.pb_start.clicked.connect(self.OnStart)
        self.ui.pb_loadRecord.clicked.connect(self.OnLoadRecord)
        self.ui.pb_clip.clicked.connect(self.OnClip)
        self.ui.sb_rotationAngle.valueChanged.connect(self.OnRotationAngleChanged)
        self.ui.gb_grabN.clicked.connect(self.OnGrabNChanged)
        self.ui.sb_grabN.valueChanged.connect(self.OnGrabNChanged)
        self.ui.slider_imageIndex.valueChanged.connect(self.OnSliderMoved)
        self.ui.sb_imageIndex.valueChanged.connect(self.OnImageIndexChanged)
        self.ui.pb_resetBuffer.clicked.connect(self.OnResetBuffer)
        self.ui.sb_bufSize.editingFinished.connect(self.OnChangeBufferSize)
        self.ui.sb_gamma.valueChanged.connect(self.OnGammaChanged)
        self.ui.pb_saveBuffer.clicked.connect(self.OnSaveBufferCliked)
        self.ui.cb_autoClip.stateChanged.connect(self.OnAutoClipChanged)
        self.ui.autoClipActivated = False
        self.ui.actionCamera_infos.triggered.connect(self.OnActionCameraInfos)
        self.ui.actionCamera_settings.triggered.connect(self.OnActionCameraSettings)
        self.ui.actionConsole.triggered.connect(self.OnActionConsole)
        self.console = FliConsole.FliConsole()
        self.console.setMinimumHeight(380)
        self.console.setVisible(False)
        self.ui.console.getData.connect(self.SendCommandToCamera)
        self.ui.consoleLayout.addWidget(self.console)
        self.lb_video = QLabelVideo.QLabelVideo()
        self.ui.layoutLabelVideo.addWidget(self.lb_video)
        self.lb_video.signalDisplayInfos.connect(self.OnDisplayInfos)
        self.lb_video.signalFireSelection.connect(self.OnClipSelection)
        self.ui.pb_start.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.ui.cb_sharpen.clicked.connect(self.OnSharpenClicked)
        self.ui.sb_fps.editingFinished.connect(self.OnChangeFps)
        self.ui.sb_exposure.editingFinished.connect(self.OnChangeExposure)
        self.ui.pb_fpsMax.clicked.connect(self.OnFpsMaxClicked)
        self.ui.pb_exposureMax.clicked.connect(self.OnExposureMaxClicked)
        self.ui.pb_buildBias.clicked.connect(self.OnBuildBiasClicked)
        self.ui.cb_badPixel.clicked.connect(self.OnBadPixelClicked)
        self.ui.cb_bias.clicked.connect(self.OnBiasClicked)
        self.ui.cb_antiBlooming.clicked.connect(self.OnAntiBloomingClicked)
        self.ui.pb_shutdown.clicked.connect(self.OnShutdownClicked)
        self.ui.sb_sensorTemp.editingFinished.connect(self.OnChangeSensorTemp)
        self.ui.actionDetectCameras.triggered.connect(self.OnDetectCameras)
        self.ui.cb_cameras.currentTextChanged.connect(self.OnCameraChanged)
        self.ui.cb_standby.clicked.connect(self.OnStandbyClicked)
        self.ui.cb_cooling.clicked.connect(self.OnCoolingClicked)

        self.ui.gb_cropping.clicked.connect(self.OnCroppingAction)
        self.ui.le_cropColumnMin.returnPressed.connect(self.OnCroppingAction)
        self.ui.le_cropColumnMax.returnPressed.connect(self.OnCroppingAction)
        self.ui.le_cropRowMin.returnPressed.connect(self.OnCroppingAction)
        self.ui.le_cropRowMax.returnPressed.connect(self.OnCroppingAction)
        #self.ui.le_cropColumnCred1.returnPressed.connect(self.OnCroppingAction)
        #self.ui.le_cropRowCred1.returnPressed.connect(self.OnCroppingAction)

        self.ui.cb_conversionGain.addItem("low")
        self.ui.cb_conversionGain.addItem("medium")
        self.ui.cb_conversionGain.addItem("high")
        self.ui.cb_conversionGain.currentIndexChanged.connect(self.OnConversionGainChanged)

        self.ui.cb_convEfficiency.addItem("low")
        self.ui.cb_convEfficiency.addItem("high")
        self.ui.cb_convEfficiency.currentIndexChanged.connect(self.OnConversionEfficiencyChanged)
        self.ui.cb_reverseX.clicked.connect(self.OnReverseXClicked)
        self.ui.cb_reverseY.clicked.connect(self.OnReverseYClicked)
        self.ui.rb_pixelFormat8b.clicked.connect(self.OnPixelFormat8bClicked)
        self.ui.rb_pixelFormat12b.clicked.connect(self.OnPixelFormat12bClicked)
        self.ui.sb_gainCblueOne.editingFinished.connect(self.OnGainCblueOneChanged)

        self.cameraModel = ""
        self.context = FliSdk.Init()
        self.OnDetectCameras()

        listOfColormap = FliSdk.ImageProcessing.GetColorMapList(self.context, -1)
        for s in listOfColormap:
            if s == "NONE":
                self.ui.cb_colorMap.insertItem(0,s)
            else:
                self.ui.cb_colorMap.addItem(s)
        self.ui.cb_colorMap.setCurrentIndex(0)
        self.ui.cb_colorMap.currentIndexChanged.connect(self.OnColormapChanged)

        listOfClipping = FliSdk.ImageProcessing.GetClippingList(self.context, -1)
        for s in listOfClipping:
            if s == "LINEAR":
                self.ui.cb_clippingType.insertItem(0,s)
            else:
                self.ui.cb_clippingType.addItem(s)
        self.ui.cb_clippingType.setCurrentIndex(0)
        self.ui.cb_clippingType.currentIndexChanged.connect(self.OnClippingTypeChanged)

        nbImagesBuffer = FliSdk.GetImagesCapacity(self.context)
        self.ui.progressBar_imageBuffer.setFormat("%v/" + str(nbImagesBuffer - 1))
        self.ui.progressBar_imageBuffer.setMaximum(nbImagesBuffer - 1)
        self.ui.slider_imageIndex.setMaximum(nbImagesBuffer - 1)
        self.ui.slider_imageIndex.setMinimum(0)
        self.ui.sb_imageIndex.setMaximum(nbImagesBuffer-1)

        f = open("stylesheet.css", "r")
        style = f.read()
        self.setStyleSheet(style)
        self.lb_video.setStyleSheet(style)
        f.close()

        self.image = QImage(640, 512, QImage.Format_RGB888)
        self.image.fill(QColor(0,0,0))
        self.lb_video.setPixmap(QPixmap.fromImage(self.image))

        plt.figure()
        buffer = FliSdk.GetRawImageAsNumpyArray(self.context, -1)
        plt.imshow(buffer, cmap='gray', vmin=0, vmax=65535)
        plt.colorbar()

        #for image received callback
        self.wrappedFunc = FliSdk.CWRAPPER(self.OnImageReceived)
        FliSdk.AddCallBackNewImage(self.context, self.wrappedFunc, 20, False, 0)

        self.show()

#-------------------------------------------------------------------#
    def OnDetectCameras(self):
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QIcon(":/FliSdkDemo/image/icon.png"))
        msgBox.setText("Detecting cameras, please wait...")
        msgBox.setStandardButtons(QMessageBox.NoButton)
        msgBox.show()
        QApplication.processEvents()
        FliSdk.DetectGrabbers(self.context)
        # listOfCameras = FliSdk.DetectCameras(self.context)

        ## added 2023-12-01
        ip = ctypes.c_char_p(b"169.254.123.123")
        username = ctypes.c_char_p(b"admin")
        password = ctypes.c_char_p(b"flicred1")
        listOfCameras = [FliSdk.AddEthernetCamera(self.context, ip, username, password)[1]]
        print(listOfCameras)

        if len(listOfCameras) == 0:
            msgBox.setText("No camera detected.")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.setDefaultButton(QMessageBox.Ok)
            msgBox.exec()
            self.ui.actionConsole.setDisabled(True)
            self.ui.actionCamera_settings.setDisabled(True)
            self.ui.actionCamera_infos.setDisabled(True)

        if len(listOfCameras)>0:
            FliSdk.SetCamera(self.context, listOfCameras[0])
            self.ui.cb_cameras.blockSignals(True)
            self.ui.cb_cameras.addItems(listOfCameras)
            self.ui.cb_cameras.blockSignals(False)

        FliSdk.Update(self.context)
        msgBox.close()

        if len(listOfCameras) > 0:
            self.ReadInfos()
            self.SetGuiForCamera()
            self.ReadParameters()
            self.timer.start(10)

#-------------------------------------------------------------------#
    def OnCameraChanged(self, name):
        FliSdk.SetCamera(self.context, str(name))
        FliSdk.Update(self.context)

        self.SetGuiForCamera()
        self.ReadInfos()
        self.ReadParameters()
        self.timer.start(10)

#-------------------------------------------------------------------#
    def OnImageReceived(self, image, ctx):
        width, height = FliSdk.GetCurrentImageDimension(self.context)
        ArrayType = ctypes.c_uint16 * width * height
        pa = ctypes.cast(image, ctypes.POINTER(ArrayType))
        buffer = np.ndarray((height, width), dtype=np.uint16, buffer=pa.contents)
        print(buffer)
        #TODO: numpy array of 16 bits image, has to be computed to a 8bit image to be displayed.

#-------------------------------------------------------------------#
    def closeEvent(self, event):
        self.timer.stop()
        FliSdk.Stop(self.context)
        FliSdk.Exit(self.context)
        event.accept()

#-------------------------------------------------------------------#
    def ReadInfos(self):
        if FliSdk.IsCred(self.context):
            res,status,diag = FliSdk.FliCred.GetStatusDetailed(self.context)
            if res:
                self.ui.lb_status.setText(status + "-" + diag)
            else:
                self.ui.lb_status.setText("no status")

            temps = []

            if self.cameraModel == "Cred2":
                temps = FliSdk.FliCredTwo.GetAllTemp(self.context)
                self.ui.le_mbTemp.setText(str(temps[1]))
                self.ui.le_feTemp.setText(str(temps[2]))
                self.ui.le_pwTemp.setText(str(temps[3]))
                self.ui.le_sensorCred2Temp.setText(str(temps[4]))
                self.ui.le_peltierTemp.setText(str(temps[5]))
                self.ui.le_heatsinkTemp.setText(str(temps[6]))
            elif self.cameraModel == "Cred3":
                temps = FliSdk.FliCredThree.GetAllTemp(self.context)
                self.ui.le_cpuTemp.setText(str(temps[1]))
                self.ui.le_backendTemp.setText(str(temps[2]))
                self.ui.le_interfaceTemp.setText(str(temps[3]))
                self.ui.le_sensorCred3Temp.setText(str(temps[4]))
                self.ui.le_ambiantTemp.setText(str(temps[5]))
            elif self.cameraModel == "Cred1":
                temps = FliSdk.FliCredOne.GetAllTemp(self.context)
                self.ui.le_mbTempCred1.setText(str(temps[1]))
                self.ui.le_feTempCred1.setText(str(temps[2]))
                self.ui.le_pwTempCred1.setText(str(temps[3]))
                self.ui.le_cryodTemp.setText(str(temps[4]))
                self.ui.le_cryoptTemp.setText(str(temps[5]))
                self.ui.le_waterTemp.setText(str(temps[6]))
                self.ui.le_peltierTempCred1.setText(str(temps[7]))
                self.ui.le_ptMcuTemp.setText(str(temps[8]))
        elif FliSdk.IsCblueOne(self.context):
            res,status = FliSdk.FliCblueOne.GetDeviceStatus(self.context)
            if res:
                self.ui.lb_status.setText(status)
            else:
                self.ui.lb_status.setText("no status")

            FliSdk.FliCblueOne.SetDeviceTemperatureSelector(self.context, CblueOne.DeviceTemperatureSelector.Sensor)
            res,sensorTemp = FliSdk.FliCblueSfnc.GetDeviceTemperature(self.context)
            sensorTemp = round(sensorTemp, 2)
            self.ui.le_sensorTempCblue1.setText(str(sensorTemp))

            FliSdk.FliCblueOne.SetDeviceTemperatureSelector(self.context, CblueOne.DeviceTemperatureSelector.CPU)
            res,cpuTemp = FliSdk.FliCblueSfnc.GetDeviceTemperature(self.context)
            cpuTemp = round(cpuTemp, 2)
            self.ui.le_cpuTempCblue1.setText(str(cpuTemp))

#-------------------------------------------------------------------#
    def ReadParameters(self):
        if self.cameraModel == "undefined":
            return

        if FliSdk.IsSerialCamera(self.context):
            res,fps = FliSdk.FliSerialCamera.GetFps(self.context)
            if res:
                self.ui.sb_fps.setValue(fps)

            if FliSdk.IsCredOne(self.context):
                self.ui.sb_exposure.setValue(1/fps)

            res,fpsMax = FliSdk.FliSerialCamera.GetFpsMax(self.context)
            if res:
                self.ui.pb_fpsMax.setText("Set fps max:" + str(round(fpsMax,5)))

            if FliSdk.IsCredTwo(self.context):
                res, tint = FliSdk.FliCredTwo.GetTint(self.context)
                self.ui.sb_exposure.setValue(1/fps)

                res,tintItr = FliSdk.FliCredTwo.GetMaxTintItr(self.context)
                if res:
                    if tint > tintItr:
                        self.ui.lb_exposure.setText("Exposure (IWR)")
                    else:
                        self.ui.lb_exposure.setText("Exposure (ITR)")

                res,conversionGain = FliSdk.FliCredTwo.GetConversionGain(self.context)
                if res:
                    self.ui.cb_conversionGain.setCurrentText(conversionGain)

                res,tintMax = FliSdk.FliCredTwo.GetTintMax(self.context)
                if res:
                    self.ui.pb_exposureMax.setText("Set tint max:" + str(round(tintMax* 1000,5)))

                res,state = FliSdk.FliCredTwo.GetBadPixelState(self.context)
                if res:
                    self.ui.cb_badPixel.setChecked(state)

                res,temp = FliSdk.FliCredTwo.GetTempSnakeSetPoint(self.context)
                if res:
                    self.ui.sb_sensorTemp.setValue(temp)

                res,state = FliSdk.FliCredTwo.GetAntiBloomingState(self.context)
                if res:
                    self.ui.cb_antiBlooming.setChecked(state)

            elif FliSdk.IsCredThree(self.context) or FliSdk.IsCredTwoLite(self.context):
                res, tint = FliSdk.FliCredThree.GetTint(self.context)
                self.ui.sb_exposure.setValue(1/fps)

                res,tintItr = FliSdk.FliCredThree.GetMaxTintItr(self.context)
                if res:
                    if tint > tintItr:
                        self.ui.lb_exposure.setText("Exposure (IWR)")
                    else:
                        self.ui.lb_exposure.setText("Exposure (ITR)")

                res,conversionGain = FliSdk.FliCredThree.GetConversionGain(self.context)
                if res:
                    self.ui.cb_conversionGain.setCurrentText(conversionGain)

                res,tintMax = FliSdk.FliCredThree.GetTintMax(self.context)
                if res:
                    self.ui.pb_exposureMax.setText("Set tint max:" + str(round(tintMax* 1000,5)))

                res,state = FliSdk.FliCredThree.GetBadPixelState(self.context)
                if res:
                    self.ui.cb_badPixel.setChecked(state)

                res,state = FliSdk.FliCredThree.GetAntiBloomingState(self.context)
                if res:
                    self.ui.cb_antiBlooming.setChecked(state)
           

            if FliSdk.IsCred(self.context):
                res,state = FliSdk.FliCred.GetBiasState(self.context)
                if res:
                    self.ui.cb_bias.setChecked(state)

            res, cropEnabled, cropData = FliSdk.GetCroppingState(self.context)
            if res:
                self.ui.gb_cropping.setChecked(cropEnabled)
                self.ui.le_cropColumnMin.setText(str(cropData.col1))
                self.ui.le_cropColumnMax.setText(str(cropData.col2))
                self.ui.le_cropRowMin.setText(str(cropData.row1))
                self.ui.le_cropRowMax.setText(str(cropData.row2))

            res, response = FliSdk.FliSerialCamera.SendCommand(self.context, "cooling raw")
            if "on" in response:
                self.ui.cb_cooling.setChecked(True)
            else:
                self.ui.cb_cooling.setChecked(False)
            res, response = FliSdk.FliSerialCamera.SendCommand(self.context, "standby raw")
            if "on" in response:
                self.ui.cb_standby.setChecked(True)
            else:
                self.ui.cb_standby.setChecked(False)

        elif FliSdk.IsCblueSfnc(self.context):
            res, fps = FliSdk.FliCblueSfnc.GetAcquisitionFrameRate(self.context)
            self.ui.sb_fps.setValue(fps)

            res,tint = FliSdk.FliCblueSfnc.GetExposureTime(self.context)
            self.ui.sb_exposure.setValue(tint/1000)

            res,fpsMax = FliSdk.FliCblueSfnc.GetAcquisitionFrameRateMax(self.context)
            self.ui.pb_fpsMax.setText("Set fps max:" + str(round(fpsMax,5)))

            res,tintMax = FliSdk.FliCblueSfnc.GetExposureTimeMax(self.context)
            self.ui.pb_exposureMax.setText("Set tint max:" + str(round(tintMax/1000,5)))

            FliSdk.FliCblueSfnc.SetGainSelector(self.context, CblueOne.GainSelector.AnalogAll)
            res, analogGain = FliSdk.FliCblueSfnc.GetGain(self.context)
            FliSdk.FliCblueSfnc.SetGainSelector(self.context, CblueOne.GainSelector.DigitalAll)
            res, digitalGain = FliSdk.FliCblueSfnc.GetGain(self.context)
            self.ui.sb_gainCblueOne.setValue(analogGain + digitalGain)

            res, revX = FliSdk.FliCblueSfnc.GetReverseX(self.context)
            self.ui.cb_reverseX.setChecked(revX)
            res, revY = FliSdk.FliCblueSfnc.GetReverseY(self.context)
            self.ui.cb_reverseY.setChecked(revY)

            res, pixelFormat = FliSdk.FliCblueSfnc.GetPixelFormat(self.context)
            if pixelFormat == CblueOne.PixelFormat.Mono8:
                self.ui.rb_pixelFormat8b.setChecked(True)
            elif pixelFormat == CblueOne.PixelFormat.Mono12:
                self.ui.rb_pixelFormat12b.setChecked(True)

            if FliSdk.IsCblueOne(self.context):
                res, convE = FliSdk.FliCblueOne.GetConversionEfficiency(self.context)
                self.ui.cb_convEfficiency.setCurrentIndex(convE)

        nbImagesBuffer = FliSdk.GetImagesCapacity(self.context)
        self.ui.progressBar_imageBuffer.setFormat("%v/" + str(nbImagesBuffer - 1))
        self.ui.progressBar_imageBuffer.setMaximum(nbImagesBuffer - 1)
        self.ui.slider_imageIndex.setMaximum(nbImagesBuffer - 1)
        self.ui.slider_imageIndex.setMinimum(0)
        self.ui.sb_imageIndex.setMaximum(nbImagesBuffer-1)

#-------------------------------------------------------------------#
    def OnSharpenClicked(self):
        FliSdk.ImageProcessing.EnableSharpen(self.context, -1, self.ui.cb_sharpen.isChecked())
        if not FliSdk.IsStarted(self.context):
            self.DisplayImage(-1)

#-------------------------------------------------------------------#
    def SetGuiForCamera(self):
        self.cameraModel = FliSdk.GetCameraModel(self.context)
        self.ui.actionCamera_infos.setChecked(True)
        self.ui.vw_cameraInfos.setMaximumWidth(500)
        self.ui.actionCamera_settings.setChecked(True)
        self.ui.vw_cameraSettings.setMaximumWidth(235)
        self.ui.vw_cameraSettings.setMinimumWidth(235)
        self.ui.spacerConsole.setMinimumHeight(220)

        if self.cameraModel == "undefined":
            self.ui.actionCamera_infos.setChecked(False)
            self.ui.vw_cameraInfos.setMaximumWidth(20)
            self.ui.actionCamera_settings.setChecked(False)
            self.ui.vw_cameraSettings.setMaximumWidth(10)
            self.ui.vw_cameraSettings.setMinimumWidth(10)
        elif self.cameraModel == "Cred1":
            self.ui.pb_exposureMax.setVisible(False)
            self.ui.sb_exposure.setVisible(False)
            self.ui.lb_exposure.setVisible(False)
            self.ui.cb_badPixel.setVisible(False)
            self.ui.lb_conversionGain.setVisible(False)
            self.ui.cb_conversionGain.setVisible(False)
            self.ui.separator_conversionGain.setVisible(False)
            self.ui.gb_tempCred2.setVisible(False)
            self.ui.gb_tempCred3.setVisible(False)
            self.ui.gb_tempCred1.setVisible(True)
            self.ui.cb_cooling.setVisible(True)
            self.ui.cb_standby.setVisible(True)
            self.ui.gb_cropping.setVisible(False)
            self.ui.line_sensorTemp.setVisible(False)
            self.ui.lb_sensorTemp.setVisible(False)
            self.ui.gb_tempCblue1.setVisible(False)
            self.ui.pb_buildBias.setVisible(True)
            self.ui.cb_antiBlooming.setVisible(True)
            self.ui.line_10.setVisible(True)
            self.ui.cb_bias.setVisible(True)
            self.ui.sb_sensorTemp.setVisible(False)
            self.ui.vw_sensorSettingsCblueOne.setVisible(False)
            self.ui.vw_imageEnhancementCblueOne.setVisible(False)
        elif self.cameraModel == "Cred2":
            self.ui.gb_tempCred1.setVisible(False)
            self.ui.gb_tempCred3.setVisible(False)
            self.ui.cb_cooling.setVisible(False)
            self.ui.cb_standby.setVisible(False)
            self.ui.line_sensorTemp.setVisible(False)
            self.ui.gb_tempCred2.setVisible(True)
            self.ui.pb_exposureMax.setVisible(True)
            self.ui.sb_exposure.setVisible(True)
            self.ui.lb_exposure.setVisible(True)
            self.ui.gb_tempCblue1.setVisible(False)
            self.ui.pb_buildBias.setVisible(True)
            self.ui.line_10.setVisible(True)
            self.ui.cb_badPixel.setVisible(True)
            self.ui.cb_antiBlooming.setVisible(True)
            self.ui.cb_bias.setVisible(True)
            self.ui.gb_cropping.setVisible(True)
            self.ui.lb_conversionGain.setVisible(True)
            self.ui.cb_conversionGain.setVisible(True)
            self.ui.line_25.setVisible(True)
            self.ui.separator_conversionGain.setVisible(True)
            self.ui.vw_sensorSettingsCblueOne.setVisible(False)
            self.ui.vw_imageEnhancementCblueOne.setVisible(False)
        elif self.cameraModel == "Cred3":
            self.ui.gb_tempCred1.setVisible(False)
            self.ui.gb_tempCred2.setVisible(False)
            self.ui.page_control.setVisible(False)
            self.ui.gb_tempCred3.setVisible(True)
            self.ui.pb_exposureMax.setVisible(True)
            self.ui.sb_exposure.setVisible(True)
            self.ui.lb_exposure.setVisible(True)
            self.ui.cb_cooling.setVisible(False)
            self.ui.cb_standby.setVisible(False)
            self.ui.gb_cropping.setVisible(True)
            self.ui.line_sensorTemp.setVisible(True)
            self.ui.lb_sensorTemp.setVisible(True)
            self.ui.sb_sensorTemp.setVisible(True)
            self.ui.pb_buildBias.setVisible(True)
            self.ui.line_10.setVisible(True)
            self.ui.cb_badPixel.setVisible(True)
            self.ui.cb_bias.setVisible(True)
            self.ui.cb_antiBlooming.setVisible(True)
            self.ui.gb_tempCblue1.setVisible(False)
            self.ui.lb_conversionGain.setVisible(True)
            self.ui.cb_conversionGain.setVisible(True)
            self.ui.line_25.setVisible(True)
            self.ui.separator_conversionGain.setVisible(True)
            self.ui.vw_sensorSettingsCblueOne.setVisible(False)
            self.ui.vw_imageEnhancementCblueOne.setVisible(False)
        elif self.cameraModel == "Cblue1":
            self.ui.gb_tempCred1.setVisible(False)
            self.ui.gb_tempCred2.setVisible(False)
            self.ui.gb_tempCred3.setVisible(False)
            self.ui.gb_tempCblue1.setVisible(True)
            self.ui.gb_cropping.setVisible(False)
            self.ui.pb_buildBias.setVisible(False)
            self.ui.line_10.setVisible(False)
            self.ui.line_25.setVisible(False)
            self.ui.cb_badPixel.setVisible(False)
            self.ui.cb_bias.setVisible(False)
            self.ui.lb_conversionGain.setVisible(False)
            self.ui.cb_conversionGain.setVisible(False)
            self.ui.separator_conversionGain.setVisible(False)
            self.ui.cb_antiBlooming.setVisible(False)
            self.ui.lb_sensorTemp.setVisible(False)
            self.ui.sb_sensorTemp.setVisible(False)
            self.ui.line_sensorTemp.setVisible(False)
            self.ui.cb_cooling.setVisible(False)
            self.ui.cb_standby.setVisible(False)
            self.ui.pb_exposureMax.setVisible(True)
            self.ui.sb_exposure.setVisible(True)
            self.ui.lb_exposure.setVisible(True)
            self.ui.vw_sensorSettingsCblueOne.setVisible(True)
            self.ui.vw_imageEnhancementCblueOne.setVisible(True)

#-------------------------------------------------------------------#
    def OnStart(self):
        if FliSdk.IsStarted(self.context):
            FliSdk.Stop(self.context)
            self.ui.pb_start.setText("Start")
            self.ui.lcd_fpsIhm.display(0)
            self.ui.lcd_fpsCamera.display(0)
            self.ui.pb_start.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            FliSdk.Start(self.context)
            self.ui.pb_start.setText("Stop")
            self.ui.pb_start.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

#-------------------------------------------------------------------#
    def OnRefresh(self):
        self.ReadInfos()

        if FliSdk.IsStarted(self.context):
            if FliSdk.IsGrabNEnabled(self.context):
                if FliSdk.IsGrabNFinished(self.context):
                    self.ui.pb_start.click()

            self.nbFrames = self.nbFrames + 1
            if int((datetime.datetime.now() - self.startTime).total_seconds()*1000) > 1000:
                self.ui.lcd_fpsIhm.display(self.nbFrames)
                self.nbFrames = 0
                self.startTime = datetime.datetime.now()

            self.ui.lcd_fpsCamera.display(FliSdk.GetImageReceivedRate(self.context))
            bufFilling = FliSdk.GetBufferFilling(self.context)
            self.ui.progressBar_imageBuffer.setValue(bufFilling)
            self.ui.slider_imageIndex.setValue(bufFilling)
            self.ui.sb_imageIndex.setValue(bufFilling)
            self.DisplayImage(-1)

#-------------------------------------------------------------------#
    def DisplayImage(self, index):
        buffer = FliSdk.GetProcessedImageRGBANumpyArray(self.context, index)
        self.image = QImage(buffer.data, buffer.shape[1], buffer.shape[0], QImage.Format_RGBA8888)

        if FliSdk.IsCred(self.context):
            self.lb_video.setPixmap(QPixmap.fromImage(self.image))
        elif FliSdk.IsCblueOne(self.context):
            self.lb_video.setPixmap(QPixmap.fromImage(self.image.scaled(640,512)))

        if self.autoClipActivated:
            self.OnClip()
        
#-------------------------------------------------------------------#
    def OnRotationAngleChanged(self):
        val = self.ui.sb_rotationAngle.value()
        if val == 360:
            self.ui.sb_rotationAngle.setValue(0)
            return
        if val == -1:
            self.ui.sb_rotationAngle.setValue(359)
            return
        FliSdk.ImageProcessing.SetRotationAngle(self.context, -1, val)
        if not FliSdk.IsStarted(self.context):
            self.DisplayImage(-1)

#-------------------------------------------------------------------#
    def OnConversionGainChanged(self):
        FliSdk.FliCredTwo.SetConversionGain(self.context, self.ui.cb_conversionGain.currentText())
        FliSdk.FliCredThree.SetConversionGain(self.context, self.ui.cb_conversionGain.currentText())

#-------------------------------------------------------------------#
    def OnConversionEfficiencyChanged(self):
        wasStarted = FliSdk.IsStarted(self.context)
        if wasStarted:
            FliSdk.Stop(self.context)
        FliSdk.FliCblueOne.SetConversionEfficiency(self.context, self.ui.cb_convEfficiency.currentIndex())
        if wasStarted:
            FliSdk.Start(self.context)

#-------------------------------------------------------------------#
    def OnShutdownClicked(self):
        FliSdk.FliCred.ShutDown(self.context)

#-------------------------------------------------------------------#
    def OnGrabNChanged(self):
        if self.ui.gb_grabN.isChecked():
            FliSdk.EnableGrabN(self.context, self.ui.sb_grabN.value())
        else:
            FliSdk.DisableGrabN(self.context)

#-------------------------------------------------------------------#
    def OnClippingTypeChanged(self):
        FliSdk.ImageProcessing.SetClippingType(self.context, -1, self.ui.cb_clippingType.currentText())
        if not FliSdk.IsStarted(self.context):
            self.DisplayImage(-1)

#-------------------------------------------------------------------#
    def OnColormapChanged(self):
        FliSdk.ImageProcessing.SetColorMap(self.context, -1, self.ui.cb_colorMap.currentText())
        if not FliSdk.IsStarted(self.context):
            self.DisplayImage(-1)

#-------------------------------------------------------------------#
    def OnClip(self):
        FliSdk.ImageProcessing.Clip(self.context, -1, 0,0,640,512)
        if not FliSdk.IsStarted(self.context):
            self.DisplayImage(-1)

#-------------------------------------------------------------------#
    def OnClipSelection(self, sel):
        FliSdk.ImageProcessing.Clip(self.context, -1, sel.x(), sel.y(), sel.width(), sel.height())
        if not FliSdk.IsStarted(self.context):
            self.DisplayImage(-1)

#-------------------------------------------------------------------#
    def OnSliderMoved(self):
        self.DisplayImage(self.ui.slider_imageIndex.value())
        self.ui.sb_imageIndex.setValue(self.ui.slider_imageIndex.value())

#-------------------------------------------------------------------#
    def OnDisplayInfos(self, enable):
        FliSdk.ImageProcessing.EnableDisplayInfos(self.context, -1, enable)
        if not FliSdk.IsStarted(self.context):
            self.DisplayImage(-1)

#-------------------------------------------------------------------#
    def OnResetBuffer(self):
        FliSdk.ResetBuffer(self.context)
        self.ui.progressBar_imageBuffer.setValue(0)
        self.ui.slider_imageIndex.setValue(0)
        self.ui.sb_imageIndex.setValue(0)
        if not FliSdk.IsStarted(self.context):
            self.DisplayImage(-1)

#-------------------------------------------------------------------#
    def OnChangeBufferSize(self):
        if self.ui.sb_bufSize.hasFocus():
            FliSdk.SetBufferSize(self.context, self.ui.sb_bufSize.value())
            nbImagesBuffer = FliSdk.GetImagesCapacity(self.context)
            self.ui.progressBar_imageBuffer.setFormat("%v/" + str(nbImagesBuffer - 1))
            self.ui.progressBar_imageBuffer.setMaximum(nbImagesBuffer - 1)
            self.ui.progressBar_imageBuffer.setValue(0)
            self.ui.slider_imageIndex.setMaximum(nbImagesBuffer - 1)
            self.ui.sb_imageIndex.setMaximum(nbImagesBuffer-1)

#-------------------------------------------------------------------#
    def OnChangeFps(self):
        if self.ui.sb_fps.hasFocus():
            if FliSdk.IsSerialCamera(self.context):
                FliSdk.FliSerialCamera.SetFps(self.context, self.ui.sb_fps.value())
            elif FliSdk.IsCblueSfnc(self.context):
                wasStarted = FliSdk.IsStarted(self.context)
                if wasStarted:
                    FliSdk.Stop(self.context)
                FliSdk.FliCblueSfnc.SetAcquisitionFrameRate(self.context, self.ui.sb_fps.value())
                if wasStarted:
                    FliSdk.Start(self.context)
            self.ReadParameters()

#-------------------------------------------------------------------#
    def OnChangeSensorTemp(self):
        if self.ui.sb_sensorTemp.hasFocus():
            FliSdk.FliCredTwo.SetTempSnakeSetPoint(self.context, self.ui.sb_sensorTemp.value())

#-------------------------------------------------------------------#
    def OnGainCblueOneChanged(self):
        if self.ui.sb_gainCblueOne.hasFocus():
            wasStarted = FliSdk.IsStarted(self.context)
            if wasStarted:
                FliSdk.Stop(self.context)
            val = self.ui.sb_gainCblueOne.value()
            if val <= 24:
                FliSdk.FliCblueSfnc.SetGainSelector(self.context, CblueOne.GainSelector.AnalogAll)
                FliSdk.FliCblueSfnc.SetGain(self.context, val)
            else:
                FliSdk.FliCblueSfnc.SetGainSelector(self.context, CblueOne.GainSelector.AnalogAll)
                FliSdk.FliCblueSfnc.SetGain(self.context, 24)
                FliSdk.FliCblueSfnc.SetGainSelector(self.context, CblueOne.GainSelector.DigitalAll)
                FliSdk.FliCblueSfnc.SetGain(self.context, val-24)
            if wasStarted:
                FliSdk.Start(self.context)

#-------------------------------------------------------------------#
    def OnChangeExposure(self):
        if self.ui.sb_exposure.hasFocus():
            if FliSdk.IsCred(self.context):
                if FliSdk.IsCredOne(self.context) or FliSdk.IsOcam2k(self.context):
                    FliSdk.FliSerialCamera.SetFps(self.context, 1 / (self.ui.sb_exposure.value()/1000.0))
                elif FliSdk.IsCredTwo(self.context):
                    FliSdk.FliCredTwo.SetTint(self.context, self.ui.sb_exposure.value()/1000.0)
                elif FliSdk.IsCredThree(self.context):
                    FliSdk.FliCredThree.SetTint(self.context, self.ui.sb_exposure.value()/1000.0)
                elif FliSdk.IsCredTwoLite(self.context):
                    FliSdk.FliCredTwoLite.SetTint(self.context, self.ui.sb_exposure.value()/1000.0)
            elif FliSdk.IsCblueSfnc(self.context):
                wasStarted = FliSdk.IsStarted(self.context)
                if wasStarted:
                    FliSdk.Stop(self.context)
                FliSdk.FliCblueSfnc.SetExposureTime(self.context, self.ui.sb_exposure.value()*1000.0)
                if wasStarted:
                    FliSdk.Start(self.context)
            self.ReadParameters()

#-------------------------------------------------------------------#
    def OnFpsMaxClicked(self):
        val = float(self.ui.pb_fpsMax.text().split(':')[1])

        if FliSdk.IsSerialCamera(self.context):
            FliSdk.FliSerialCamera.SetFps(self.context, val)
        elif FliSdk.IsCblueSfnc(self.context):
            wasStarted = FliSdk.IsStarted(self.context)
            if wasStarted:
                FliSdk.Stop(self.context)
            FliSdk.FliCblueSfnc.SetAcquisitionFrameRate(self.context, val)
            if wasStarted:
                FliSdk.Start(self.context)
        self.ReadParameters()

#-------------------------------------------------------------------#
    def OnExposureMaxClicked(self):
        if FliSdk.IsCred(self.context):
            val = float(self.ui.pb_exposureMax.text().split(':')[1])/1000.0
            if FliSdk.IsCredOne(self.context) or FliSdk.IsOcam2k(self.context):
                FliSdk.FliSerialCamera.SetFps(self.context, 1 / val)
            elif FliSdk.IsCredTwo(self.context):
                FliSdk.FliCredTwo.SetTint(self.context, val)
            elif FliSdk.IsCredThree(self.context):
                FliSdk.FliCredThree.SetTint(self.context, val)
            elif FliSdk.IsCredTwoLite(self.context):
                FliSdk.FliCredTwoLite.SetTint(self.context, val)
        elif FliSdk.IsCblueSfnc(self.context):
            wasStarted = FliSdk.IsStarted(self.context)
            if wasStarted:
                FliSdk.Stop(self.context)
            val = float(self.ui.pb_exposureMax.text().split(':')[1])*1000.0
            FliSdk.FliCblueSfnc.SetExposureTime(self.context, val)
            if wasStarted:
                FliSdk.Start(self.context)
        self.ReadParameters()

#-------------------------------------------------------------------#
    def OnBuildBiasClicked(self):
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QIcon(":/FliSdkDemo/image/icon.ico"))
        msgBox.setText("Building bias, please wait...")
        msgBox.setStandardButtons(QMessageBox.NoButton)
        msgBox.show()
        QApplication.processEvents()
        res = FliSdk.FliCred.BuildBias(self.context)
        if not res:
            msgBox.setText("Error while building bias.")
            msgBox.setStandardButtons(QMessageBox.Ok)
            msgBox.exec()
        msgBox.close()

#-------------------------------------------------------------------#
    def OnBadPixelClicked(self):
        FliSdk.FliCredTwo.EnableBadPixel(self.context, self.ui.cb_badPixel.isChecked())
        FliSdk.FliCredThree.EnableBadPixel(self.context, self.ui.cb_badPixel.isChecked())

#-------------------------------------------------------------------#
    def OnBiasClicked(self):
        FliSdk.FliSerialCamera.EnableBias(self.context, self.ui.cb_bias.isChecked())

#-------------------------------------------------------------------#
    def OnAntiBloomingClicked(self):
        FliSdk.FliCredTwo.EnableAntiBlooming(self.context, self.ui.cb_antiBlooming.isChecked())
        FliSdk.FliCredThree.EnableAntiBlooming(self.context, self.ui.cb_antiBlooming.isChecked())

#-------------------------------------------------------------------#
    def OnReverseXClicked(self):
        wasStarted = FliSdk.IsStarted(self.context)
        if wasStarted:
            FliSdk.Stop(self.context)
        FliSdk.FliCblueSfnc.SetReverseX(self.context, self.ui.cb_reverseX.isChecked())
        if wasStarted:
            FliSdk.Start(self.context)

#-------------------------------------------------------------------#
    def OnReverseYClicked(self):
        wasStarted = FliSdk.IsStarted(self.context)
        if wasStarted:
            FliSdk.Stop(self.context)
        FliSdk.FliCblueSfnc.SetReverseY(self.context, self.ui.cb_reverseY.isChecked())
        if wasStarted:
            FliSdk.Start(self.context)

#-------------------------------------------------------------------#
    def OnPixelFormat8bClicked(self):
        wasStarted = FliSdk.IsStarted(self.context)
        if wasStarted:
            FliSdk.Stop(self.context)
        FliSdk.FliCblueSfnc.SetPixelFormat(self.context, CblueOne.PixelFormat.Mono8)
        nbImagesBuffer = FliSdk.GetImagesCapacity(self.context)
        self.ui.progressBar_imageBuffer.setFormat("%v/" + str(nbImagesBuffer - 1))
        self.ui.progressBar_imageBuffer.setMaximum(nbImagesBuffer - 1)
        self.ui.progressBar_imageBuffer.setValue(0)
        self.ui.slider_imageIndex.setMaximum(nbImagesBuffer - 1)
        self.ui.sb_imageIndex.setMaximum(nbImagesBuffer-1)
        if wasStarted:
            FliSdk.Start(self.context)

#-------------------------------------------------------------------#
    def OnPixelFormat12bClicked(self):
        wasStarted = FliSdk.IsStarted(self.context)
        if wasStarted:
            FliSdk.Stop(self.context)
        FliSdk.FliCblueSfnc.SetPixelFormat(self.context, CblueOne.PixelFormat.Mono12)
        nbImagesBuffer = FliSdk.GetImagesCapacity(self.context)
        self.ui.progressBar_imageBuffer.setFormat("%v/" + str(nbImagesBuffer - 1))
        self.ui.progressBar_imageBuffer.setMaximum(nbImagesBuffer - 1)
        self.ui.progressBar_imageBuffer.setValue(0)
        self.ui.slider_imageIndex.setMaximum(nbImagesBuffer - 1)
        self.ui.sb_imageIndex.setMaximum(nbImagesBuffer-1)
        if wasStarted:
            FliSdk.Start(self.context)

#-------------------------------------------------------------------#
    def SendCommandToCamera(self, command):
        res, response = FliSdk.FliSerialCamera.SendCommand(self.context, command)
        self.console.PutData(response)

#-------------------------------------------------------------------#
    def OnAutoClipChanged(self):
        self.autoClipActivated = self.ui.cb_autoClip.checkState()

#-------------------------------------------------------------------#
    def OnImageIndexChanged(self):
        self.ui.slider_imageIndex.setValue(self.ui.sb_imageIndex.value())

#-------------------------------------------------------------------#
    def OnGammaChanged(self):
        FliSdk.ImageProcessing.SetGamma(self.context, -1, self.ui.sb_gamma.value())
        self.DisplayImage(-1)

#-------------------------------------------------------------------#
    def OnLoadRecord(self):
        cropData = FliSdk.CroppingData()
        fileName = QFileDialog.getOpenFileName(self,
		"Select File",
		"",
		"Images (*.raw *.flf)")
        print(fileName)

        if len(fileName[0]) == 0:
            return

        print(FliSdk.LoadBufferFromFile(self.context, fileName[0], cropData))
        bufFilling = FliSdk.GetBufferFilling(self.context)
        self.ui.progressBar_imageBuffer.setValue(bufFilling)
        self.ui.slider_imageIndex.setValue(bufFilling)
        self.ui.sb_imageIndex.setValue(bufFilling)
        self.DisplayImage(-1)

#-------------------------------------------------------------------#
    def OnSaveBufferCliked(self):
        fileName = QFileDialog.getSaveFileName(self,
        "Save buffer",
        "buffer",
        "raw files (*.raw);; firstlightframe (*.flf)")

        if not fileName[0]:
        	return

        FliSdk.SaveBufferWithOptions(self.context, fileName[0], self.ui.sb_startIndex.value(), self.ui.sb_endIndex.value(), None, True, 0, False, 0)

#-------------------------------------------------------------------#
    def OnActionCameraInfos(self):
        if self.ui.actionCamera_infos.isChecked():
            self.ui.vw_cameraInfos.setMaximumWidth(500)
        else:
            self.ui.vw_cameraInfos.setMaximumWidth(15)

#-------------------------------------------------------------------#
    def OnActionCameraSettings(self):
        if self.ui.actionCamera_settings.isChecked():
            self.ui.vw_cameraSettings.setMaximumWidth(235)
            self.ui.vw_cameraSettings.setMinimumWidth(235)
        else:
            self.ui.vw_cameraSettings.setMaximumWidth(10)
            self.ui.vw_cameraSettings.setMinimumWidth(10)

#-------------------------------------------------------------------#
    def OnActionConsole(self):
        if self.ui.actionConsole.isChecked():
            self.ui.spacerConsole.setMinimumHeight(30)
            self.console.setVisible(True)
            self.console.setFocus()
        else:
            self.ui.spacerConsole.setMinimumHeight(220)
            self.console.setVisible(False)

#-------------------------------------------------------------------#
    def OnSimplePrintClicked(self):
        self.lb_video.grab().save("capture.png", "PNG")
        #os.startfile("capture.png", "print")

#-------------------------------------------------------------------#
    def OnStandbyClicked(self):
        if(self.ui.cb_standby.isChecked()):
            res, response = FliSdk.FliSerialCamera.SendCommand(self.context, "set standby on")
        else:
            res, response = FliSdk.FliSerialCamera.SendCommand(self.context, "set standby off")
        self.console.PutData(response)

#-------------------------------------------------------------------#
    def OnCoolingClicked(self):
        if(self.ui.cb_cooling.isChecked()):
            res, response = FliSdk.FliSerialCamera.SendCommand(self.context, "set cooling on")
        else:
            res, response = FliSdk.FliSerialCamera.SendCommand(self.context, "set cooling off") 
        self.console.PutData(response)

#-------------------------------------------------------------------#
    def OnCroppingAction(self):
        cropData = FliSdk.CroppingData(self.context)
        cropData.col2 = int(self.ui.le_cropColumnMax.text())
        cropData.col1 = int(self.ui.le_cropColumnMin.text())
        cropData.row2 = int(self.ui.le_cropRowMax.text())
        cropData.row1 = int(self.ui.le_cropRowMin.text())
        res = FliSdk.IsCroppingDataValid(self.context, cropData)
        enable = self.ui.gb_cropping.isChecked()
        
        if res:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QIcon(":/FliSdkDemo/image/icon.png"))
            msgBox.setText("Setting cropping, please wait...")
            msgBox.setStandardButtons(QMessageBox.NoButton)
            msgBox.show()
            QApplication.processEvents()
            res = FliSdk.SetCroppingState(self.context, enable, cropData)

            if not res:
                msgBox.setText("Error while setting cropping.")
                msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.exec()
                return
            msgBox.close()
            self.ReadParameters()

#-------------------------------------------------------------------#
if __name__=='__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()
