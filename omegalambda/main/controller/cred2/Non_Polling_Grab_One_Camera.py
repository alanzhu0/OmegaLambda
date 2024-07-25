import FliSdk_V2

import ctypes

CLBKFUNC = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.POINTER(ctypes.c_byte), ctypes.c_void_p)
def callback(image, context = None):
    data_tot = image
    
    """Do work here"""
    
    print('Got an image !')
    
clbk_func = CLBKFUNC(callback)

#################################################################################################

context = FliSdk_V2.Init()

print("Detection of grabbers...")
listOfGrabbers = FliSdk_V2.DetectGrabbers(context)

if len(listOfGrabbers) == 0:
    print("No grabber detected, exit.")
    exit()

print("Done.")
print("List of detected grabber(s):")

for s in listOfGrabbers:
    print("- " + s)

print("Detection of cameras...")
listOfCameras = FliSdk_V2.DetectCameras(context)
ip = ctypes.c_char_p(b"169.254.123.123")
username = ctypes.c_char_p(b"admin")
password = ctypes.c_char_p(b"flicred1")
listOfCameras = [FliSdk_V2.AddEthernetCamera(context, ip, username, password)[1]]

if len(listOfCameras) == 0:
    print("No camera detected, exit.")
    exit()

print("Done.")
print("List of detected camera(s):")

i = 0
for s in listOfCameras:
    print("- " + str(i) + " -> " + s)
    i = i + 1

cameraIndex = int(input("Which camera to use? (0, 1, ...) "))
print("Setting camera: " + listOfCameras[cameraIndex])
ok = FliSdk_V2.SetCamera(context, listOfCameras[cameraIndex])

if not ok:
    print("Error while setting camera.")
    exit()

print("Setting mode full.")
FliSdk_V2.SetMode(context, FliSdk_V2.Mode.Full)

print("Updating...")
ok = FliSdk_V2.Update(context)

if not ok:
    print("Error while updating SDK.")
    exit()

print("Done.")

fps = 0

if FliSdk_V2.IsSerialCamera(context):
    res, fps = FliSdk_V2.FliSerialCamera.GetFps(context)
elif FliSdk_V2.IsCblueSfnc(context):
    res, fps = FliSdk_V2.FliCblueSfnc.GetAcquisitionFrameRate(context)
print("Current camera FPS: " + str(fps))

val = input("FPS to set? ")
try:
    valFloat = float(val)
    if FliSdk_V2.IsSerialCamera(context):
        FliSdk_V2.FliSerialCamera.SetFps(context, valFloat)
    elif FliSdk_V2.IsCblueSfnc(context):
        FliSdk_V2.FliCblueSfnc.SetAcquisitionFrameRate(context, valFloat)
except:
    print("Value is not a float")

if FliSdk_V2.IsSerialCamera(context):
    res, fps = FliSdk_V2.FliSerialCamera.GetFps(context)
elif FliSdk_V2.IsCblueSfnc(context):
    res, fps = FliSdk_V2.FliCblueSfnc.GetAcquisitionFrameRate(context)
print("FPS read: " + str(fps))

if FliSdk_V2.IsCredTwo(context) or FliSdk_V2.IsCredThree(context) or FliSdk_V2.IsCredTwoLite(context):
    res, response = FliSdk_V2.FliSerialCamera.SendCommand(context, "mintint raw")
    minTint = float(response)

    res, response = FliSdk_V2.FliSerialCamera.SendCommand(context, "maxtint raw")
    maxTint = float(response)

    res, response = FliSdk_V2.FliSerialCamera.SendCommand(context, "tint raw")

    print("Current camera tint: " + str(float(response)*1000) + "ms")

    val = input("Tint to set? (between " + str(minTint*1000) + "ms and " + str(maxTint*1000)+ "ms) ")
    try:
        valFloat = float(val)
        res, response = FliSdk_V2.FliSerialCamera.SendCommand(context, "set tint " + str(valFloat/1000))
    except:
        print("Value is not a float")

    res, response = FliSdk_V2.FliSerialCamera.SendCommand(context, "tint raw")
    print("Current camera tint: " + str(float(response)*1000) + "ms")
elif FliSdk_V2.IsCblueSfnc(context):
    res, tint = FliSdk_V2.FliCblueSfnc.GetExposureTime(context)
    print("Current camera tint: " + str(tint/1000) + "ms")
    
UserContext = None
FliSdk_V2.EnableRingBuffer(context, True)
callbackContext = FliSdk_V2.AddCallBackNewImage(context, clbk_func, 0, False, UserContext)
FliSdk_V2.Start(context)

val = input("Type anything to exit")

FliSdk_V2.Stop(context)
FliSdk_V2.Exit(context)
