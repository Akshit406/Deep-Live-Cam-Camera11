"""Exercise real mouse gestures and verify Camera11 receives the edited canvas."""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["KERAS_BACKEND"] = "torch"
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
import run  # noqa: F401 - register bundled native DLL directories
import numpy as np
from PIL import Image
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QFontDatabase, QFont, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from modules import ui

app = QApplication([])
QFontDatabase.addApplicationFont("C:/Windows/Fonts/segoeui.ttf")
app.setFont(QFont("Segoe UI", 10))
app.setStyleSheet(ui.QSS)
ui.get_available_cameras = lambda: ([], ["No cameras found"])
window = ui.MainWindow(lambda: None, lambda: None)
window.show()
window.mode_selector.setCurrentIndex(1)
app.processEvents()
panel = window.photo_panel
canvas = panel.preview


def drag(start, end):
    for kind, pos, button, buttons in [
        (
            QMouseEvent.Type.MouseButtonPress,
            start,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
        ),
        (
            QMouseEvent.Type.MouseMove,
            end,
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
        ),
        (
            QMouseEvent.Type.MouseButtonRelease,
            end,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
        ),
    ]:
        event = QMouseEvent(
            kind, pos, pos, button, buttons, Qt.KeyboardModifier.NoModifier
        )
        QApplication.sendEvent(canvas, event)
    QTest.qWait(150)


def wheel(steps):
    pos = canvas._screen_rect().center()
    event = QWheelEvent(
        pos,
        pos,
        QPoint(),
        QPoint(0, steps * 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QApplication.sendEvent(canvas, event)
    QTest.qWait(150)


def read_camera():
    identifier = (
        "@device_sw_{860BB310-5D01-11D0-BD3B-00A0C911CE86}"
        + chr(92)
        + json.loads((root / "virtual-camera/camera.json").read_text())["clsid"]
    )
    r = subprocess.run(
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
    assert r.returncode == 0, r.stderr.decode(errors="replace")
    return np.frombuffer(r.stdout, np.uint8).reshape(4, 720, 1280, 3)[-1]


with tempfile.TemporaryDirectory() as directory:
    photo = Path(directory) / "mouse-edit-test.png"
    Image.new("RGB", (1280, 720), (255, 0, 0)).save(photo)
    try:
        assert panel.load_image(str(photo))
        panel.start_stream()
        assert panel._camera is not None, panel.status.text()
        rect = canvas._screen_rect()
        drag(rect.bottomRight(), rect.center())
        frame = canvas.frame_bgr()
        assert abs(canvas._rect.width() - 640) < 2
        assert abs(canvas._rect.height() - 360) < 2
        assert frame[100, 100, 2] == 255 and frame[500, 800].max() == 0
        center = canvas._screen_rect().center()
        scale = canvas.viewport_rect().width() / 1280
        drag(center, center + QPointF(320 * scale, 180 * scale))
        assert abs(canvas._rect.x() - 320) < 2 and abs(canvas._rect.y() - 180) < 2
        received = read_camera()
        assert received[360, 640, 2] > 240
        assert received[0:170].max() < 5 and received[:, 0:300].max() < 5
        assert received[550:].max() < 5 and received[:, 970:].max() < 5
        print(
            "Chroma edge maxima:",
            int(received[:, :, 0].max()),
            int(received[:, :, 1].max()),
            flush=True,
        )
        assert received[:, :, 0].max() < 25 and received[:, :, 1].max() < 25
        print(
            "PASS: mouse corner resize and drag position reach Camera11 with black background; no editor handles in stream",
            flush=True,
        )
        before = canvas._rect.width()
        wheel(-3)
        assert canvas._rect.width() < before
        wheel(3)
        assert abs(canvas._rect.width() - before) < 0.01
        # Output must not change when the application window is resized.
        original = canvas.frame_bgr().copy()
        window.resize(900, 1000)
        app.processEvents()
        assert np.array_equal(canvas.frame_bgr(), original)
        print(
            "PASS: wheel resizing preserves proportions and window resizing leaves output unchanged",
            flush=True,
        )
        window.resize(640, 820)
        app.processEvents()
        window.grab().save(str(root / "virtual-camera/mode2-resize-preview.png"))
        panel.reset_button.click()
        QTest.qWait(150)
        assert canvas.frame_bgr()[:, :, 2].min() == 255
        received = read_camera()
        print(
            "Reset stream red mean:",
            float(received[:, :, 2].mean()),
            "timer:",
            panel._edit_timer.isActive(),
            flush=True,
        )
        assert received[:, :, 2].mean() > 240
        # All four corners preserve their opposite anchor and aspect ratio.
        for index in range(4):
            canvas.reset_fit()
            corners = canvas._corners()
            opposite = corners[(index + 2) % 4]
            drag(corners[index], (corners[index] + canvas._screen_rect().center()) / 2)
            actual = canvas._corners()[(index + 2) % 4]
            assert (
                abs(actual.x() - opposite.x()) < 1
                and abs(actual.y() - opposite.y()) < 1
            )
            assert abs(canvas._rect.width() / canvas._rect.height() - 16 / 9) < 1e-6
        # Panning past the edge clips safely and can be recovered with reset.
        center = canvas._screen_rect().center()
        drag(center, center + QPointF(-1000, -1000))
        assert canvas._rect.right() > 0 and canvas._rect.bottom() > 0
        assert canvas.frame_bgr().shape == (720, 1280, 3)
        panel.reset_button.click()
        panel.stop_stream()
        assert not panel._edit_timer.isActive()
        assert read_camera().max() < 5
        print(
            "PASS: Fit / Center, every corner handle, edge clipping, and Stop cleanup",
            flush=True,
        )
    finally:
        panel.stop_stream()
        window.close()
print("MOUSE PHOTO EDITOR VERIFIED", flush=True)
