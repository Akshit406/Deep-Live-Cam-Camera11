# Camera11 source and build

The friendly name is `USB2.0 HD UVC WebCam (2b7e:b685)11`. The CLSID and channel configuration are in camera.json. This is a Windows DirectShow software camera with its own identity.

The filter adapts OBS Studio 32.0.4 virtual-camera code and libdshowcapture commit c13d4b7b0c66979396ba0a9060c9aafc15bb7b22. Original copies and licenses are in vendor/; changes and the standalone publisher are in src/. See ../NOTICE.md and upstream.json. These files and build scripts provide the corresponding source for bin/deeplive-camera11-{x64,x86}.dll.

## Build from source

1. Install Visual Studio 2022 Build Tools or Visual Studio 2022 with the C++ desktop workload, Windows SDK, and CMake tools. A CMake version of at least 3.28 is needed.
2. From the repository root, run:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\virtual-camera\build.ps1
   ```

3. The script builds both x64 and x86 and copies the Release DLLs into virtual-camera/bin/.
4. Run Install Camera11.bat and approve Windows elevation to register both architectures. Close camera consumers before updating DLLs.
5. If publishing rebuilt DLLs, update their SHA-256 entries in installer/assets.json and distribute the exact corresponding source.

Regular users can use the included DLLs; Build Tools are needed only for rebuilding. The system installer copies the filters to `%ProgramFiles%\DeepLiveCamera11` and registers them in the corresponding 32/64-bit DirectShow registries. The app publishes using its own DLL copy in bin/; keep that folder with the app.

The publisher repeats the most recent frame at 30 fps and outputs black after it stops. It does not need OBS. Some clients block virtual cameras or do not accept DirectShow sources.

## Verify without using a real webcam

```powershell
.\venv\Scripts\python.exe tests\windows\test_virtual_camera.py
.\venv\Scripts\python.exe tests\windows\test_camera_integration.py
.\venv\Scripts\python.exe tests\windows\test_photo_stream.py
.\venv\Scripts\python.exe tests\windows\test_photo_mouse.py
```

These checks use generated color images and a separate FFmpeg camera client. Register Camera11 first and stop any running publisher before testing. They do not record a physical webcam.
