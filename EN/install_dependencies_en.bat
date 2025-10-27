@echo off
REM ============================================================================
REM Python dependencies installation script
REM For scripts: photo_gps_to_gpx.py and sync_gpx_to_photos.py
REM ============================================================================

echo ========================================================================
echo Python Dependencies Installation
echo ========================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Download Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python detected:
python --version
echo.

REM Update pip
echo [1/2] Updating pip...
python -m pip install --upgrade pip --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to update pip
    pause
    exit /b 1
)
echo [OK] pip updated
echo.

REM Install dependencies
echo [2/2] Installing libraries...
echo.

echo   - Pillow (image processing)...
python -m pip install Pillow --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Pillow
    pause
    exit /b 1
)
echo   [OK] Pillow installed

echo   - piexif (EXIF reading for NEF)...
python -m pip install piexif --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install piexif
    pause
    exit /b 1
)
echo   [OK] piexif installed

echo   - requests (HTTP requests)...
python -m pip install requests --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requests
    pause
    exit /b 1
)
echo   [OK] requests installed

echo   - pyexiv2 (EXIF/IPTC metadata for RAW)...
python -m pip install pyexiv2 --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install pyexiv2
    pause
    exit /b 1
)
echo   [OK] pyexiv2 installed

echo.
echo ========================================================================
echo Installation completed successfully!
echo ========================================================================
echo.
echo You can now use:
echo   - photo_gps_to_gpx.py       (generate GPX from photos)
echo   - sync_gpx_to_photos.py     (synchronize GPX to photos)
echo.
pause
    