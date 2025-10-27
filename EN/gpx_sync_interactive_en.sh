#!/bin/bash

# Interactive script to generate GPX from photos and synchronize

# Function to display main menu
show_menu() {
    clear
    echo "========================================================================"
    echo "                 GPX PHOTO MANAGER"
    echo "========================================================================"
    echo
    echo "  1. Generate GPX from smartphone photos"
    echo "  2. Synchronize GPX to Nikon photos (NEF)"
    echo "  3. Complete Pipeline (1 + 2 automatic)"
    echo "  4. Exit"
    echo
    echo "========================================================================"
    echo
}

# Function to generate GPX from photos
generate_gpx() {
    clear
    echo "========================================================================"
    echo "              STEP 1: GENERATE GPX FROM PHOTOS"
    echo "========================================================================"
    echo

    echo "[1/4] Folder containing your smartphone photos:"
    echo "       (Example: /media/Photos/Smartphones/Mobile/2023_best)"
    echo
    read -p "Path: " photo_source

    if [ ! -d "$photo_source" ]; then
        echo
        echo "[ERROR] Folder does not exist!"
        read -p "Press Enter to continue..."
        return
    fi

    echo
    echo "[2/4] GPX destination folder (leave empty = same folder):"
    echo "       (Example: /media/MyGPX or leave empty)"
    echo
    read -p "Path: " gpx_output

    if [ -z "$gpx_output" ]; then
        gpx_output="$photo_source"
    fi

    echo
    echo "[3/4] Do you want to anonymize GPS coordinates?"
    echo "       (Replaces precise coordinates with city center)"
    echo
    echo "  1. NO - Exact coordinates (default)"
    echo "  2. YES - City center coordinates (anonymized)"
    echo
    read -p "Your choice (1-2) [1]: " anon_choice
    anon_choice=${anon_choice:-1}

    anonymize_flag=""
    [ "$anon_choice" = "2" ] && anonymize_flag="--anonymize"

    echo
    echo "========================================================================"
    echo "GPX GENERATION SUMMARY:"
    echo "========================================================================"
    echo "  Source photos:      $photo_source"
    echo "  GPX destination:    $gpx_output"
    echo "  Anonymization:      $anon_choice"
    if [ "$anon_choice" = "2" ]; then
        echo "                      (city center coordinates)"
    else
        echo "                      (exact coordinates)"
    fi
    echo "========================================================================"
    echo
    read -p "Press Enter to start generation..."

    echo
    echo "[4/4] Generating GPX..."
    echo

    if [ "$gpx_output" = "$photo_source" ]; then
        python3 photo_gps_to_gpx_en.py "$photo_source" $anonymize_flag
    else
        python3 photo_gps_to_gpx_en.py "$photo_source" "$gpx_output" $anonymize_flag
    fi

    if [ $? -ne 0 ]; then
        echo
        echo "[ERROR] GPX generation failed!"
        read -p "Press Enter to continue..."
        return
    fi

    folder_name=$(basename "$photo_source")
    if [ "$anon_choice" = "2" ]; then
        generated_gpx="$gpx_output/trace_gps_${folder_name}_anonymized.gpx"
    else
        generated_gpx="$gpx_output/trace_gps_${folder_name}.gpx"
    fi

    if [ ! -f "$generated_gpx" ]; then
        generated_gpx=$(ls "$gpx_output"/trace_gps_${folder_name}*.gpx 2>/dev/null | head -n 1)
    fi

    echo
    echo "========================================================================"
    echo "GPX GENERATED SUCCESSFULLY!"
    echo "========================================================================"
    echo "  File: $generated_gpx"
    echo "========================================================================"
    echo
    read -p "Press Enter to continue..."
}

