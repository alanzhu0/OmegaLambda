# CRED2 Camera Image Capture - Alan Zhu, 2024-06-21

from astropy.io import fits
import ctypes
import cv2
import numpy as np
import os
import json
import psutil
import queue
import signal
import subprocess
import sys
import threading
from tqdm import tqdm
from time import sleep
from datetime import datetime, timezone

# from PIL import Image

import FliSdk_V2 as FliSdk


########## Hardcoded - should not need to modify ##########
FILENAME_NUM_LENGTH: int = 8
FILENAME_NUM: int = 0
COMPRESS_CMD: list[str] = ["C:\\Program Files (x86)\\CFITSIO\\bin\\fpack.exe", "-h", "-F", "-Y"]
COMPRESS_GROUP_SIZE: int = 100
MAX_COMPRESS_PROCESSES: int = 10
IP_ADDRESS: ctypes.c_char_p = ctypes.c_char_p(b"169.254.123.123")
USERNAME: ctypes.c_char_p = ctypes.c_char_p(b"admin")
PASSWORD: ctypes.c_char_p = ctypes.c_char_p(b"flicred1")
CONTEXT: ctypes.c_void_p = None
TEMPERATURE: float = -40.0  # Celsius
TEMP_THRESHOLD: float = 0.5  # Celsius. Temperature threshold for cooler to reach setpoint.
FRAME_TIME: float = 0.04  # Seconds. Optimal individual frame exposure time for CRED2 camera.
TIME_SCALE_FACTOR: float = 36.0  # Because we don't get accurate frame rates (much higher than expected), compensate for it by increasing the stack time (empirically determined).

CONFIG_FILE: str = os.path.join(os.path.dirname(__file__), "cred2_capture_config.json")
"""Example config file:
{
    "total_run_time_seconds": 0.0,
    "image_stack_time_seconds": 1.0,
    "take_calibration_images": false,
    "data_directory": "data",
    "filename_prefix": "image-",
    "enable_compression": true,
    "wait_for_cooler_settle": true
}
"""
TOTAL_RUN_TIME: float = 0.0 * TIME_SCALE_FACTOR  # Seconds. Total time to capture images for. 0 for continuous capture.
IMAGE_STACK_TIME: float = 1.0 * TIME_SCALE_FACTOR  # Seconds. Stacked exposure time for the stacked images.
TAKE_CALIBRATION_IMAGES: bool = False  # Take biases, darks, flats
DATA_DIRECTORY: str = "data"
FILENAME_PREFIX: str = "image-"
ENABLE_COMPRESSION: bool = True  # Compress images after saving using fpack
WAIT_FOR_COOLER_SETTLE: bool = True  # Wait for cooler to reach setpoint before capturing images

# Load config
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        TOTAL_RUN_TIME = config.get("total_run_time_seconds", TOTAL_RUN_TIME) * TIME_SCALE_FACTOR
        IMAGE_STACK_TIME = config.get("image_stack_time_seconds", IMAGE_STACK_TIME) * TIME_SCALE_FACTOR
        TAKE_CALIBRATION_IMAGES = config.get("take_calibration_images", TAKE_CALIBRATION_IMAGES)
        DATA_DIRECTORY = config.get("data_directory", DATA_DIRECTORY)
        FILENAME_PREFIX = config.get("filename_prefix", FILENAME_PREFIX)
        ENABLE_COMPRESSION = config.get("enable_compression", ENABLE_COMPRESSION)
        WAIT_FOR_COOLER_SETTLE = config.get("wait_for_cooler_settle", WAIT_FOR_COOLER_SETTLE)


########## Calculated parameters ##########
IMAGE_STACK_SIZE: int = int(IMAGE_STACK_TIME / FRAME_TIME)  # Number of images to stack for each stacked image. 1 for no stacking.
NUM_IMAGES = max(int(TOTAL_RUN_TIME / IMAGE_STACK_TIME), 1)  # Number of images to capture.
CONTINUOUS_CAPTURE: bool = TOTAL_RUN_TIME == 0.0  # If True, will capture images continuously until stopped
FPS: float = 1 / FRAME_TIME
FITS_HEADER: dict[str, str | float] = {  # For FITS headers
    "ORIGIN": "George Mason University Observatory",
    "INSTRUME": "CRED2 Near-Infrared Camera",
    "OBSERVER": "GMU CRED2 automation code",
    "EXPTIME": IMAGE_STACK_TIME,
    "FRAMTIME": FRAME_TIME,
    "SET-TEMP": TEMPERATURE,
    "DATE": None,
}

