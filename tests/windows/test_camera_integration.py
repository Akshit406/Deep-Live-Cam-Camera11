from pathlib import Path
import sys, os, subprocess, json

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["KERAS_BACKEND"] = "torch"
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
root = Path(__file__).resolve().parents[2]
import run  # noqa: F401 - register bundled native DLL directories
import numpy as np
from modules import ui, globals as g
from modules.virtual_camera import CAMERA_NAME
from PySide6.QtWidgets import QApplication
from pygrabber.dshow_graph import FilterGraph

all_devices = FilterGraph().get_input_devices()
indices, names = ui.get_available_cameras()
assert CAMERA_NAME in all_devices and CAMERA_NAME not in names
assert all(all_devices[i] == name for i, name in zip(indices, names))
print("Source-camera filtering preserves device indexes", flush=True)
app = QApplication.instance() or QApplication([])
g.execution_providers = ["CUDAExecutionProvider"]
g.frame_processors = ["face_swapper"]
g.headless = True
ui.update_status = lambda text, *args: print(text, flush=True)


class FakeCapture:
    actual_fps = 30
    actual_width = 1280
    actual_height = 720

    def __init__(self, *args):
        self.released = False

    def start(self, *args):
        return True

    def release(self):
        self.released = True


class IdleWorker:
    def __init__(self, *args):
        pass

    def start(self):
        pass

    def wait(self, *args):
        pass


ui.VideoCapturer = FakeCapture
ui._CaptureWorker = IdleWorker
ui._ProcessingWorker = IdleWorker
window = ui.WebcamPreviewWindow(0)
try:
    window._processed_queue.put(np.full((720, 1280, 3), (0, 0, 255), np.uint8))
    window._tick()
    identifier = (
        "@device_sw_{860BB310-5D01-11D0-BD3B-00A0C911CE86}"
        + chr(92)
        + json.loads((root / "virtual-camera/camera.json").read_text())["clsid"]
    )
    result = subprocess.run(
        [
            str(root / "ffmpeg.exe"),
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "dshow",
            "-video_size",
            "1280x720",
            "-framerate",
            "30",
            "-i",
            "video=" + identifier,
            "-frames:v",
            "3",
            "-pix_fmt",
            "bgr24",
            "-f",
            "rawvideo",
            "pipe:1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=25,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    frames = np.frombuffer(result.stdout, np.uint8).reshape(3, 720, 1280, 3)
    pixel = frames[-1, 360, 640]
    assert pixel[2] > 240 and pixel[0] < 15 and pixel[1] < 15, pixel
    print("Processed preview frame received by separate camera client", flush=True)
finally:
    window.close()
assert window._virtual_camera is None and window._cap.released
print("Preview close releases output and input", flush=True)


class FailedCapture(FakeCapture):
    def start(self, *args):
        return False


ui.VideoCapturer = FailedCapture
failed = ui.WebcamPreviewWindow(0)
failed.close()
app.processEvents()
print("Camera-open failure cleans up safely", flush=True)
print("APP INTEGRATION VERIFIED", flush=True)
