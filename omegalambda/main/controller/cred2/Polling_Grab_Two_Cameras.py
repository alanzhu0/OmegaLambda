import FliSdk_V2

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

context_bis = 0
if len(listOfCameras) > 1:
    val = input("do you want to use a second camera? (y/n) ")
    if val == "y" or val == "yes":
        context_bis = FliSdk_V2.Init()

        print("Detection of grabbers...")
        listOfGrabbers = FliSdk_V2.DetectGrabbers(context_bis)

        if len(listOfGrabbers) == 0:
            print("No grabber detected, exit.")
            exit()

        print("Done.")
        print("List of detected grabber(s):")

        for s in listOfGrabbers:
            print("- " + s)

        print("Detection of cameras...")
        listOfCameras = FliSdk_V2.DetectCameras(context_bis)

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
        ok = FliSdk_V2.SetCamera(context_bis, listOfCameras[cameraIndex])

        if not ok:
            print("Error while setting camera.")
            exit()

        print("Setting mode full.")
        FliSdk_V2.SetMode(context_bis, FliSdk_V2.Mode.Full)

        print("Updating...")
        ok = FliSdk_V2.Update(context_bis)

        if not ok:
            print("Error while updating SDK.")
            exit()

        print("Done.")

        fps = 0

        if FliSdk_V2.IsSerialCamera(context_bis):
            res, fps = FliSdk_V2.FliSerialCamera.GetFps(context_bis)
        elif FliSdk_V2.IsCblueSfnc(context_bis):
            res, fps = FliSdk_V2.FliCblueSfnc.GetAcquisitionFrameRate(context_bis)
        print("Current camera FPS: " + str(fps))

        val = input("FPS to set? ")
        try:
            valFloat = float(val)
            if FliSdk_V2.IsSerialCamera(context_bis):
                FliSdk_V2.FliSerialCamera.SetFps(context_bis, valFloat)
            elif FliSdk_V2.IsCblueSfnc(context_bis):
                FliSdk_V2.FliCblueSfnc.SetAcquisitionFrameRate(context_bis, valFloat)
        except:
            print("Value is not a float")

        if FliSdk_V2.IsSerialCamera(context_bis):
            res, fps = FliSdk_V2.FliSerialCamera.GetFps(context_bis)
        elif FliSdk_V2.IsCblueSfnc(context_bis):
            res, fps = FliSdk_V2.FliCblueSfnc.GetAcquisitionFrameRate(context_bis)
        print("FPS read: " + str(fps))

        if FliSdk_V2.IsCredTwo(context) or FliSdk_V2.IsCredThree(context) or FliSdk_V2.IsCredTwoLite(context):
            res, response = FliSdk_V2.FliSerialCamera.SendCommand(context_bis, "mintint raw")
            minTint = float(response)

            res, response = FliSdk_V2.FliSerialCamera.SendCommand(context_bis, "maxtint raw")
            maxTint = float(response)

            res, response = FliSdk_V2.FliSerialCamera.SendCommand(context_bis, "tint raw")

            print("Current camera tint: " + str(float(response)*1000) + "ms")

            val = input("Tint to set? (between " + str(minTint*1000) + "ms and " + str(maxTint*1000)+ "ms) ")
            try:
                valFloat = float(val)
                res, response = FliSdk_V2.FliSerialCamera.SendCommand(context_bis, "set tint " + str(valFloat/1000))
            except:
                print("Value is not a float")

            res, response = FliSdk_V2.FliSerialCamera.SendCommand(context_bis, "tint raw")
            print("Current camera tint: " + str(float(response)*1000) + "ms")
        elif FliSdk_V2.IsCblueSfnc(context_bis):
            res, tint = FliSdk_V2.FliCblueSfnc.GetExposureTime(context_bis)
            print("Current camera tint: " + str(tint/1000) + "ms")

val = input("How much images to read? ")
if not val.isnumeric():
    val = 600

FliSdk_V2.ImageProcessing.EnableAutoClip(context, -1, True)
FliSdk_V2.ImageProcessing.SetColorMap(context, -1, "RAINBOW")

if context_bis != 0:
    FliSdk_V2.ImageProcessing.EnableAutoClip(context_bis, -1, True)
    FliSdk_V2.ImageProcessing.SetColorMap(context_bis, -1, "PLASMA")

cameraName = FliSdk_V2.GetCurrentCameraName(context)
FliSdk_V2.Start(context)

cameraName_bis = ""
if context_bis != 0:
    FliSdk_V2.Start(context_bis)
    cameraName_bis = FliSdk_V2.GetCurrentCameraName(context_bis)

for i in range(int(val)):
    image = FliSdk_V2.GetProcessedImage(context, -1) #-1 to get the last image in the buffer
    FliSdk_V2.Display8bImage(context, image, cameraName + " image 8b")
    image = FliSdk_V2.GetRawImage(context, -1)
    FliSdk_V2.Display16bImage(context, image, cameraName + " image 16b", False)

    if context_bis != 0:
        image = FliSdk_V2.GetProcessedImage(context_bis, -1) #-1 to get the last image in the buffer
        FliSdk_V2.Display8bImage(context_bis, image, cameraName_bis + " image 8b")
        image = FliSdk_V2.GetRawImage(context_bis, -1)
        FliSdk_V2.Display16bImage(context_bis, image, cameraName_bis + " image 16b", False)

FliSdk_V2.Stop(context)
FliSdk_V2.Exit(context)

if context_bis != 0:
    FliSdk_V2.Stop(context_bis)
    FliSdk_V2.Exit(context_bis)