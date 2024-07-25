import ctypes
import os

lib = ctypes.cdll.LoadLibrary("C:\\Program Files\\First Light Imaging\\SDK_1_4_0\\lib\\release\\FliSdk_vision.dll")

# _DIRNAME = os.getenv('FliSdk', 'C:\\Program Files\\FirstLightImaging\\FliSdk')

# # _DIRNAME = "/media/alan/341C06871C064478/Program Files/FirstLightImaging/FliSdk"

# if os.name == 'nt':
#     lib = ctypes.cdll.LoadLibrary(_DIRNAME + "\\lib\\release\\FliSdk.dll")
# elif os.name == 'posix':
#     if "aarch64" in str(os.uname()):
#         lib = ctypes.cdll.LoadLibrary(_DIRNAME + "/lib/libFliSdk.so")
#     else:
#         lib = ctypes.cdll.LoadLibrary(_DIRNAME + "/lib/release/libFliSdk.so")

CWRAPPER = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)