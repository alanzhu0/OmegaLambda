import FliSdk_V2
import ctypes

context = FliSdk_V2.Init()


print("Detection of grabbers...")
listOfGrabbers = FliSdk_V2.DetectGrabbers(context)
# print("Start ethernet grabber", FliSdk_V2.FliCredTwo.StartEthernetGrabber(context))
# print("Serial", FliSdk_V2.FliSerialCamera.SendCommand(context, "exec ethernetgrabber start"))
# print("Set grabber", FliSdk_V2.SetGrabber(context, "Ethernet#"))


if len(listOfGrabbers) == 0:
    print("No grabber detected, exit.")
    exit()

print("Done.")
print("List of detected grabber(s):")

for s in listOfGrabbers:
    print("- " + s)

print("Detection of cameras...")
# listOfCameras = FliSdk_V2.DetectCameras(context)
ip = ctypes.c_char_p(b"169.254.123.123")
username = ctypes.c_char_p(b"admin")
password = ctypes.c_char_p(b"flicred1")
listOfCameras = [FliSdk_V2.AddEthernetCamera(context, ip, username, password)[1]]
print(listOfCameras)

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

val = input("How much images to read? ")
if not val.isnumeric():
    val = 600

FliSdk_V2.ImageProcessing.EnableAutoClip(context, -1, True)
FliSdk_V2.ImageProcessing.SetColorMap(context, -1, "RAINBOW")
FliSdk_V2.Start(context)

for i in range(int(val)):
    image = FliSdk_V2.GetProcessedImage(context, -1) #-1 to get the last image in the buffer
    FliSdk_V2.Display8bImage(context, image, "image 8b")
    image = FliSdk_V2.GetRawImage(context, -1)
    FliSdk_V2.Display16bImage(context, image, "image 16b", False)

input("Press Enter to exit. ")
FliSdk_V2.FliCredTwo.StopEthernetGrabber(context)
FliSdk_V2.Stop(context)
FliSdk_V2.Exit(context)
