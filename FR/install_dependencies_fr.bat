@echo off
REM ============================================================================
REM Script d'installation des dépendances Python
REM Pour les scripts: photo_gps_to_gpx.py et sync_gpx_to_photos.py
REM ============================================================================

echo ========================================================================
echo Installation des dependances Python
echo ========================================================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo.
    echo Telechargez Python depuis: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python detecte:
python --version
echo.

REM Mettre à jour pip
echo [1/2] Mise a jour de pip...
python -m pip install --upgrade pip --quiet
if %errorlevel% neq 0 (
    echo [ERREUR] Echec de la mise a jour de pip
    pause
    exit /b 1
)
echo [OK] pip mis a jour
echo.

REM Installer les dépendances
echo [2/2] Installation des bibliotheques...
echo.

echo   - Pillow (traitement d'images)...
python -m pip install Pillow --quiet
if %errorlevel% neq 0 (
    echo [ERREUR] Echec installation Pillow
    pause
    exit /b 1
)
echo   [OK] Pillow installe

echo   - piexif (lecture EXIF pour NEF)...
python -m pip install piexif --quiet
if %errorlevel% neq 0 (
    echo [ERREUR] Echec installation piexif
    pause
    exit /b 1
)
echo   [OK] piexif installe

echo   - requests (requetes HTTP)...
python -m pip install requests --quiet
if %errorlevel% neq 0 (
    echo [ERREUR] Echec installation requests
    pause
    exit /b 1
)
echo   [OK] requests installe

echo   - pyexiv2 (metadata EXIF/IPTC pour RAW)...
python -m pip install pyexiv2 --quiet
if %errorlevel% neq 0 (
    echo [ERREUR] Echec installation pyexiv2
    pause
    exit /b 1
)
echo   [OK] pyexiv2 installe

echo.
echo ========================================================================
echo Installation terminee avec succes !
echo ========================================================================
echo.
echo Vous pouvez maintenant utiliser:
echo   - photo_gps_to_gpx.py       (generer GPX depuis photos)
echo   - sync_gpx_to_photos.py     (synchroniser GPX vers photos)
echo.
pause