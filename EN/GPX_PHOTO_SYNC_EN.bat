@echo off
setlocal enabledelayedexpansion

REM Interactive script to generate GPX from photos and synchronize

color 0A
title GPX PHOTO SYNC - by miamax_

:MAIN_MENU
cls
echo ========================================================================
echo                           GPX PHOTO SYNC
echo ========================================================================
echo.
echo   1. Generate GPX from smartphone photos
echo   2. Synchronize GPX to Nikon photos (NEF)
echo   3. Complete Pipeline (1 + 2 automatic)
echo   4. Exit
echo.
echo ========================================================================
echo.
set /p "choice=Your choice (1-4): "

if "%choice%"=="1" goto GENERATE_GPX
if "%choice%"=="2" goto SYNC_GPX
if "%choice%"=="3" goto COMPLETE_PIPELINE
if "%choice%"=="4" goto END
goto MAIN_MENU

REM ============================================================================
REM STEP 1: GENERATE GPX FROM PHOTOS
REM ============================================================================
:GENERATE_GPX
cls
echo ========================================================================
echo              STEP 1: GENERATE GPX FROM PHOTOS
echo ========================================================================
echo.

echo [1/4] Folder containing your smartphone photos:
echo        (Example: F:\Photos\Smartphones\Mobile\2023_best)
echo.
set /p "photo_source=Path: "

if not exist "%photo_source%" (
    echo.
    echo [ERROR] Folder does not exist!
    pause
    goto GENERATE_GPX
)

echo.
echo [2/4] GPX destination folder (leave empty = same folder):
echo        (Example: E:\MyGPX or leave empty)
echo.
set /p "gpx_output="

if "%gpx_output%"=="" (
    set "gpx_output=%photo_source%"
)

echo.
echo [3/4] Do you want to anonymize GPS coordinates?
echo        (Replaces precise coordinates with city center)
echo.
echo   1. NO - Exact coordinates (default)
echo   2. YES - City center coordinates (anonymized)
echo.
set /p "anon_choice=Your choice (1-2) [1]: "
if "%anon_choice%"=="" set "anon_choice=1"

set "anonymize_flag="
if "%anon_choice%"=="2" set "anonymize_flag=--anonymize"

echo.
echo ========================================================================
echo GPX GENERATION SUMMARY:
echo ========================================================================
echo   Source photos:      %photo_source%
echo   GPX destination:    %gpx_output%
echo   Anonymization:      %anon_choice%
if "%anon_choice%"=="2" echo                       (city center coordinates)
if "%anon_choice%"=="1" echo                       (exact coordinates)
echo ========================================================================
echo.
echo Press any key to start generation...
pause >nul

echo.
echo [4/4] Generating GPX...
echo.

if "%gpx_output%"=="%photo_source%" (
    python photo_gps_to_gpx_en.py "%photo_source%" %anonymize_flag%
) else (
    python photo_gps_to_gpx_en.py "%photo_source%" "%gpx_output%" %anonymize_flag%
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] GPX generation failed!
    pause
    goto MAIN_MENU
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
echo GPX GENERATED SUCCESSFULLY!
echo ========================================================================
echo   File: %generated_gpx%
echo ========================================================================
echo.
pause
goto MAIN_MENU

REM ============================================================================
REM STEP 2: SYNCHRONIZE GPX TO PHOTOS
REM ============================================================================
:SYNC_GPX
cls
echo ========================================================================
echo           STEP 2: SYNCHRONIZE GPX TO NIKON PHOTOS
echo ========================================================================
echo.

echo [1/4] Folder containing GPX files:
echo        (Example: E:\MyGPX)
echo.
set /p "gpx_folder=Path: "

if not exist "%gpx_folder%" (
    echo.
    echo [ERROR] Folder does not exist!
    pause
    goto SYNC_GPX
)

REM List available GPX files
echo.
echo Searching for GPX files in: %gpx_folder%
echo.

