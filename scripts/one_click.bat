@echo off
REM Python conversion to exe starts
pyinstaller --onefile --name VektorConverter --windowed --icon=../img/VektorConverter.ico gui.py
echo Done conversion!

REM Moving exe into main directory
move ".\dist\VektorConverter.exe" "..\VektorConverter.exe"
echo exe is now at main path!

REM Delete build folder
if exist ".\build" (
    rmdir /S /Q ".\build"
    echo "build/ folder deleted"
)

REM Delete dist folder (optional, comment out if you want to keep the exe)
if exist ".\dist" (
    rmdir /S /Q ".\dist"
    echo "dist/ folder deleted"
)

REM Delete .spec file (optional)
for %%f in (*.spec) do del /F /Q "%%f"

echo All PyInstaller-generated files cleaned!
pause