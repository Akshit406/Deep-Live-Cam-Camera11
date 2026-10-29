"""Mode 2 UI-to-DirectShow integration using generated photos only."""

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["KERAS_BACKEND"] = "torch"
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
import run  # noqa: F401 - register bundled native DLL directories
import numpy as np
from PIL import Image
from PySide6.QtWidgets import QApplication
from modules import ui, photo_stream


def read_camera():
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
            "4",
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
    return np.frombuffer(result.stdout, np.uint8).reshape(4, 720, 1280, 3)[-1]


app = QApplication.instance() or QApplication([])
app.setStyleSheet(ui.QSS)
# Mode 2 must function even without any physical cameras.
ui.get_available_cameras = lambda: ([], ["No cameras found"])
closed = []
window = ui.MainWindow(lambda: None, lambda: closed.append(True))
window.show()
window.mode_selector.setCurrentIndex(1)
app.processEvents()
panel = window.photo_panel
assert window.mode_stack.currentWidget() is panel
assert not panel.start_button.isEnabled()
panel.start_stream()
assert panel._camera is None
with tempfile.TemporaryDirectory(prefix="camera11-photo-test-") as folder:
    folder = Path(folder)
    red = folder / "portrait-test.png"
    Image.new("RGB", (300, 600), (255, 0, 0)).save(red)
    green = folder / "landscape-test.png"
    Image.new("RGB", (1280, 720), (0, 255, 0)).save(green)
    try:
        with patch.object(
            photo_stream.QFileDialog, "getOpenFileName", return_value=(str(red), "")
        ):
            panel.select_button.click()
        assert panel._frame.shape == (600, 300, 3)
        panel.start_button.click()
        assert panel._camera is not None, panel.status.text()
        received = read_camera()
        assert received[:, :400].max() < 5
        assert received[:, 880:].max() < 5
        assert received[360, 640, 2] > 240 and received[360, 640, :2].max() < 15
        print(
            "PASS: gallery picker -> portrait photo -> separate DirectShow client, proportions preserved",
            flush=True,
        )
        app.processEvents()
        window.grab().save(str(root / "virtual-camera/mode2-preview.png"))
        camera = panel._camera
        with patch.object(
            photo_stream.QFileDialog, "getOpenFileName", return_value=("", "")
        ):
            panel.select_button.click()
        bad = folder / "corrupt.png"
        bad.write_text("not an image")
        assert not panel.load_image(str(bad))
        assert panel._camera is camera and panel.filename.text() == red.name
        assert panel.load_image(str(green))
        received = read_camera()
        assert received[:, :, 1].mean() > 240 and received[:, :, (0, 2)].max() < 15
        print(
            "PASS: cancel/corrupt image preserves stream; choosing another photo updates live output",
            flush=True,
        )
        panel.stop_button.click()
        assert panel._camera is None
        assert read_camera().max() < 5
        print("PASS: Stop outputs black and releases publisher", flush=True)
        # Phone orientation and transparent PNG decoding.
        rotated = folder / "phone.jpg"
        exif = Image.Exif()
        exif[274] = 6
        Image.new("RGB", (80, 40), (255, 255, 255)).save(rotated, exif=exif)
        assert panel.load_image(str(rotated))
        assert panel._frame.shape == (80, 40, 3)
        transparent = folder / "transparent.png"
        Image.new("RGBA", (20, 20), (255, 0, 0, 0)).save(transparent)
        assert panel.load_image(str(transparent)) and panel._frame.max() == 0
        print("PASS: phone rotation and image transparency handled", flush=True)
        assert panel.load_image(str(green))
        panel.start_stream()
        window.mode_selector.setCurrentIndex(0)
        assert panel._camera is None
        app.processEvents()
        window.grab().save(str(root / "virtual-camera/mode1-preview.png"))
        window.mode_selector.setCurrentIndex(1)
        assert panel._camera is None and panel.start_button.isEnabled()
        panel.start_stream()
        # A competing publisher receives a useful error and cannot disrupt the active one.
        second = photo_stream.PhotoStreamPanel()
        second.load_image(str(red))
        second.start_stream()
        assert second._camera is None and "already active" in second.status.text()
        second.close()
        received = read_camera()
        assert received[360, 640, 1] > 240
        window.close()
        assert closed and panel._camera is None
        print(
            "PASS: mode change, duplicate stream protection, restart, and app close cleanup",
            flush=True,
        )
    finally:
        panel.stop_stream()
        window.close()


# Simulate an asynchronous delivery failure and verify recoverable controls.
class BrokenPublisher:
    error = "test delivery failure"

    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


broken = BrokenPublisher()
panel._camera = broken
panel._check_stream()
assert (
    broken.closed
    and panel._camera is None
    and "test delivery failure" in panel.status.text()
)
assert panel.start_button.isEnabled()
print("PASS: publisher failures stop safely and allow retry", flush=True)
print("MODE 2 VERIFIED", flush=True)