# Function to synchronize GPX to photos
sync_gpx() {
    clear
    echo "========================================================================"
    echo "           STEP 2: SYNCHRONIZE GPX TO NIKON PHOTOS"
    echo "========================================================================"
    echo

    echo "[1/4] Folder containing GPX files:"
    echo "       (Example: /media/MyGPX)"
    echo
    read -p "Path: " gpx_folder

    if [ ! -d "$gpx_folder" ]; then
        echo
        echo "[ERROR] Folder does not exist!"
        read -p "Press Enter to continue..."
        return
    fi

    echo
    echo "Searching for GPX files in: $gpx_folder"
    echo

    # List available GPX files
    declare -a gpx_files
    count=0
    while IFS= read -r -d '' file; do
        ((count++))
        gpx_files[$count]="$file"
        echo "  [$count] $(basename "$file")"
    done < <(find "$gpx_folder" -maxdepth 1 -name "*.gpx" -print0)

    if [ $count -eq 0 ]; then
        echo "[ERROR] No GPX file found in this folder!"
        read -p "Press Enter to continue..."
        return
    fi

    echo
    echo "  [0] Enter manual path"
    echo
    read -p "Choose a file (0-$count): " gpx_choice

    if [ "$gpx_choice" = "0" ]; then
        echo
        echo "Enter the full path of the GPX file:"
        read -p "Path: " gpx_file
    else
        gpx_file="${gpx_files[$gpx_choice]}"
    fi

    if [ ! -f "$gpx_file" ]; then
        echo
        echo "[ERROR] GPX file does not exist!"
        read -p "Press Enter to continue..."
        return
    fi

    echo
    echo "[2/4] Folder containing your Nikon photos (NEF):"
    echo "       (Example: /media/Photos/NIKON/2018/july)"
    echo
    read -p "Path: " nef_folder

    if [ ! -d "$nef_folder" ]; then
        echo
        echo "[ERROR] Folder does not exist!"
        read -p "Press Enter to continue..."
        return
    fi

    echo
    echo "[3/4] Do you want to create a backup of the original files?"
    echo "       (Recommended for first use)"
    echo
    echo "  1. YES - Create .backup (recommended, default)"
    echo "  2. NO - Modify directly"
    echo
    read -p "Your choice (1-2) [1]: " backup_choice
    backup_choice=${backup_choice:-1}

    backup_flag=""
    [ "$backup_choice" = "1" ] && backup_flag="--backup"

    echo
    echo "[4/4] Operating mode:"
    echo
    echo "  1. EXECUTION - Actually modify files (default)"
    echo "  2. SIMULATION (dry-run) - Test without modifying"
    echo
    read -p "Your choice (1-2) [1]: " mode_choice
    mode_choice=${mode_choice:-1}

    dryrun_flag=""
    [ "$mode_choice" = "2" ] && dryrun_flag="--dry-run"

    echo
    echo "========================================================================"
    echo "SYNCHRONIZATION SUMMARY:"
    echo "========================================================================"
    echo "  GPX file:           $gpx_file"
    echo "  NEF photos:         $nef_folder"
    echo "  Backup:             $backup_choice"
    if [ "$backup_choice" = "1" ]; then
        echo "                      (.backup files created)"
    else
        echo "                      (no backup)"
    fi
    echo "  Mode:               $mode_choice"
    if [ "$mode_choice" = "2" ]; then
        echo "                      (SIMULATION - no modifications)"
    else
        echo "                      (EXECUTION - actual modifications)"
    fi
    echo "========================================================================"
    echo

    if [ "$mode_choice" = "1" ]; then
        echo "WARNING: NEF files will be modified!"
        echo
    fi
    read -p "Press Enter to start synchronization..."

    echo
    echo "Synchronizing..."
    echo

    python3 sync_gpx_to_photos_en.py "$gpx_file" "$nef_folder" $backup_flag $dryrun_flag

    if [ $? -ne 0 ]; then
        echo
        echo "[ERROR] Synchronization failed!"
        read -p "Press Enter to continue..."
        return
    fi

    echo
    echo "========================================================================"
    echo "SYNCHRONIZATION COMPLETE!"
    echo "========================================================================"
    if [ "$mode_choice" = "2" ]; then
        echo "  Mode: SIMULATION - No files modified"
    else
        echo "  Mode: EXECUTION - Files updated"
        if [ "$backup_choice" = "1" ]; then
            echo "  Backups: Available in $nef_folder (.backup files)"
        fi
    fi
    echo "========================================================================"
    echo
    read -p "Press Enter to continue..."
}