########## Helpers ##########
def create_save_directory() -> None:
    if not os.path.exists(DATA_DIRECTORY):
        os.makedirs(DATA_DIRECTORY)
        print(f"Created directory {DATA_DIRECTORY} for saving images.")
    elif not os.path.isdir(DATA_DIRECTORY):
        print(f"Error: {DATA_DIRECTORY} is not a directory.")
        disconnect()
        exit()
    elif len(os.listdir(DATA_DIRECTORY)) > 0:
        # If directory already exists, attempt to continue numbering from last image
        try:
            global FILENAME_NUM
            FILENAME_NUM = max(
                int(file[len(FILENAME_PREFIX): len(FILENAME_PREFIX) + FILENAME_NUM_LENGTH]) 
                for file in os.listdir(DATA_DIRECTORY) 
                if file.startswith(FILENAME_PREFIX)
            )
            print(f"Continuing numbering from image {FILENAME_NUM}.")
        except ValueError:
            print(f"Error: {DATA_DIRECTORY} contains files that do not match the expected format. Attempting to continue.")
            pass

    print(f"Saving images to {DATA_DIRECTORY}.")


########## Camera control ##########
def setup() -> None:
    print("Setting up CRED2 camera.")
    
    FliSdk.Update(CONTEXT)
    FliSdk.Start(CONTEXT)
    set_temp(TEMPERATURE)

    create_save_directory()

    if WAIT_FOR_COOLER_SETTLE:
        print("Waiting for cooler to reach setpoint...")
        temp = get_temp()
        while abs(temp - TEMPERATURE) > TEMP_THRESHOLD:
            sleep(2)
            temp = get_temp()
            print(temp, end=" ")
        print("\nCooler has reached setpoint.")

    if TAKE_CALIBRATION_IMAGES:
        take_calibration_images()
    
    set_fps(FPS)
    
    sleep(2)  # Wait for camera to set up
    print("CRED2 camera setup complete.")


def connect() -> None:
    global CONTEXT
    CONTEXT = FliSdk.Init()

    print("Attempting to connect to CRED2 camera via Ethernet...")
    camera: str = FliSdk.AddEthernetCamera(CONTEXT, IP_ADDRESS, USERNAME, PASSWORD)[1]
    
    if not camera:
        print("Could not connect to CRED2 camera via Ethernet.")
        disconnect()
        exit()

    FliSdk.SetCamera(CONTEXT, camera)
    print("Connected to CRED2 camera via Ethernet.")


def disconnect() -> None:
    FliSdk.Stop(CONTEXT)
    FliSdk.Exit(CONTEXT)
    print("Disconnected from CRED2 camera.")


def get_fps() -> float:
    return FliSdk.FliSerialCamera.GetFps(CONTEXT)[1]


def set_fps(fps: float) -> float:
    FliSdk.FliSerialCamera.SetFps(CONTEXT, fps)
    print(f"FPS set to {get_fps()}.")


def get_temp() -> float:
    return FliSdk.FliCredTwo.GetTempSnake(CONTEXT)[1]


def set_temp(temp: float) -> float:
    FliSdk.FliCredTwo.SetTempSnakeSetPoint(CONTEXT, temp)
    print(f"Temperature setpoint set to {FliSdk.FliCredTwo.GetTempSnakeSetPoint(CONTEXT)[1]} C.")
    print(f"Current temperature: {get_temp()} C.")


########## Calibration images ##########
NUM_DARK_FRAMES: int = max(int(get_fps() * 60), 20)
NUM_FLAT_FRAMES: int = NUM_DARK_FRAMES
FLAT_FPS: float = 10.0


def take_darks() -> None:
    set_fps(FPS)
    print(f"Taking {NUM_DARK_FRAMES} dark frames at {FPS} FPS.")
    take_calibration_image("dark", NUM_DARK_FRAMES)


def take_flats() -> None:
    set_fps(FLAT_FPS)
    print(f"Taking {NUM_FLAT_FRAMES} flat frames at {FPS} FPS.")
    take_calibration_image("flat", NUM_FLAT_FRAMES)