set count=0
for %%F in ("%gpx_folder%\*.gpx") do (
    set /a count+=1
    set "gpx_file_!count!=%%F"
    echo   [!count!] %%~nxF
)

if %count%==0 (
    echo [ERROR] No GPX file found in this folder!
    pause
    goto SYNC_GPX
)

echo.
echo   [0] Enter manual path
echo.
set /p "gpx_choice=Choose a file (0-%count%): "

if "%gpx_choice%"=="0" (
    echo.
    echo Enter the full path of the GPX file:
    set /p "gpx_file=Path: "
) else (
    set "gpx_file=!gpx_file_%gpx_choice%!"
)

if not exist "%gpx_file%" (
    echo.
    echo [ERROR] GPX file does not exist!
    pause
    goto SYNC_GPX
)

echo.
echo [2/4] Folder containing your Nikon photos (NEF):
echo        (Example: M:\Photos\NIKON\2018\july)
echo.
set /p "nef_folder=Path: "

if not exist "%nef_folder%" (
    echo.
    echo [ERROR] Folder does not exist!
    pause
    goto SYNC_GPX
)

echo.
echo [3/4] Do you want to create a backup of the original files?
echo        (Recommended for first use)
echo.
echo   1. YES - Create .backup (recommended, default)
echo   2. NO - Modify directly
echo.
set /p "backup_choice=Your choice (1-2) [1]: "
if "%backup_choice%"=="" set "backup_choice=1"

set "backup_flag="
if "%backup_choice%"=="1" set "backup_flag=--backup"

echo.
echo [4/4] Operating mode:
echo.
echo   1. EXECUTION - Actually modify files (default)
echo   2. SIMULATION (dry-run) - Test without modifying
echo.
set /p "mode_choice=Your choice (1-2) [1]: "
if "%mode_choice%"=="" set "mode_choice=1"

set "dryrun_flag="
if "%mode_choice%"=="2" set "dryrun_flag=--dry-run"

echo.
echo ========================================================================
echo SYNCHRONIZATION SUMMARY:
echo ========================================================================
echo   GPX file:           %gpx_file%
echo   NEF photos:         %nef_folder%
echo   Backup:             %backup_choice%
if "%backup_choice%"=="1" echo                       (.backup files created)
if "%backup_choice%"=="2" echo                       (no backup)
echo   Mode:               %mode_choice%
if "%mode_choice%"=="2" echo                       (SIMULATION - no modifications)
if "%mode_choice%"=="1" echo                       (EXECUTION - actual modifications)
echo ========================================================================
echo.
if "%mode_choice%"=="1" (
    echo WARNING: NEF files will be modified!
    echo.
)
echo Press any key to start synchronization...
pause >nul

echo.
echo Synchronizing...
echo.

python sync_gpx_to_photos_en.py "%gpx_file%" "%nef_folder%" %backup_flag% %dryrun_flag%

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Synchronization failed!
    pause
    goto MAIN_MENU
)

echo.
echo ========================================================================
echo SYNCHRONIZATION COMPLETE!
echo ========================================================================
if "%mode_choice%"=="2" (
    echo   Mode: SIMULATION - No files modified
) else (
    echo   Mode: EXECUTION - Files updated
    if "%backup_choice%"=="1" (
        echo   Backups: Available in %nef_folder% (.backup files)
    )
)
echo ========================================================================
echo.
pause
goto MAIN_MENU

REM ============================================================================
REM COMPLETE PIPELINE (GENERATION + AUTOMATIC SYNC)
REM ============================================================================
:COMPLETE_PIPELINE
cls
echo ========================================================================
echo            COMPLETE PIPELINE: GENERATION + SYNCHRONIZATION
echo ========================================================================
echo.

echo ----------------------------------------------------------------------
echo  STEP 1/2: GPX GENERATION
echo ----------------------------------------------------------------------
echo.

echo [1/6] Folder containing your smartphone photos:
echo.
set /p "photo_source=Path: "

