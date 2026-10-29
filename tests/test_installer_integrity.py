"""Verify installer download integrity without touching installed runtimes."""

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import io

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "camera11_setup", ROOT / "installer/setup_windows.py"
)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class DownloadIntegrityTests(unittest.TestCase):
    def test_corrupt_response_does_not_replace_existing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "asset.bin"
            path.write_bytes(b"existing original")
            expected = hashlib.sha256(b"expected download").hexdigest()
            with patch.object(
                setup.urllib.request,
                "urlopen",
                return_value=io.BytesIO(b"corrupt response"),
            ):
                with self.assertRaisesRegex(RuntimeError, "Checksum mismatch"):
                    setup.download("https://example.invalid/model", path, expected)
            self.assertEqual(path.read_bytes(), b"existing original")

    def test_verified_response_replaces_corrupt_file(self):
        content = b"verified asset"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "asset.bin"
            path.write_bytes(b"corrupt file")
            with patch.object(
                setup.urllib.request, "urlopen", return_value=io.BytesIO(content)
            ):
                setup.download(
                    "https://example.invalid/model",
                    path,
                    hashlib.sha256(content).hexdigest(),
                )
            self.assertEqual(path.read_bytes(), content)
            self.assertFalse(path.with_name("asset.bin.part").exists())

    def test_existing_verified_file_does_not_need_network(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "asset.bin"
            path.write_bytes(b"cached verified asset")
            with patch.object(
                setup.urllib.request,
                "urlopen",
                side_effect=AssertionError("unnecessary download"),
            ):
                setup.download(
                    "https://example.invalid/model", path, setup.sha256(path)
                )

    def test_distributed_native_files_match_manifest(self):
        setup.verify_bundled_files()


if __name__ == "__main__":
    unittest.main()