def take_calibration_images() -> None:
    print("-" * 40)
    print("Beginning calibration images procedure.")
    print("Preparing to take dark frames. Place the lens cap on the camera to ensure no light enters the sensor.")
    input("Press Enter to continue... ")

    take_darks()
    print()

    # print(f"Taking {NUM_BIAS_FRAMES} bias frames at {BIAS_FPS} FPS.")
    # set_fps(BIAS_FPS)
    # take_calibration_image("bias", NUM_BIAS_FRAMES)
    # print()

    print("Preparing to take flat frames. Remove the lens cap from the camera and evenly illuminate the sensor.")
    input("Press Enter to continue... ")
    take_flats()

    print("Done taking calibration images.")
    print("-" * 40)


def take_calibration_image(calibration_type, num_frames) -> None:
    images: list[np.ndarray[np.uint16]] = [get_image() for _ in range(num_frames)]
    image = median_images(images)
    annotation = f"{calibration_type}_{FPS / 60:.2f}s"
    path = write_to_fits(image, annotation=annotation)
    print(f"Calibration image saved to {path}.")
    compress(path)


########## Image processing ##########
def get_image() -> np.ndarray[np.uint16]:
    return FliSdk.GetRawImageAsNumpyArray(CONTEXT, -1)
    # return FliSdk.GetProcessedImageGrayscale16bNumpyArray(CONTEXT, -1)


def stack_images(images: list[np.ndarray[np.uint16]]) -> np.ndarray[np.uint32]:
    """Stack images by summing pixel values."""
    return np.sum(images, axis=0, dtype=np.uint32)


def median_images(images: list[np.ndarray[np.uint16]]) -> np.ndarray[np.uint16]:
    """Return an image with the median of the pixel values of the images."""
    return np.median(images, axis=0, dtype=np.uint16)


def write_to_fits(image: np.ndarray[np.uint16 | np.uint32], annotation: str = "") -> str:
    global FILENAME_NUM, FITS_HEADER
    FILENAME_NUM += 1
    FITS_HEADER["DATE"] = datetime.now(timezone.utc).strftime('%F %T.%f')[:-3]
    header: fits.Header = fits.Header(FITS_HEADER)
    hdu: fits.PrimaryHDU = fits.PrimaryHDU(image, header=header)
    filename: str = f"{DATA_DIRECTORY}/{FILENAME_PREFIX}{str(FILENAME_NUM).zfill(FILENAME_NUM_LENGTH)}{'_' + annotation if annotation else ''}.fits"
    hdu.writeto(filename)
    return filename
    # image_8bit = np.array(Image.fromarray(image, mode="RGBA").convert("L"))
    # hdu_8bit: fits.PrimaryHDU = fits.PrimaryHDU(image_8bit)
    # filename_8bit: str = f"{DATA_DIRECTORY}/{FILENAME_PREFIX}{str(FILENAME_NUM).zfill(FILENAME_NUM_LENGTH)}_8bit.fits"
    # hdu_8bit.writeto(filename_8bit)


def compress(path: str) -> None:
    subprocess.Popen(COMPRESS_CMD + [path])


def compress_group(paths: list[str]) -> None:
    subprocess.Popen(COMPRESS_CMD + paths)


def show_image(image: np.ndarray[np.uint16] | np.ndarray[np.uint32]) -> None:
    # Need to be careful to not modify complex data types
    # display_image = np.array(Image.fromarray(image, mode="RGBA").convert("L")) if image.dtype == np.uint32 else image
    display_image = image.astype(np.uint16) if image.dtype == np.uint32 else image
    cv2.imshow("CRED2 Camera", display_image)
    cv2.waitKey(1)


########## Threads ##########
write_queue = queue.Queue()
display_queue = queue.Queue()
compress_queue = queue.Queue()

read_th: threading.Thread = None
write_th: threading.Thread = None
compress_th: threading.Thread = None

stop_event = threading.Event()
continue_taking_images = threading.Event()  # If False, will pause taking images
continue_taking_images.set()


def stop_threads(*args, script_done=False) -> None:
    print("Stopping threads...")
    stop_event.set()
    if read_th and not script_done:
        read_th.join()
    if write_th:
        write_th.join()
    if ENABLE_COMPRESSION and compress_th:
        compress_th.join()
    if CONTEXT:
        disconnect()
    exit()


def pause_captures() -> None:
    print("Pausing image captures.")
    continue_taking_images.clear()


def resume_captures() -> None:
    print("Resuming image captures.")
    continue_taking_images.set()