if not exist "%photo_source%" (
    echo [ERROR] Folder does not exist!
    pause
    goto COMPLETE_PIPELINE
)

echo.
echo [2/6] GPX destination folder (leave empty = same folder):
echo.
set /p "gpx_output="

if "%gpx_output%"=="" (
    set "gpx_output=%photo_source%"
)

echo.
echo [3/6] Anonymize GPS coordinates?
echo   1. NO - Exact coordinates (default)
echo   2. YES - City center coordinates
echo.
set /p "anon_choice=Choice (1-2) [1]: "
if "%anon_choice%"=="" set "anon_choice=1"

set "anonymize_flag="
if "%anon_choice%"=="2" set "anonymize_flag=--anonymize"

echo.
echo ----------------------------------------------------------------------
echo  STEP 2/2: SYNCHRONIZATION GPX to NEF PHOTOS
echo ----------------------------------------------------------------------
echo.

echo [4/6] Folder containing your Nikon photos (NEF):
echo.
set /p "nef_folder=Path: "

if not exist "%nef_folder%" (
    echo [ERROR] Folder does not exist!
    pause
    goto COMPLETE_PIPELINE
)

echo.
echo [5/6] Create a backup of NEF files?
echo   1. YES - Create .backup (recommended, default)
echo   2. NO - Modify directly
echo.
set /p "backup_choice=Choice (1-2) [1]: "
if "%backup_choice%"=="" set "backup_choice=1"

set "backup_flag="
if "%backup_choice%"=="1" set "backup_flag=--backup"

echo.
echo [6/6] Operating mode:
echo   1. EXECUTION - Actually modify files (default)
echo   2. SIMULATION (dry-run)
echo.
set /p "mode_choice=Choice (1-2) [1]: "
if "%mode_choice%"=="" set "mode_choice=1"

set "dryrun_flag="
if "%mode_choice%"=="2" set "dryrun_flag=--dry-run"

echo.
echo ========================================================================
echo COMPLETE PIPELINE SUMMARY:
echo ========================================================================
echo STEP 1 - GPX GENERATION:
echo   Smartphone photos:  %photo_source%
echo   GPX destination:    %gpx_output%
echo   Anonymization:      %anon_choice%
echo.
echo STEP 2 - SYNCHRONIZATION:
echo   NEF photos:         %nef_folder%
echo   Backup:             %backup_choice%
echo   Mode:               %mode_choice%
echo ========================================================================
echo.
echo Press any key to start the complete pipeline...
pause >nul

echo.
echo ========================================================================
echo [STEP 1/2] Generating GPX...
echo ========================================================================
echo.

if "%gpx_output%"=="%photo_source%" (
    python photo_gps_to_gpx_en.py "%photo_source%" %anonymize_flag%
) else (
    python photo_gps_to_gpx_en.py "%photo_source%" "%gpx_output%" %anonymize_flag%
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] GPX generation failed!
    pause
    goto MAIN_MENU
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
echo GPX generated: %generated_gpx%
timeout /t 2 >nul

echo.
echo ========================================================================
echo [STEP 2/2] Synchronizing GPX to NEF photos...
echo ========================================================================
echo.

python sync_gpx_to_photos_en.py "%generated_gpx%" "%nef_folder%" %backup_flag% %dryrun_flag%

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Synchronization failed!
    pause
    goto MAIN_MENU
)

echo.
echo ========================================================================
echo COMPLETE PIPELINE FINISHED SUCCESSFULLY!
echo ========================================================================
echo   1. GPX generated:      %generated_gpx%
echo   2. Photos synchronized in: %nef_folder%
if "%mode_choice%"=="1" echo   Mode: EXECUTION
if "%mode_choice%"=="2" echo   Mode: SIMULATION
echo ========================================================================
echo.
pause
goto MAIN_MENU

:END
cls
echo.
echo ========================================================================
echo                     Goodbye!
echo ========================================================================
echo.
timeout /t 2 >nul
exit /b 0