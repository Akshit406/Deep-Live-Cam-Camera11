"""Publish processed frames to the independent Camera11 DirectShow device."""

from __future__ import annotations
import ctypes
import platform
import threading
import time
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent / "virtual-camera"
CAMERA_NAME = "USB2.0 HD UVC WebCam (2b7e:b685)11"


class VirtualCamera:
    def __init__(self, width=1280, height=720, fps=30):
        if platform.system() != "Windows":
            raise RuntimeError("Camera11 requires Windows")
        if width % 2 or height % 2 or min(width, height, fps) <= 0:
            raise ValueError("Camera dimensions must be positive and even")
        self.width, self.height, self.fps = width, height, fps
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._frame = None
        self._error = None
        self._handle = None
        self._thread = None
        arch = "x64" if ctypes.sizeof(ctypes.c_void_p) == 8 else "x86"
        dll = ROOT / "bin" / f"deeplive-camera11-{arch}.dll"
        if not dll.exists():
            raise RuntimeError("Camera11 is not installed; run Install Camera11.bat")
        self._dll = ctypes.CDLL(str(dll))
        self._dll.dlc_create.argtypes = [ctypes.c_uint32] * 3
        self._dll.dlc_create.restype = ctypes.c_void_p
        self._dll.dlc_write.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_uint64,
        ]
        self._dll.dlc_write.restype = ctypes.c_int
        self._dll.dlc_close.argtypes = [ctypes.c_void_p]
        self._dll.dlc_close.restype = None
        self._handle = self._dll.dlc_create(width, height, fps)
        if not self._handle:
            raise RuntimeError(
                "Camera11 is already active in another preview, or could not start"
            )
        self.send(np.zeros((height, width, 3), dtype=np.uint8))
        self._thread = threading.Thread(
            target=self._run, name="Camera11 output", daemon=True
        )
        self._thread.start()

    def send(self, bgr_frame):
        if self._stop.is_set():
            if self._error:
                raise RuntimeError(self._error)
            return
        if (
            bgr_frame.dtype != np.uint8
            or bgr_frame.ndim != 3
            or bgr_frame.shape[2] != 3
        ):
            raise ValueError("Expected uint8 BGR image")
        h, w = bgr_frame.shape[:2]
        if h <= 0 or w <= 0:
            raise ValueError("Empty camera frame")
        if (w, h) != (self.width, self.height):
            scale = min(self.width / w, self.height / h)
            nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
            resized = cv2.resize(
                bgr_frame,
                (nw, nh),
                interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC,
            )
            canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            x, y = (self.width - nw) // 2, (self.height - nh) // 2
            canvas[y : y + nh, x : x + nw] = resized
        else:
            canvas = np.ascontiguousarray(bgr_frame)
        i420 = cv2.cvtColor(canvas, cv2.COLOR_BGR2YUV_I420).reshape(-1)
        n = self.width * self.height
        nv12 = np.empty(n * 3 // 2, dtype=np.uint8)
        nv12[:n] = i420[:n]
        nv12[n::2] = i420[n : n + n // 4]
        nv12[n + 1 :: 2] = i420[n + n // 4 :]
        with self._lock:
            self._frame = nv12

    def _run(self):
        period = 1 / self.fps
        deadline = time.perf_counter()
        try:
            while not self._stop.is_set():
                with self._lock:
                    frame = self._frame
                if frame is not None:
                    if not self._dll.dlc_write(
                        self._handle,
                        frame.ctypes.data,
                        frame.nbytes,
                        time.perf_counter_ns() // 100,
                    ):
                        raise RuntimeError("Camera11 frame delivery failed")
                deadline += period
                now = time.perf_counter()
                if deadline < now:
                    deadline = now
                self._stop.wait(max(0, deadline - now))
        except Exception as exc:
            self._error = str(exc)
            self._stop.set()

    @property
    def error(self):
        """Report asynchronous publisher failures to the UI."""
        return self._error

    def close(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        if self._handle:
            self._dll.dlc_close(self._handle)
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