def read_thread() -> None:
    read_images = 0

    if IMAGE_STACK_SIZE > 1:
        if CONTINUOUS_CAPTURE:
            images: list[np.ndarray[np.uint16]] = []
            while not stop_event.is_set():
                continue_taking_images.wait()
                images.append(get_image())
                if len(images) >= IMAGE_STACK_SIZE:
                    image = stack_images(images)
                    images.clear()
                    write_queue.put(image)
                    display_queue.put(image)
                    read_images += 1
        else:
            for _ in tqdm(range(NUM_IMAGES), unit="images"):
                continue_taking_images.wait()
                images = [get_image() for _ in range(IMAGE_STACK_SIZE)]
                image = stack_images(images)
                write_queue.put(image)
                read_images += 1
                if stop_event.is_set():
                    break
    else:
        if CONTINUOUS_CAPTURE:
            while not stop_event.is_set():
                continue_taking_images.wait()
                image = get_image()
                write_queue.put(image)
                display_queue.put(image)
                read_images += 1
        else:
            for _ in tqdm(range(NUM_IMAGES), unit="images"):
                continue_taking_images.wait()
                image = get_image()
                write_queue.put(image)
                read_images += 1
                if stop_event.is_set():
                    break

    if read_images >= NUM_IMAGES and not CONTINUOUS_CAPTURE:
        print()
        print(f"Done capturing {NUM_IMAGES} images.")
        # wait_time = write_queue.qsize() * 0.05 + (compress_queue.qsize() * 0.1 if ENABLE_COMPRESSION else 0)
        # if wait_time > 0:
        #     wait_time += 1
        #     print(f"Waiting for {wait_time:.2f} seconds for remaining images to be saved and compressed...")
        #     sleep(wait_time)
        stop_threads(script_done=True)


def write_thread() -> None:
    while not stop_event.is_set():
        image = write_queue.get()
        path = write_to_fits(image)
        write_queue.task_done()
        if ENABLE_COMPRESSION:
            compress_queue.put(path)


def compress_thread() -> None:
    compress_group_paths: list[str] = []

    while not stop_event.is_set():
        path = compress_queue.get()
        compress_group_paths.append(path)
        compress_queue.task_done()

        if len(compress_group_paths) >= COMPRESS_GROUP_SIZE:
            while sum(1 for p in psutil.process_iter() if p.name() == "fpack.exe") >= MAX_COMPRESS_PROCESSES and not stop_event.is_set():
                sleep(0.5)
            compress_group(compress_group_paths)
            compress_group_paths.clear()


def display_thread() -> None:
    while not stop_event.is_set():
        image = display_queue.get()
        show_image(image)
        with display_queue.mutex:
            display_queue.queue.clear()  # Always show the latest image
        display_queue.task_done()


########## Main ##########
def main() -> None:
    signal.signal(signal.SIGINT, stop_threads)
    signal.signal(signal.SIGTERM, stop_threads)
    signal.signal(signal.SIGABRT, pause_captures)  # Send SIGABRT to pause captures 
    signal.signal(signal.SIGILL, resume_captures)  # Send SIGILL to resume captures

    connect()
    setup()
    
    if len(sys.argv) > 1 and (calibration_image := sys.argv[1]) in ("darks", "flats"):
        if calibration_image == "darks":
            take_darks()
        elif calibration_image == "flats":
            take_flats()
        stop_threads(script_done=True)

    if NUM_IMAGES <= 0:
        print("No images to capture.")
        stop_threads(script_done=True)
    
    print("Starting threads...")
    global read_th, write_th
    read_th = threading.Thread(target=read_thread)
    read_th.start()
    write_th = threading.Thread(target=write_thread)
    write_th.start()
    
    if ENABLE_COMPRESSION:
        compress_th = threading.Thread(target=compress_thread)
        compress_th.start()
        
    if CONTINUOUS_CAPTURE:
        print("Press CTRL+C to stop capturing images.")
        display_thread()
    else:
        print('-' * 40)
        print("Capturing images.")
        print(f"Number of images: {NUM_IMAGES}.")
        print(f"Total run time: {NUM_IMAGES * (IMAGE_STACK_TIME / TIME_SCALE_FACTOR)} seconds.")
        print(f"Stacked exposure time: {IMAGE_STACK_TIME / TIME_SCALE_FACTOR} seconds.")
        print(f"Individual frame exposure time: {FRAME_TIME} seconds ({FPS} FPS).")
        print("Press CTRL+C to stop capturing images prematurely.")
        print()


if __name__ == "__main__":
    main()
