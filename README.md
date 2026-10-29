# Deep-Live-Cam Camera11

A Windows edition of **[Deep-Live-Cam by hacksider and its contributors](https://github.com/hacksider/Deep-Live-Cam)**, maintained by [Akshit Saxena / Akshit406](https://github.com/Akshit406), with an integrated virtual camera and a mouse-controlled photo streaming mode.

**Deep-Live-Cam created the original face swap application.** This repository builds on that work and preserves its source history and AGPL license. It is an independently maintained edition. See [credits and component licenses](NOTICE.md) and the [original upstream README](docs/UPSTREAM_README.md).

## What you get

- **Mode 1 — Live face swap:** choose a source face, use your webcam, and send the processed video to Camera11.
- **Mode 2 — Photo to Camera11:** select an image from your gallery, move it by dragging, and resize it with a corner handle or the mouse wheel. Uncovered areas are black. The changes are streamed live.
- **Camera name:** `USB2.0 HD UVC WebCam (2b7e:b685)11`.
- **Output:** 1280 × 720 at 30 fps. Editor handles are excluded from the camera output.
- An independent DirectShow virtual camera adapted from OBS Studio and libdshowcapture; OBS does not need to be installed or running.

## Requirements

- Windows 10 or 11, Intel/AMD **x64**. This installer does not support Windows ARM, macOS, or Linux.
- Internet access and approximately **20 GB of free disk space** for installation, downloads, and caches. Download size depends on the selected CPU/GPU backend.
- 8 GB RAM minimum; 16 GB recommended. A physical webcam is needed for Mode 1.
- For GPU acceleration: an NVIDIA GPU and a driver reporting CUDA 12.8 support or newer. The CUDA Toolkit and Visual Studio are not needed for the prebuilt installation. Other systems use CPU mode; live face swapping will be slower.
- Windows administrator approval when registering Camera11 for all users. Python packages and the application are installed in your user directory.

## Install with one command

Open **Windows PowerShell** from the Start menu and paste:

```powershell
& ([scriptblock]::Create((Invoke-RestMethod 'https://raw.githubusercontent.com/Akshit406/Deep-Live-Cam-Camera11/v1.0.1/install.ps1')))
```

The command installs release **v1.0.1** into `%LOCALAPPDATA%\DeepLiveCamCamera11`, creates a Desktop shortcut, and opens the app. Approve the Windows prompt to register the camera. Keep the terminal open until installation finishes; large downloads can take a while.

The installer downloads a private Python 3.12.13 runtime, pinned Python packages, FFmpeg, and the model set used by this edition. It uses the bundled, source-built InsightFace wheel and Camera11 DLLs, so users do not have to compile C++ code. Bundled files and model/tool downloads are checked against SHA-256 hashes. See [the installer manifest](installer/assets.json) and [model license information](docs/MODELS.md).

**A normal browser page or browser console cannot install this system by itself.** Use the command in Windows PowerShell. A browser can download the source ZIP or installer for you; the camera registration still requires Windows approval. Performance depends on the receiving computer's hardware and driver.

To force CPU mode:

```powershell
& ([scriptblock]::Create((Invoke-RestMethod 'https://raw.githubusercontent.com/Akshit406/Deep-Live-Cam-Camera11/v1.0.1/install.ps1'))) -Acceleration Cpu
```

For a different destination:

```powershell
& ([scriptblock]::Create((Invoke-RestMethod 'https://raw.githubusercontent.com/Akshit406/Deep-Live-Cam-Camera11/v1.0.1/install.ps1'))) -InstallDir 'D:\Apps\DeepLiveCamera11'
```

Review the [installer script](install.ps1) before running it, or use the downloaded-source steps below. Rerunning the same command resumes an interrupted install in the same release directory. For a different release, use a new directory; the installer does not overwrite an existing installation from another release.

## Install from the source ZIP or a Git clone

1. Download the [v1.0.1 source ZIP](https://github.com/Akshit406/Deep-Live-Cam-Camera11/archive/refs/tags/v1.0.1.zip) and extract it to a writable folder, or clone the repository:

   ```powershell
   git clone https://github.com/Akshit406/Deep-Live-Cam-Camera11.git
   cd Deep-Live-Cam-Camera11
   ```

2. Double-click **Install.bat**, or run this from the extracted repository folder:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
   ```

3. Approve the camera registration prompt and wait for the runtime checks to pass.
4. Open **Start Deep Live Cam.bat** or the **Deep-Live-Cam Camera11** Desktop shortcut whenever you want to run it again. **Start Deep Live Cam (CPU).bat** is the CPU fallback launcher.

The app, `venv`, private `.runtime`, and bundled publisher DLLs must stay together in the install folder. Your selected photos are local files and are not packaged into the repository or uploaded by the installer. For detailed setup, verification, building, and troubleshooting, see [INSTALL.md](docs/INSTALL.md).

## Use Mode 1 — live face swap

1. Select **Mode 1 - Live face swap** at the top.
2. Click **Select a face** and choose the replacement face image.
3. Choose your physical webcam in **Camera** and click **Live**.
4. In the receiving application, choose `USB2.0 HD UVC WebCam (2b7e:b685)11` as its camera. Choose your microphone separately.
5. Keep the Live Preview open. Closing it stops the output.

You can change **Face Enhancer** in the app. GPEN-512 is the initial launcher default; GPEN-256 or None may provide better frame rates on smaller GPUs. Face swap processing can be slower than 30 fps; the virtual camera repeats the most recent processed frame.

## Use Mode 2 — stream a photo

1. Choose **Mode 2 - Photo to Camera 11**.
2. Click **Select image from gallery** and choose a photo.
3. Drag the photo to position it. Drag any corner or scroll the mouse wheel to resize it while keeping its proportions.
4. The outlined 16:9 area is the output canvas. Areas not covered by the photo are black. Parts outside the canvas are cropped. **Fit / Center image** resets the placement.
5. Click **Start streaming**, then choose the `...11` camera in the receiving app.

You can adjust or replace the image while streaming. The app can be minimized. **Stop streaming**, switching modes, or closing the app stops output; clients receive black frames. Mode 2 is a still image stream.

## Camera compatibility

Camera11 supports Windows desktop applications that accept **DirectShow** virtual cameras. Some apps require physical cameras, only use another Windows camera API, or block virtual cameras, so compatibility is not universal. Camera11 has its own software device identity.

If it is missing, close and reopen the receiving app. For an AdsPower/SunBrowser profile, stop and restart the entire browser profile before reopening its camera selector. Run **Install Camera11.bat** to repair registration. See [troubleshooting](docs/INSTALL.md#troubleshooting).

## Attribution, licenses, and model terms

- **Original application:** [hacksider/Deep-Live-Cam](https://github.com/hacksider/Deep-Live-Cam), including its contributors. The source snapshot for this edition is commit [`d759e31`](https://github.com/hacksider/Deep-Live-Cam/commit/d759e31b11d9432afdfddce698c0f7c9a715e086). The application and changes in this repository are distributed under **AGPL-3.0**; see [LICENSE](LICENSE).
- **Virtual camera:** adapted from [OBS Studio 32.0.4](https://github.com/obsproject/obs-studio/tree/32.0.4/plugins/win-dshow) and [libdshowcapture](https://github.com/obsproject/libdshowcapture). Their original license texts, source, and build instructions are retained. Details: [NOTICE.md](NOTICE.md), [virtual-camera README](virtual-camera/README.md).
- **InsightFace:** the library code is MIT licensed; the bundled wheel's original source and license notice are provided. **Pretrained InsightFace models have separate terms, including noncommercial research restrictions; the application license does not grant model rights.** Check [model terms](docs/MODELS.md) before use.
- **FFmpeg, PyTorch, Qt/PySide6, ONNX Runtime, restoration models, and other dependencies** retain their own licenses. Downloads come from the respective upstream providers; model weights and FFmpeg executables are not republished in this Git repository.

Retain attribution and the relevant licenses when redistributing. Use faces with permission and disclose altered media when sharing it. See the original project's notices in the [upstream README](docs/UPSTREAM_README.md).
