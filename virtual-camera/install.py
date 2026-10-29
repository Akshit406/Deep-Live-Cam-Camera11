"""Install/remove the standalone DirectShow camera for the current Windows user."""

from pathlib import Path
import argparse, json, winreg, shutil

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "camera.json").read_text())
CLSID = CONFIG["clsid"]
CATEGORY = "{860BB310-5D01-11D0-BD3B-00A0C911CE86}"


def put(key, name, value, view):
    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_WRITE | view
    ) as handle:
        winreg.SetValueEx(handle, name, 0, winreg.REG_SZ, value)


def delete_tree(path, view):
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ | view
        ) as key:
            children = []
            while True:
                try:
                    children.append(winreg.EnumKey(key, len(children)))
                except OSError:
                    break
        for child in children:
            delete_tree(path + "\\" + child, view)
        winreg.DeleteKeyEx(winreg.HKEY_CURRENT_USER, path, view)
    except FileNotFoundError:
        pass


def install():
    (ROOT / "bin").mkdir(exist_ok=True)
    for arch, view in [
        ("x64", winreg.KEY_WOW64_64KEY),
        ("x86", winreg.KEY_WOW64_32KEY),
    ]:
        built = ROOT / f"build-{arch}/Release/deeplive-camera11-{arch}.dll"
        if not built.exists():
            raise FileNotFoundError(built)
        dll = ROOT / "bin" / built.name
        shutil.copy2(built, dll)
        base = "Software\\Classes\\CLSID\\" + CLSID
        put(base, "", "Deep-Live-Cam Camera11 Virtual Camera", view)
        put(base + "\\InprocServer32", "", str(dll), view)
        put(base + "\\InprocServer32", "ThreadingModel", "Both", view)
        instance = "Software\\Classes\\CLSID\\" + CATEGORY + "\\Instance\\" + CLSID
        put(instance, "CLSID", CLSID, view)
        put(instance, "FriendlyName", CONFIG["name"], view)
    print("Installed:", CONFIG["name"])


def uninstall():
    for view in [winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY]:
        delete_tree(
            "Software\\Classes\\CLSID\\" + CATEGORY + "\\Instance\\" + CLSID, view
        )
        delete_tree("Software\\Classes\\CLSID\\" + CLSID, view)
    print("Removed the Camera11 registration.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    uninstall() if args.uninstall else install()
