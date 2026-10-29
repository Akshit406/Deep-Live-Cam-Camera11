# Credits and third-party notices

Deep-Live-Cam Camera11 is maintained by Akshit Saxena (Akshit406). Original Deep-Live-Cam authorship belongs to hacksider and the Deep-Live-Cam contributors. The original public Git history is retained. The upstream snapshot is d759e31b11d9432afdfddce698c0f7c9a715e086.

## Application

- Upstream: https://github.com/hacksider/Deep-Live-Cam
- License: GNU Affero General Public License v3.0 (the original LICENSE is retained).
- This edition adds Camera11 publishing, Windows installation tooling and documentation, and Mode 2 photo streaming with a mouse editor. These application additions are offered under the same AGPL-3.0 terms. Changes were made in October 2026.
- Original documentation: docs/UPSTREAM_README.md. Existing source copyright and author notices remain in place.

## Virtual camera

- OBS Studio 32.0.4, https://github.com/obsproject/obs-studio/tree/32.0.4/plugins/win-dshow
- OBS source and GPL license: virtual-camera/vendor/obs/ (COPYING).
- libdshowcapture commit c13d4b7b0c66979396ba0a9060c9aafc15bb7b22, https://github.com/obsproject/libdshowcapture
- libdshowcapture source and LGPL-2.1 license: virtual-camera/vendor/libdshowcapture/ (COPYING).
- Modifications: virtual-camera/src/. Includes a new CLSID and device name, private shared-memory channel, black placeholder, standalone publisher API, registration changes, and standalone build definitions. Modified in October 2026 for this edition. Original source remains in vendor/ for comparison.
- The camera DLLs derive from these projects and retain their component license obligations. Complete corresponding source and the CMake build are in this repository; they are distributed alongside the DLLs. See virtual-camera/README.md.
- Camera11 runs independently of OBS. No affiliation or endorsement by OBS is implied.

## InsightFace Python dependency

- InsightFace Contributors, https://github.com/deepinsight/insightface
- Python library version 0.7.3, MIT license. See installer/INSIGHTFACE-LICENSE.txt.
- The Windows x64 / CPython 3.12 wheel in installer/wheels/ was built locally from the unmodified PyPI 0.7.3 source distribution, with Microsoft Visual C++ and NumPy 2.x. This wheel avoids a C++ compiler requirement on the user's computer.
- Its exact source distribution is included in installer/sources/. Original source URL and SHA-256 are documented in installer/README.md and assets.json.
- No pretrained InsightFace weights are embedded in this wheel/repository. Model rights are separate; see docs/MODELS.md.

## Downloaded components

FFmpeg: https://ffmpeg.org/ ; Windows build: https://www.gyan.dev/ffmpeg/builds/ . The installer downloads Gyan's GPLv3 essentials build and retains the archive license locally. The build and source references are documented in installer/README.md.

uv and private Python distribution: https://github.com/astral-sh/uv and https://github.com/astral-sh/python-build-standalone . uv is downloaded from its official release. Their own licenses apply.

PyTorch / torchvision: https://pytorch.org/ ; ONNX Runtime: https://github.com/microsoft/onnxruntime ; PySide6 / Qt for Python: https://doc.qt.io/qtforpython-6/ ; OpenCV: https://opencv.org/ . These packages and all transitive dependencies keep their upstream licenses and notices in the installed distributions.

Restoration and face model sources and terms are listed separately in docs/MODELS.md. The application license does not relicense any model or third-party component.