# Function to execute complete pipeline
pipeline_complete() {
    clear
    echo "========================================================================"
    echo "            COMPLETE PIPELINE: GENERATION + SYNCHRONIZATION"
    echo "========================================================================"
    echo

    echo "----------------------------------------------------------------------"
    echo " STEP 1/2: GPX GENERATION"
    echo "----------------------------------------------------------------------"
    echo

    echo "[1/6] Folder containing your smartphone photos:"
    echo
    read -p "Path: " photo_source

    if [ ! -d "$photo_source" ]; then
        echo "[ERROR] Folder does not exist!"
        read -p "Press Enter to continue..."
        return
    fi

    echo
    echo "[2/6] GPX destination folder (leave empty = same folder):"
    echo
    read -p "Path: " gpx_output

    if [ -z "$gpx_output" ]; then
        gpx_output="$photo_source"
    fi

    echo
    echo "[3/6] Anonymize GPS coordinates?"
    echo "  1. NO - Exact coordinates (default)"
    echo "  2. YES - City center coordinates"
    echo
    read -p "Choice (1-2) [1]: " anon_choice
    anon_choice=${anon_choice:-1}

    anonymize_flag=""
    [ "$anon_choice" = "2" ] && anonymize_flag="--anonymize"

    echo
    echo "----------------------------------------------------------------------"
    echo " STEP 2/2: SYNCHRONIZATION GPX to NEF PHOTOS"
    echo "----------------------------------------------------------------------"
    echo

    echo "[4/6] Folder containing your Nikon photos (NEF):"
    echo
    read -p "Path: " nef_folder

    if [ ! -d "$nef_folder" ]; then
        echo "[ERROR] Folder does not exist!"
        read -p "Press Enter to continue..."
        return
    fi

    echo
    echo "[5/6] Create a backup of NEF files?"
    echo "  1. YES - Create .backup (recommended, default)"
    echo "  2. NO - Modify directly"
    echo
    read -p "Choice (1-2) [1]: " backup_choice
    backup_choice=${backup_choice:-1}

    backup_flag=""
    [ "$backup_choice" = "1" ] && backup_flag="--backup"

    echo
    echo "[6/6] Operating mode:"
    echo "  1. EXECUTION - Actually modify files (default)"
    echo "  2. SIMULATION (dry-run) - Test without modifying"
    echo
    read -p "Choice (1-2) [1]: " mode_choice
    mode_choice=${mode_choice:-1}

    dryrun_flag=""
    [ "$mode_choice" = "2" ] && dryrun_flag="--dry-run"

    echo
    echo "========================================================================"
    echo "COMPLETE PIPELINE SUMMARY:"
    echo "========================================================================"
    echo "STEP 1 - GPX GENERATION:"
    echo "  Smartphone photos:  $photo_source"
    echo "  GPX destination:    $gpx_output"
    echo "  Anonymization:      $anon_choice"
    echo
    echo "STEP 2 - SYNCHRONIZATION:"
    echo "  NEF photos:         $nef_folder"
    echo "  Backup:             $backup_choice"
    echo "  Mode:               $mode_choice"
    echo "========================================================================"
    echo
    read -p "Press Enter to start the complete pipeline..."

    echo
    echo "========================================================================"
    echo "[STEP 1/2] Generating GPX..."
    echo "========================================================================"
    echo

    if [ "$gpx_output" = "$photo_source" ]; then
        python3 photo_gps_to_gpx_en.py "$photo_source" $anonymize_flag
    else
        python3 photo_gps_to_gpx_en.py "$photo_source" "$gpx_output" $anonymize_flag
    fi

    if [ $? -ne 0 ]; then
        echo
        echo "[ERROR] GPX generation failed!"
        read -p "Press Enter to continue..."
        return
    fi

    folder_name=$(basename "$photo_source")
    if [ "$anon_choice" = "2" ]; then
        generated_gpx="$gpx_output/trace_gps_${folder_name}_anonymized.gpx"
    else
        generated_gpx="$gpx_output/trace_gps_${folder_name}.gpx"
    fi

    if [ ! -f "$generated_gpx" ]; then
        generated_gpx=$(ls "$gpx_output"/trace_gps_${folder_name}*.gpx 2>/dev/null | head -n 1)
    fi

    echo
    echo "GPX generated: $generated_gpx"
    sleep 2

    echo
    echo "========================================================================"
    echo "[STEP 2/2] Synchronizing GPX to NEF photos..."
    echo "========================================================================"
    echo

    python3 sync_gpx_to_photos_en.py "$generated_gpx" "$nef_folder" $backup_flag $dryrun_flag

    if [ $? -ne 0 ]; then
        echo
        echo "[ERROR] Synchronization failed!"
        read -p "Press Enter to continue..."
        return
    fi

    echo
    echo "========================================================================"
    echo "COMPLETE PIPELINE FINISHED SUCCESSFULLY!"
    echo "========================================================================"
    echo "  1. GPX generated:      $generated_gpx"
    echo "  2. Photos synchronized in: $nef_folder"
    if [ "$mode_choice" = "1" ]; then
        echo "  Mode: SIMULATION"
    else
        echo "  Mode: EXECUTION"
    fi
    echo "========================================================================"
    echo
    read -p "Press Enter to continue..."
}

# Main menu loop
while true; do
    show_menu
    read -p "Your choice (1-4): " choice
    case $choice in
        1) generate_gpx ;;
        2) sync_gpx ;;
        3) pipeline_complete ;;
        4)
            clear
            echo
            echo "========================================================================"
            echo "                     Goodbye!"
            echo "========================================================================"
            echo
            sleep 2
            exit 0
            ;;
        *) continue ;;
    esac
done