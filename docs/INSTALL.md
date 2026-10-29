# Install, run, and troubleshoot

## Supported setup

The installer targets Windows 10/11 x64 with CPython 3.12.13. Camera11 is a DirectShow virtual camera. CPU and NVIDIA CUDA backends are supported by this installer. A complete install was checked in a fresh private Python environment on the maintainer's Windows/NVIDIA computer; a new physical machine or clean OS installation has not been tested locally. GitHub Actions also exercises a CPU installation and source builds. It does not reproduce the maintainer's hardware, graphics driver, personal files, browser profile, or operating system.

Use [the README one-command install](../README.md#install-with-one-command), or extract/clone the repository and run Install.bat. No preinstalled Python, pip, Git, Visual Studio, CUDA Toolkit, or OBS is needed for the ZIP/one-command path. Models and large dependencies need internet access.

## Installer options

From a downloaded source folder:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Acceleration Auto
```

| Option | Effect |
| --- | --- |
| `-Acceleration Auto` | Choose CUDA when nvidia-smi reports CUDA 12.8+ support; otherwise choose CPU. |
| `-Acceleration Cpu` | Install CPU PyTorch and ONNX Runtime. |
| `-Acceleration Cuda` | Require a compatible NVIDIA driver; fail with an explanation when unavailable. |
| `-InstallDir 'D:\Apps\Camera11'` | Download the tagged source into a new folder and install there. |
| `-SkipModels` | Defer model downloads; normal app startup/Mode 1 can fetch missing models later. |
| `-SkipCamera` | Install the app without registering the Windows virtual camera. |
| `-SkipLaunch` | Finish setup without opening the app. |
| `-SkipShortcut` | Avoid creating or changing the Desktop shortcut (useful for CI). |
| `-Plan` | Print the installation plan without downloading or installing anything. |

The source ZIP is pinned to v1.0.0. The private Python interpreter is installed under .runtime/; the environment is venv/. uv and downloads live under .installer/. A small installer-state.json records the selected backend and completion status. These files are ignored by Git.

Downloads use HTTPS and SHA-256 checks from installer/assets.json. Existing verified models are reused; corrupt/incomplete downloads are replaced only after a verified download succeeds. Re-run the installer to resume after a network failure. Keep the install directory writable and avoid Program Files for the application itself.

The camera registration helper asks for administrator approval, copies the x64/x86 filter DLLs to Program Files\DeepLiveCamera11, and registers the device. If matching DLLs are already registered, setup reuses them. It does not install a kernel driver. The app needs the publisher DLL in its own virtual-camera/bin/ directory after registration.

## Start and use

Open Start Deep Live Cam.bat or the Desktop shortcut. Start Deep Live Cam (CPU).bat is a slower fallback. The initial launcher selects face_swapper and GPEN-512. Existing saved enhancer choices are loaded by the UI; you can choose GPEN-256 or None for better live speed.

For Mode 1, choose a source face and physical webcam, then Live. Select Camera11 in the receiving app and leave the Live Preview open.

For Mode 2, select a gallery photo, drag it to move, drag a corner or use the wheel to resize, and click Start streaming. The 16:9 canvas matches the streamed composition. Empty space is black; outside edges are cropped. Fit / Center image resets the photo. Replacing a photo starts with a centered fit.

Changes in Mode 2 are sent while streaming. Keep the main app open; minimizing is fine. Stopping the stream, changing modes, or closing the app releases the publisher. Select the microphone separately in the receiving app.

## Verify an installation

From the installed folder:

```powershell
.\venv\Scripts\python.exe installer\check_install.py --backend cpu
```

For a CUDA installation use `--backend cuda`. This checks native imports, a small tensor calculation, FFmpeg, and the photo panel without opening a physical webcam.

With Camera11 registered and all other publishers stopped, run:

```powershell
.\venv\Scripts\python.exe tests\windows\test_virtual_camera.py
.\venv\Scripts\python.exe tests\windows\test_camera_integration.py
.\venv\Scripts\python.exe tests\windows\test_photo_stream.py
.\venv\Scripts\python.exe tests\windows\test_photo_mouse.py
```

These tests use generated images and a separate FFmpeg camera client. They cover actual output colors, black background, mouse placement/size, switching images/modes, duplicate publisher handling, and cleanup. They do not capture a physical webcam.

For a source rebuild of the camera or InsightFace wheel, see [virtual-camera/README.md](../virtual-camera/README.md) and [installer/README.md](../installer/README.md).

## Troubleshooting

**Camera11 is missing:** close receiving apps, run Install Camera11.bat, approve the Windows prompt, and reopen the receiving app. For SunBrowser, stop/reopen its entire AdsPower profile. Check virtual-camera/system-install-status.json. Apps that reject software cameras or do not accept DirectShow may remain incompatible.

**Black image:** start Live in Mode 1 or Start streaming in Mode 2, and select the `...11` camera in the receiving app. Black is the intentional output when no publisher is running.

**Camera11 is already active:** stop the stream in the other app instance or preview. There is one publisher per camera. OBS Virtual Camera is a separate device and does not need to run.

**CUDA startup fails:** update the NVIDIA driver or rerun install.ps1 with -Acceleration Cpu. Do not mix CPU and CUDA ONNX Runtime packages in one environment. If you previously installed the other backend in the same folder, install this release into a new directory for a clean backend switch.

**A DLL import fails on a minimal Windows installation:** install the Microsoft Visual C++ v14 x64 Redistributable from https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist . uv's private Python and PySide6/PyTorch include runtime components, but system configurations can differ. Restart and rerun the check.

**Download or checksum failure:** check network/disk space and rerun the installer. A checksum failure stops setup; do not replace the expected hash just to bypass it. The maintainer should update a release manifest only after verifying an upstream change.

**Slow Mode 1:** reduce/disable the face enhancer, improve lighting, or use supported NVIDIA hardware. A 30 fps virtual stream repeats the last processed frame when processing is slower. Mode 2 requires much less processing.

**Only a source face changes, not hair:** Mode 1 swaps the detected face area. Mode 2 streams the whole selected image and is a still photo mode.

## Uninstall

1. Stop streaming and close the app and camera consumers.
2. Run Uninstall Camera11.bat and approve the Windows prompt to remove this device's registration.
3. Remove the application install folder and its Desktop shortcut when no longer needed.
4. Model files in %USERPROFILE%\.insightface\models\buffalo_l may be shared with other InsightFace apps; remove them only if you no longer need them.

No global Python installation or graphics driver is removed. This uninstall does not remove other cameras or OBS. Program Files\DeepLiveCamera11 may retain unregistered DLLs; after unregistering and closing consumers, that directory can be removed manually.
