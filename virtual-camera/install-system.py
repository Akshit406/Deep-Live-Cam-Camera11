"""Standard system registration for the Camera11 DirectShow filter."""

from pathlib import Path
import ctypes, json, os, shutil, subprocess, sys, winreg

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import install as account_installer

CONFIG = json.loads((ROOT / "camera.json").read_text())
CLSID = CONFIG["clsid"]
assert CLSID == "{B0EE4310-2E61-4821-84B1-771F7300FF4C}"
CATEGORY = "{860BB310-5D01-11D0-BD3B-00A0C911CE86}"
DEST = Path(os.environ["ProgramFiles"]) / "DeepLiveCamera11"
STATUS = ROOT / "system-install-status.json"


def register(arch, uninstall=False):
    directory = "System32" if arch == "x64" else "SysWOW64"
    dll = DEST / f"deeplive-camera11-{arch}.dll"
    command = [str(Path(os.environ["WINDIR"]) / directory / "regsvr32.exe"), "/s"]
    if uninstall:
        command.append("/u")
    command.append(str(dll))
    result = subprocess.run(command, timeout=30)
    if result.returncode:
        raise RuntimeError(f"{arch} camera registration returned {result.returncode}")


def verify():
    for arch, view in [
        ("x64", winreg.KEY_WOW64_64KEY),
        ("x86", winreg.KEY_WOW64_32KEY),
    ]:
        base = "SOFTWARE\\Classes\\CLSID\\" + CLSID + "\\InprocServer32"
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, base, 0, winreg.KEY_READ | view
        ) as key:
            dll = Path(winreg.QueryValueEx(key, "")[0])
            assert dll == DEST / f"deeplive-camera11-{arch}.dll", dll
        instance = "SOFTWARE\\Classes\\CLSID\\" + CATEGORY + "\\Instance\\" + CLSID
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, instance, 0, winreg.KEY_READ | view
        ) as key:
            assert winreg.QueryValueEx(key, "FriendlyName")[0] == CONFIG["name"]
            assert len(winreg.QueryValueEx(key, "FilterData")[0]) > 0


def main():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise PermissionError(
            "Windows administrator approval is required to register a system camera."
        )
    removing = "--uninstall" in sys.argv
    if removing:
        account_installer.uninstall()
        for arch in ["x64", "x86"]:
            if (DEST / f"deeplive-camera11-{arch}.dll").exists():
                register(arch, True)
        STATUS.write_text(
            json.dumps({"status": "removed", "name": CONFIG["name"]}, indent=2)
        )
        return
    sources = {
        arch: ROOT / "bin" / f"deeplive-camera11-{arch}.dll" for arch in ["x64", "x86"]
    }
    for path in sources.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    DEST.mkdir(parents=True, exist_ok=True)
    for arch, path in sources.items():
        shutil.copy2(path, DEST / path.name)
    # Remove our earlier per-user keys so HKCR registration targets HKLM.
    account_installer.uninstall()
    completed = []
    try:
        for arch in ["x64", "x86"]:
            register(arch)
            completed.append(arch)
        verify()
    except Exception:
        for arch in completed:
            try:
                register(arch, True)
            except Exception:
                pass
        account_installer.install()
        raise
    STATUS.write_text(
        json.dumps(
            {
                "status": "installed",
                "name": CONFIG["name"],
                "scope": "system",
                "directory": str(DEST),
                "architectures": ["x64", "x86"],
                "filter_metadata": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        STATUS.write_text(
            json.dumps({"status": "failed", "error": str(error)}, indent=2)
        )
        raise
