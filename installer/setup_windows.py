"""Install the pinned Windows runtime and verified upstream model assets."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "installer/assets.json").read_text(encoding="utf-8"))


def sha256(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def download(url, destination, expected):
    destination = Path(destination)
    if destination.is_file() and sha256(destination) == expected:
        print(f"Verified: {destination.name}", flush=True)
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + ".part")
    request = urllib.request.Request(
        url, headers={"User-Agent": "Deep-Live-Cam-Camera11/1.0"}
    )
    print(f"Downloading: {destination.name}", flush=True)
    with (
        urllib.request.urlopen(request, timeout=120) as response,
        partial.open("wb") as handle,
    ):
        shutil.copyfileobj(response, handle, 1024 * 1024)
    if sha256(partial) != expected:
        raise RuntimeError(
            f"Checksum mismatch: {destination.name}. The download was not installed."
        )
    partial.replace(destination)
    return destination


def verify_bundled_files():
    for name, expected in MANIFEST["files"].items():
        path = ROOT / name
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(
                f"Bundled file is missing or modified: {name}. Download a clean release."
            )


def run(command):
    print(
        "Running:", subprocess.list2cmdline([str(part) for part in command]), flush=True
    )
    subprocess.run([str(part) for part in command], cwd=ROOT, check=True)


def cuda_available():
    executable = shutil.which("nvidia-smi")
    if executable is None:
        executable = str(
            Path(os.environ.get("WINDIR", "C:/Windows")) / "System32/nvidia-smi.exe"
        )
    try:
        result = subprocess.run(
            [executable], capture_output=True, text=True, timeout=20
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    version = re.search(r"CUDA Version:\s*(\d+)\.(\d+)", result.stdout)
    return (
        result.returncode == 0
        and version is not None
        and tuple(map(int, version.groups())) >= (12, 8)
    )


def install_packages(uv, backend):
    pip = [
        uv,
        "pip",
        "install",
        "--python",
        sys.executable,
        "--no-deps",
        "--only-binary",
        ":all:",
    ]
    run([*pip, "-r", ROOT / "installer/requirements-windows.txt"])
    run([*pip, "-r", ROOT / f"installer/requirements-{backend}.txt"])
    runtime = "onnxruntime-gpu" if backend == "cuda" else "onnxruntime"
    run([*pip, f"{runtime}==1.26.0"])
    wheel = next(ROOT.glob("installer/wheels/insightface-*.whl"))
    run([*pip, wheel])
    run([uv, "pip", "check", "--python", sys.executable])


def install_ffmpeg():
    info = MANIFEST["ffmpeg"]
    archive = download(
        info["url"], ROOT / ".installer/downloads/ffmpeg.zip", info["sha256"]
    )
    with zipfile.ZipFile(archive) as source:
        for executable in ["ffmpeg.exe", "ffprobe.exe"]:
            members = [
                name
                for name in source.namelist()
                if name.endswith("/bin/" + executable)
            ]
            if len(members) != 1:
                raise RuntimeError("Unexpected FFmpeg archive layout")
            with source.open(members[0]) as src, (ROOT / executable).open("wb") as dest:
                shutil.copyfileobj(src, dest)
        license_files = [
            name
            for name in source.namelist()
            if Path(name).name in ("LICENSE", "LICENSE.txt")
        ]
        if license_files:
            (ROOT / "ffmpeg-LICENSE.txt").write_bytes(source.read(license_files[0]))


def model_destination(info):
    if info["destination"] == "insightface":
        return Path.home() / ".insightface/models/buffalo_l" / Path(info["name"]).name
    return ROOT / "models" / info["name"]


def install_models():
    print(
        "Downloading the upstream model set; see docs/MODELS.md for its separate license terms.",
        flush=True,
    )
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(download, item["url"], model_destination(item), item["sha256"])
            for item in MANIFEST["models"]
        ]
        for future in futures:
            future.result()


def camera_installed():
    try:
        import ctypes

        config = json.loads((ROOT / "virtual-camera/camera.json").read_text())
        import winreg

        for arch, view in [
            ("x64", winreg.KEY_WOW64_64KEY),
            ("x86", winreg.KEY_WOW64_32KEY),
        ]:
            base = "SOFTWARE\\Classes\\CLSID\\" + config["clsid"] + "\\InprocServer32"
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE, base, 0, winreg.KEY_READ | view
            ) as key:
                dll = Path(winreg.QueryValueEx(key, "")[0])
            if (
                sha256(dll)
                != MANIFEST["files"][f"virtual-camera/bin/deeplive-camera11-{arch}.dll"]
            ):
                return False
        # Load only our checksummed publisher DLL; registration remains in Windows.
        ctypes.CDLL(str(ROOT / "virtual-camera/bin/deeplive-camera11-x64.dll"))
        return True
    except (OSError, KeyError):
        return False


def install_camera():
    if camera_installed():
        print(
            "Camera11 is already registered with the matching release DLLs.", flush=True
        )
        return
    run([sys.executable, ROOT / "virtual-camera/request-install.py", "--wait"])
    if not camera_installed():
        raise RuntimeError(
            "Camera registration did not complete. Run Install Camera11.bat and approve the Windows prompt."
        )


def write_launchers(backend):
    common = '@echo off\ncd /d "%~dp0"\nset "KERAS_BACKEND=torch"\n'
    for name, provider in [
        ("Start Deep Live Cam.bat", backend),
        ("Start Deep Live Cam (CPU).bat", "cpu"),
    ]:
        text = (
            common
            + f'"%~dp0venv\\Scripts\\python.exe" run.py --frame-processor face_swapper face_enhancer_gpen512 --execution-provider {provider}\nif errorlevel 1 pause\n'
        )
        (ROOT / name).write_text(text, encoding="ascii")
    # Use the shell's Desktop known folder, including redirected/OneDrive desktops.
    command = "$s=New-Object -ComObject WScript.Shell; $p=$s.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Deep-Live-Cam Camera11.lnk')); $p.TargetPath=$env:CAMERA11_LAUNCHER; $p.WorkingDirectory=$env:CAMERA11_ROOT; $p.Save()"
    environment = dict(
        os.environ,
        CAMERA11_LAUNCHER=str(ROOT / "Start Deep Live Cam.bat"),
        CAMERA11_ROOT=str(ROOT),
    )
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        env=environment,
        check=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uv")
    parser.add_argument(
        "--acceleration", choices=["auto", "cpu", "cuda"], default="auto"
    )
    parser.add_argument("--skip-camera", action="store_true")
    parser.add_argument("--skip-models", action="store_true")
    parser.add_argument("--skip-launch", action="store_true")
    parser.add_argument("--skip-shortcut", action="store_true")
    parser.add_argument(
        "--assets-only",
        action="store_true",
        help="Download/verify assets without modifying the Python environment or camera registration",
    )
    args = parser.parse_args()
    if sys.platform != "win32" or sys.maxsize <= 2**32:
        parser.error("Windows x64 and 64-bit Python are required")
    verify_bundled_files()
    if args.assets_only:
        install_ffmpeg()
        if not args.skip_models:
            install_models()
        return
    if not args.uv:
        parser.error("--uv is required (normally supplied by install.ps1)")
    available = cuda_available()
    backend = (
        ("cuda" if available else "cpu")
        if args.acceleration == "auto"
        else args.acceleration
    )
    if backend == "cuda" and not available:
        parser.error(
            "CUDA 12.8 support was not detected. Update the NVIDIA driver or use -Acceleration Cpu."
        )
    print(
        f"Installing Camera11 with {backend.upper()} acceleration in {ROOT}", flush=True
    )
    install_packages(args.uv, backend)
    install_ffmpeg()
    if not args.skip_models:
        install_models()
    run([sys.executable, ROOT / "installer/check_install.py", "--backend", backend])
    if not args.skip_camera:
        install_camera()
    if not args.skip_shortcut:
        write_launchers(backend)
    else:
        # CI still needs a matching default launcher.
        launcher = ROOT / "Start Deep Live Cam.bat"
        launcher.write_text(
            (ROOT / "Start Deep Live Cam (CPU).bat")
            .read_text()
            .replace("--execution-provider cpu", f"--execution-provider {backend}"),
            encoding="ascii",
        )
    state = {
        "release": MANIFEST["release"],
        "backend": backend,
        "models_downloaded": not args.skip_models,
        "camera_registered": camera_installed(),
        "python": sys.version.split()[0],
    }
    (ROOT / "installer-state.json").write_text(json.dumps(state, indent=2) + "\n")
    print(
        "Installation complete. Start Deep Live Cam.bat launches the app. Select Mode 2 for gallery photo streaming.",
        flush=True,
    )
    if not args.skip_launch:
        environment = dict(os.environ, KERAS_BACKEND="torch")
        subprocess.Popen(
            [
                sys.executable,
                "run.py",
                "--frame-processor",
                "face_swapper",
                "face_enhancer_gpen512",
                "--execution-provider",
                backend,
            ],
            cwd=ROOT,
            env=environment,
        )


if __name__ == "__main__":
    main()
