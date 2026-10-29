# Contributing to Camera11

This is Akshit406's independently maintained Windows edition of hacksider/Deep-Live-Cam. Keep original authorship, copyright notices, and component licenses. Send issues and pull requests for this edition to this repository; upstream Deep-Live-Cam issues belong in its own project.

Use a feature branch, keep model weights and personal media out of Git, and include relevant verification results. Application changes use the repository's AGPL-3.0 license; vendored camera sources retain their own licenses.

Before publishing changes:

```powershell
uvx --from ruff==0.15.7 ruff check
.\venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'
```

For changes to the virtual camera or Mode 2, also run the generated-image integration checks listed in virtual-camera/README.md with Camera11 registered and other publishers stopped. For changes to live face processing, check physical webcam use, face enhancement, and map-faces behavior as appropriate. Do not claim physical hardware tests when using stubs.

If rebuilding camera DLLs or the InsightFace wheel, include the corresponding source and update installer/assets.json hashes. Preserve the pinned release install path and document changes to package/model versions. GitHub Actions checks lint, unit tests, and a CPU installation/runtime check on Windows.
