"""Request Windows elevation for the tightly scoped Camera11 installer."""

from pathlib import Path
import ctypes
from ctypes import wintypes
import subprocess
import sys


class ShellExecuteInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("fMask", wintypes.ULONG),
        ("hwnd", wintypes.HWND),
        ("lpVerb", wintypes.LPCWSTR),
        ("lpFile", wintypes.LPCWSTR),
        ("lpParameters", wintypes.LPCWSTR),
        ("lpDirectory", wintypes.LPCWSTR),
        ("nShow", ctypes.c_int),
        ("hInstApp", wintypes.HINSTANCE),
        ("lpIDList", ctypes.c_void_p),
        ("lpClass", wintypes.LPCWSTR),
        ("hkeyClass", wintypes.HKEY),
        ("dwHotKey", wintypes.DWORD),
        ("hIcon", wintypes.HANDLE),
        ("hProcess", wintypes.HANDLE),
    ]


def main():
    wait = "--wait" in sys.argv
    script = Path(__file__).resolve().with_name("install-system.py")
    arguments = subprocess.list2cmdline(
        [str(script), *[arg for arg in sys.argv[1:] if arg != "--wait"]]
    )
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    shell.ShellExecuteExW.argtypes = [ctypes.POINTER(ShellExecuteInfo)]
    shell.ShellExecuteExW.restype = wintypes.BOOL
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.GetExitCodeProcess.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    info = ShellExecuteInfo()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = 0x00000040  # SEE_MASK_NOCLOSEPROCESS
    info.lpVerb = "runas"
    info.lpFile = sys.executable
    info.lpParameters = arguments
    info.lpDirectory = str(script.parent.parent)
    info.nShow = 0
    if not shell.ShellExecuteExW(ctypes.byref(info)):
        raise SystemExit(
            "Windows did not approve the camera installer. No installation was started."
        )
    try:
        if wait:
            if kernel.WaitForSingleObject(info.hProcess, 0xFFFFFFFF) != 0:
                raise OSError(
                    ctypes.get_last_error(), "Waiting for the camera installer failed"
                )
            result = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(info.hProcess, ctypes.byref(result)):
                raise ctypes.WinError(ctypes.get_last_error())
            if result.value:
                raise SystemExit(
                    f"Camera installer failed with code {result.value}; see virtual-camera/system-install-status.json."
                )
            print("Camera installer completed successfully.")
        else:
            print(
                "Camera installer started. Its result is saved in virtual-camera/system-install-status.json."
            )
    finally:
        if info.hProcess:
            kernel.CloseHandle(info.hProcess)


if __name__ == "__main__":
    main()
