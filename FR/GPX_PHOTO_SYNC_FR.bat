@echo off
setlocal enabledelayedexpansion

REM Script interactif pour generer GPX depuis photos et synchroniser

color 0A
title Gestionnaire GPX - Photos

:MENU_PRINCIPAL
cls
echo ========================================================================
echo                           GPX PHOTO SYNC
echo ========================================================================
echo.
echo   1. Generer GPX depuis photos smartphone
echo   2. Synchroniser GPX vers photos Nikon (NEF)
echo   3. Pipeline complet (1 + 2 automatique)
echo   4. Quitter
echo.
echo ========================================================================
echo.
set /p "choice=Votre choix (1-4): "

if "%choice%"=="1" goto GENERER_GPX
if "%choice%"=="2" goto SYNC_GPX
if "%choice%"=="3" goto PIPELINE_COMPLET
if "%choice%"=="4" goto FIN
goto MENU_PRINCIPAL

REM ============================================================================
REM ETAPE 1: GENERER GPX DEPUIS PHOTOS
REM ============================================================================
:GENERER_GPX
cls
echo ========================================================================
echo              ETAPE 1: GENERER GPX DEPUIS PHOTOS
echo ========================================================================
echo.

echo [1/4] Dossier contenant vos photos smartphone:
echo        (Exemple: F:\Photos\Smartphones\Mobile\2023_best)
echo.
set /p "photo_source=Chemin: "

if not exist "%photo_source%" (
    echo.
    echo [ERREUR] Le dossier n'existe pas!
    pause
    goto GENERER_GPX
)

echo.
echo [2/4] Dossier de destination du GPX (laissez vide = meme dossier):
echo        (Exemple: E:\MesGPX ou laissez vide)
echo.
set /p "gpx_output="

if "%gpx_output%"=="" (
    set "gpx_output=%photo_source%"
)

echo.
echo [3/4] Voulez-vous anonymiser les coordonnees GPS ?
echo        (Remplace coordonnees precises par centre-ville)
echo.
echo   1. NON - Coordonnees exactes (defaut)
echo   2. OUI - Coordonnees centre-ville (anonymise)
echo.
set /p "anon_choice=Votre choix (1-2) [1]: "
if "%anon_choice%"=="" set "anon_choice=1"

set "anonymize_flag="
if "%anon_choice%"=="2" set "anonymize_flag=--anonymize"

echo.
echo ========================================================================
echo RESUME DE LA GENERATION GPX:
echo ========================================================================
echo   Photos source:      %photo_source%
echo   Destination GPX:    %gpx_output%
echo   Anonymisation:      %anon_choice%
if "%anon_choice%"=="2" echo                       (coordonnees centre-ville)
if "%anon_choice%"=="1" echo                       (coordonnees exactes)
echo ========================================================================
echo.
echo Appuyez sur une touche pour lancer la generation...
pause >nul

echo.
echo [4/4] Generation du GPX en cours...
echo.

if "%gpx_output%"=="%photo_source%" (
    python photo_gps_to_gpx_fr.py "%photo_source%" %anonymize_flag%
) else (
    python photo_gps_to_gpx_fr.py "%photo_source%" "%gpx_output%" %anonymize_flag%
)

if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] La generation du GPX a echoue!
    pause
    goto MENU_PRINCIPAL
)

for %%F in ("%photo_source%") do set "folder_name=%%~nxF"
if "%anon_choice%"=="2" (
    set "generated_gpx=%gpx_output%\trace_gps_%folder_name%_anonymized.gpx"
) else (
    set "generated_gpx=%gpx_output%\trace_gps_%folder_name%.gpx"
)

if not exist "%generated_gpx%" (
    for %%F in ("%gpx_output%\trace_gps_%folder_name%*.gpx") do (
        set "generated_gpx=%%F"
    )
)

echo.
echo ========================================================================
echo GPX GENERE AVEC SUCCES!
echo ========================================================================
echo   Fichier: %generated_gpx%
echo ========================================================================
echo.
pause
goto MENU_PRINCIPAL

REM ============================================================================
REM ETAPE 2: SYNCHRONISER GPX VERS PHOTOS
REM ============================================================================
:SYNC_GPX
cls
echo ========================================================================
echo           ETAPE 2: SYNCHRONISER GPX VERS PHOTOS NIKON
echo ========================================================================
echo.

echo [1/4] Dossier contenant les fichiers GPX:
echo        (Exemple: E:\MesGPX)
echo.
set /p "gpx_folder=Chemin: "

if not exist "%gpx_folder%" (
    echo.
    echo [ERREUR] Le dossier n'existe pas!
    pause
    goto SYNC_GPX
)

