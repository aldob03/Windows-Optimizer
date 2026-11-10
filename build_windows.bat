@echo off
setlocal
py -m venv .venv
call .venv\Scripts\activate
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --clean --windowed --onefile --name "Windows Optimizer" --collect-all PySide6 main.py
echo.
echo Build completata. File: dist\Windows Optimizer.exe
pause
