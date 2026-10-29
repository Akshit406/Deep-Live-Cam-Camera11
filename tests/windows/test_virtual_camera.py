from pathlib import Path
import sys, subprocess, json, time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np
from modules.virtual_camera import VirtualCamera

root = Path(__file__).resolve().parents[2]


def read_camera():
    command = [
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
        "video=@device_sw_{860BB310-5D01-11D0-BD3B-00A0C911CE86}"
        + chr(92)
        + json.loads((root / "virtual-camera/camera.json").read_text())["clsid"],
        "-frames:v",
        "3",
        "-pix_fmt",
        "bgr24",
        "-f",
        "rawvideo",
        "pipe:1",
    ]
    result = subprocess.run(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace"))
    assert len(result.stdout) == 1280 * 720 * 3 * 3, (len(result.stdout), result.stderr)
    return np.frombuffer(result.stdout, np.uint8).reshape(3, 720, 1280, 3)[-1]


with VirtualCamera() as camera:
    src = np.zeros((720, 1280, 3), np.uint8)
    src[:, :640] = [255, 0, 0]
    src[:, 640:] = [0, 255, 0]
    camera.send(src)
    time.sleep(0.2)
    result = read_camera()
    left = result[200:500, 100:500].mean(axis=(0, 1))
    right = result[200:500, 800:1100].mean(axis=(0, 1))
    print("Received BGR test colors:", left.tolist(), right.tolist(), flush=True)
    assert left[0] > 240 and left[1] < 15 and left[2] < 15
    assert right[1] > 240 and right[0] < 15 and right[2] < 15
    try:
        second = VirtualCamera()
    except RuntimeError:
        print("Duplicate producer rejected correctly", flush=True)
    else:
        second.close()
        raise AssertionError("Duplicate producer was allowed")
time.sleep(0.5)
black = read_camera()
assert black.max() < 5, (int(black.min()), int(black.max()))
print("Stopped camera outputs black, not stale video", flush=True)
with VirtualCamera() as camera:
    camera.send(np.full((480, 640, 3), 255, np.uint8))
    result = read_camera()
    assert result[:, 0:100].max() < 5
    assert result[:, 300:900].mean() > 245
print("Restart and aspect-ratio preservation passed", flush=True)
print("STANDALONE CAMERA VERIFIED", flush=True)
