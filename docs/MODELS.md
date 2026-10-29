# Model downloads and terms

The installer fetches the same model set used by this edition from the original Deep-Live-Cam maintainer's Hugging Face mirror:
https://huggingface.co/hacksider/deep-live-cam/tree/581e70b61240b7928404c17900437f47cfe94133

Pinned URLs, byte sizes, and SHA-256 values are in [assets.json](../installer/assets.json). These weights are **downloaded from upstream**, not committed to this Git repository or uploaded to its GitHub Releases.

| Files | Purpose | Installed location |
| --- | --- | --- |
| inswapper_128_fp16.onnx | Face swap | models/ |
| GPEN-BFR-256.onnx and GPEN-BFR-512.onnx | Face restoration | models/ |
| gfpgan-1024.onnx | Face restoration | models/ |
| buffalo_l: 1k3d68, 2d106det, det_10g, genderage, w600k_r50 | Face detection, recognition, landmarks | %USERPROFILE%\.insightface\models\buffalo_l\ |

## Model rights differ from code rights

InsightFace's MIT library license does not cover its pretrained models. InsightFace states that its training data and models trained on that data are available for **noncommercial research purposes only**, including auto-downloaded models. For inswapper and buffalo_l licensing, follow the contacts and terms in the [official InsightFace license section](https://github.com/deepinsight/insightface#license) and [InsightFace website](https://www.insightface.ai/).

GPEN source/terms: https://github.com/yangxy/GPEN . GFPGAN source/terms: https://github.com/TencentARC/GFPGAN . ONNX conversion reference: https://github.com/harisreedhar/Face-Upscalers-ONNX . Check each applicable model's original terms; a mirror's metadata does not replace the original rights holder's terms.

The AGPL license on the application does not grant commercial model permissions. Obtain any permissions needed for your use. Mode 2 streams a photo without face model inference; the default full installation downloads the model set so Mode 1 and the enhancer choices are ready.

To defer model downloads:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -SkipModels
```

Mode 1 can then download missing models when needed. For the same pinned set with checksum checks, run the installer again without -SkipModels. Normal upstream first-run downloads may use upstream's current mirror revision; the installer is the reproducible, pinned route.
