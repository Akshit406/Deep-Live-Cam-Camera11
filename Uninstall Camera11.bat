@echo off
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" virtual-camera\request-install.py --uninstall
pause
