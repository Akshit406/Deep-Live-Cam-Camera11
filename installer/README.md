# Installer internals and provenance

The supported entry point is ../install.ps1. See ../README.md for user instructions.

- uv 0.13.6 from astral-sh/uv official GitHub Releases; archive SHA-256 is pinned in assets.json.
- Private CPython 3.12.13 managed by uv/python-build-standalone, stored in .runtime/. Global Python and PATH are not replaced.
- requirements-windows.txt pins the complete shared dependency set from the working installation. CPU/CUDA PyTorch requirements are separate. setup_windows.py installs wheels and then runs uv pip check.
- CUDA: PyTorch 2.11.0+cu128, torchvision 0.26.0+cu128, onnxruntime-gpu 1.26.0. CPU: PyTorch 2.11.0+cpu, torchvision 0.26.0+cpu, onnxruntime 1.26.0.
- Auto selects CUDA only when nvidia-smi reports CUDA 12.8+ support. The installer does not change the graphics driver.
- InsightFace: locally built insightface-0.7.3-cp312-cp312-win_amd64.whl; SHA-256 ae5e7e69a5aa10805142092372fa4910294680d58b344b86fbab8822c0038b70. Built from unmodified source with the Visual Studio 2022 C++ compiler and NumPy 2.x. See INSIGHTFACE-LICENSE.txt.
- Included corresponding source: sources/insightface-0.7.3.tar.gz. Original URL: https://files.pythonhosted.org/packages/0b/8d/0f4af90999ca96cf8cb846eb5ae27c5ef5b390f9c090dd19e4fa76364c13/insightface-0.7.3.tar.gz . SHA-256 f191f719612ebb37018f41936814500544cd0f86e6fcd676c023f354c668ddf7.
- To rebuild the InsightFace wheel, extract that source, open an x64 Native Tools command prompt with MSVC installed, use Python 3.12 with setuptools, wheel, Cython and NumPy 2.x, and run `python -m pip wheel --no-deps --no-build-isolation .`. Retain the included source and license when redistributing.
- FFmpeg 9.0.2 essentials from https://github.com/GyanD/codexffmpeg/releases/tag/9.0.2 ; SHA-256 60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba. Build information/source: https://www.gyan.dev/ffmpeg/builds/ and https://github.com/FFmpeg/FFmpeg/commit/946fcce07b . The ZIP and its license are kept on the user's system; executables are downloaded, not included in Git.
- Camera11 x64/x86 DLL hashes and upstream model hashes are in assets.json. Complete camera source is in ../virtual-camera/.

Installation is resumable: existing files are verified before reuse. Failed downloads are not installed. It does not copy the maintainer's venv, caches, photos, credentials, or Windows settings. It recreates the supported application features and dependency versions; hardware/OS/driver behavior can differ.