REM Lister les fichiers GPX disponibles
echo.
echo Recherche des fichiers GPX dans: %gpx_folder%
echo.

set count=0
for %%F in ("%gpx_folder%\*.gpx") do (
    set /a count+=1
    set "gpx_file_!count!=%%F"
    echo   [!count!] %%~nxF
)

if %count%==0 (
    echo [ERREUR] Aucun fichier GPX trouve dans ce dossier!
    pause
    goto SYNC_GPX
)

echo.
echo   [0] Entrer un chemin manuel
echo.
set /p "gpx_choice=Choisissez un fichier (0-%count%): "

if "%gpx_choice%"=="0" (
    echo.
    echo Entrez le chemin complet du fichier GPX:
    set /p "gpx_file=Chemin: "
) else (
    set "gpx_file=!gpx_file_%gpx_choice%!"
)

if not exist "%gpx_file%" (
    echo.
    echo [ERREUR] Le fichier GPX n'existe pas!
    pause
    goto SYNC_GPX
)

echo.
echo [2/4] Dossier contenant vos photos Nikon (NEF):
echo        (Exemple: M:\Photos\NIKON\2018\juillet)
echo.
set /p "nef_folder=Chemin: "

if not exist "%nef_folder%" (
    echo.
    echo [ERREUR] Le dossier n'existe pas!
    pause
    goto SYNC_GPX
)

echo.
echo [3/4] Voulez-vous creer une sauvegarde des fichiers originaux ?
echo        (Recommande pour la premiere utilisation)
echo.
echo   1. OUI - Creer .backup (recommande, defaut)
echo   2. NON - Modifier directement
echo.
set /p "backup_choice=Votre choix (1-2) [1]: "
if "%backup_choice%"=="" set "backup_choice=1"

set "backup_flag="
if "%backup_choice%"=="1" set "backup_flag=--backup"

echo.
echo [4/4] Mode de fonctionnement:
echo.
echo   1. EXECUTION - Modifier reellement les fichiers (defaut)
echo   2. SIMULATION (dry-run) - Tester sans modifier
echo.
set /p "mode_choice=Votre choix (1-2) [1]: "
if "%mode_choice%"=="" set "mode_choice=1"

set "dryrun_flag="
if "%mode_choice%"=="2" set "dryrun_flag=--dry-run"

echo.
echo ========================================================================
echo RESUME DE LA SYNCHRONISATION:
echo ========================================================================
echo   Fichier GPX:        %gpx_file%
echo   Photos NEF:         %nef_folder%
echo   Backup:             %backup_choice%
if "%backup_choice%"=="1" echo                       (fichiers .backup crees)
if "%backup_choice%"=="2" echo                       (pas de backup)
echo   Mode:               %mode_choice%
if "%mode_choice%"=="1" echo                       (SIMULATION - aucune modification)
if "%mode_choice%"=="2" echo                       (EXECUTION - modifications reelles)
echo ========================================================================
echo.
if "%mode_choice%"=="2" (
    echo ATTENTION: Les fichiers NEF vont etre modifies!
    echo.
)
echo Appuyez sur une touche pour lancer la synchronisation...
pause >nul

echo.
echo Synchronisation en cours...
echo.

python sync_gpx_to_photos_fr.py "%gpx_file%" "%nef_folder%" %backup_flag% %dryrun_flag%

if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] La synchronisation a echoue!
    pause
    goto MENU_PRINCIPAL
)

echo.
echo ========================================================================
echo SYNCHRONISATION TERMINEE!
echo ========================================================================
if "%mode_choice%"=="1" (
    echo   Mode: SIMULATION - Aucun fichier modifie
) else (
    echo   Mode: EXECUTION - Fichiers mis a jour
    if "%backup_choice%"=="1" (
        echo   Backups: Disponibles dans %nef_folder% (fichiers .backup)
    )
)
echo ========================================================================
echo.
pause
goto MENU_PRINCIPAL

REM ============================================================================
REM PIPELINE COMPLET (GENERATION + SYNC AUTOMATIQUE)
REM ============================================================================
:PIPELINE_COMPLET
cls
echo ========================================================================
echo            PIPELINE COMPLET: GENERATION + SYNCHRONISATION
echo ========================================================================
echo.

echo ----------------------------------------------------------------------
echo  ETAPE 1/2: GENERATION GPX
echo ----------------------------------------------------------------------
echo.

echo [1/6] Dossier contenant vos photos smartphone:
echo.
set /p "photo_source=Chemin: "

if not exist "%photo_source%" (
    echo [ERREUR] Le dossier n'existe pas!
    pause
    goto PIPELINE_COMPLET
)

