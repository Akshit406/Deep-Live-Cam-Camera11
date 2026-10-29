"""Smoke check the installed native runtime without opening a physical webcam."""

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["KERAS_BACKEND"] = "torch"
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import run  # noqa: F401 - register native DLL search paths
import cv2
import insightface
import numpy as np
import onnxruntime as ort
import torch
from PySide6.QtWidgets import QApplication
from modules.photo_stream import PhotoStreamPanel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    assert sys.version_info[:2] == (3, 12), sys.version
    assert insightface.__version__ == "0.7.3"
    sample = np.zeros((8, 8, 3), np.uint8)
    assert cv2.cvtColor(sample, cv2.COLOR_BGR2RGB).shape == sample.shape
    assert (torch.ones(2) + 1).tolist() == [2, 2]
    if args.backend == "cuda":
        assert torch.cuda.is_available(), (
            "PyTorch could not use CUDA; check your NVIDIA driver."
        )
        assert "CUDAExecutionProvider" in ort.get_available_providers()
        assert torch.ones(2, device="cuda").sum().item() == 2
    subprocess.run(
        [str(ROOT / "ffmpeg.exe"), "-version"], check=True, stdout=subprocess.DEVNULL
    )
    app = QApplication.instance() or QApplication([])
    panel = PhotoStreamPanel()
    assert not panel.start_button.isEnabled()
    panel.close()
    app.processEvents()
    print(
        "Runtime check passed: OpenCV, InsightFace, PyTorch, ONNX Runtime, FFmpeg, and Mode 2 UI."
    )


if __name__ == "__main__":
    main()
