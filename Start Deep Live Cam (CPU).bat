@echo off
cd /d "%~dp0"
set "KERAS_BACKEND=torch"
"%~dp0venv\Scripts\python.exe" run.py --frame-processor face_swapper face_enhancer_gpen512 --execution-provider cpu
if errorlevel 1 pause