echo.
echo [2/6] Dossier de destination du GPX (laissez vide = meme dossier):
echo.
set /p "gpx_output="

if "%gpx_output%"=="" (
    set "gpx_output=%photo_source%"
)

echo.
echo [3/6] Anonymiser les coordonnees GPS ?
echo   1. NON - Coordonnees exactes (defaut)
echo   2. OUI - Coordonnees centre-ville
echo.
set /p "anon_choice=Choix (1-2) [1]: "
if "%anon_choice%"=="" set "anon_choice=1"

set "anonymize_flag="
if "%anon_choice%"=="2" set "anonymize_flag=--anonymize"

echo.
echo ----------------------------------------------------------------------
echo  ETAPE 2/2: SYNCHRONISATION GPX vers PHOTOS NEF
echo ----------------------------------------------------------------------
echo.

echo [4/6] Dossier contenant vos photos Nikon (NEF):
echo.
set /p "nef_folder=Chemin: "

if not exist "%nef_folder%" (
    echo [ERREUR] Le dossier n'existe pas!
    pause
    goto PIPELINE_COMPLET
)

echo.
echo [5/6] Creer une sauvegarde des NEF ?
echo   1. OUI - Creer .backup (recommande, defaut)
echo   2. NON - Modifier directement
echo.
set /p "backup_choice=Choix (1-2) [1]: "
if "%backup_choice%"=="" set "backup_choice=1"

set "backup_flag="
if "%backup_choice%"=="1" set "backup_flag=--backup"

echo.
echo [6/6] Mode de fonctionnement:
echo   1. EXECUTION - Modifier reellement les fichiers (defaut)
echo   2. SIMULATION (dry-run) - Tester sans modifier
echo.
set /p "mode_choice=Choix (1-2) [1]: "
if "%mode_choice%"=="" set "mode_choice=1"

set "dryrun_flag="
if "%mode_choice%"=="2" set "dryrun_flag=--dry-run"

echo.
echo ========================================================================
echo RESUME DU PIPELINE COMPLET:
echo ========================================================================
echo ETAPE 1 - GENERATION GPX:
echo   Photos smartphone:  %photo_source%
echo   Destination GPX:    %gpx_output%
echo   Anonymisation:      %anon_choice%
echo.
echo ETAPE 2 - SYNCHRONISATION:
echo   Photos NEF:         %nef_folder%
echo   Backup:             %backup_choice%
echo   Mode:               %mode_choice%
echo ========================================================================
echo.
echo Appuyez sur une touche pour lancer le pipeline complet...
pause >nul

echo.
echo ========================================================================
echo [ETAPE 1/2] Generation du GPX...
echo ========================================================================
echo.

if "%gpx_output%"=="%photo_source%" (
    python photo_gps_to_gpx_fr.py "%photo_source%" %anonymize_flag%
) else (
    python photo_gps_to_gpx_fr.py "%photo_source%" "%gpx_output%" %anonymize_flag%
)

if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] La generation du GPX a echoue!
    pause
    goto MENU_PRINCIPAL
)

for %%F in ("%photo_source%") do set "folder_name=%%~nxF"
if "%anon_choice%"=="2" (
    set "generated_gpx=%gpx_output%\trace_gps_%folder_name%_anonymized.gpx"
) else (
    set "generated_gpx=%gpx_output%\trace_gps_%folder_name%.gpx"
)

if not exist "%generated_gpx%" (
    for %%F in ("%gpx_output%\trace_gps_%folder_name%*.gpx") do (
        set "generated_gpx=%%F"
    )
)

echo.
echo GPX genere: %generated_gpx%
timeout /t 2 >nul

echo.
echo ========================================================================
echo [ETAPE 2/2] Synchronisation GPX vers Photos NEF...
echo ========================================================================
echo.

python sync_gpx_to_photos_fr.py "%generated_gpx%" "%nef_folder%" %backup_flag% %dryrun_flag%

if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] La synchronisation a echoue!
    pause
    goto MENU_PRINCIPAL
)

echo.
echo ========================================================================
echo PIPELINE COMPLET TERMINE AVEC SUCCES!
echo ========================================================================
echo   1. GPX genere:      %generated_gpx%
echo   2. Photos synchronisees dans: %nef_folder%
if "%mode_choice%"=="1" echo   Mode: SIMULATION
if "%mode_choice%"=="2" echo   Mode: EXECUTION
echo ========================================================================
echo.
pause
goto MENU_PRINCIPAL

:FIN
cls
echo.
echo ========================================================================
echo                     Au revoir!
echo ========================================================================
echo.
timeout /t 2 >nul
exit /b 0
