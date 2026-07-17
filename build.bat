@echo off
echo ===========================
echo Building with PyInstaller...
echo ===========================

pyinstaller build.spec

if %errorlevel% neq 0 (
    echo Build failed!
    exit /b %errorlevel%
)

echo.
echo ===========================
echo Compressing with UPX...
echo ===========================
REM Change to the output folder name in your spec (omni_describer_dist)
cd dist\omni_describer_dist

REM Compress the main EXE (UPX must be on your PATH)
upx omni_describer.exe

cd ../..

echo Done!
pause
