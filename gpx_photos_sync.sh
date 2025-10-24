#!/bin/bash

# Script interactif pour generer GPX depuis photos et synchroniser

# Fonction pour afficher le menu principal
show_menu() {
    clear
    echo "========================================================================"
    echo "                 GESTIONNAIRE GPX - PHOTOS"
    echo "========================================================================"
    echo
    echo "  1. Generer GPX depuis photos smartphone"
    echo "  2. Synchroniser GPX vers photos Nikon (NEF)"
    echo "  3. Pipeline complet (1 + 2 automatique)"
    echo "  4. Quitter"
    echo
    echo "========================================================================"
    echo
}

# Fonction pour générer GPX depuis photos
generate_gpx() {
    clear
    echo "========================================================================"
    echo "              ETAPE 1: GENERER GPX DEPUIS PHOTOS"
    echo "========================================================================"
    echo

    echo "[1/4] Dossier contenant vos photos smartphone:"
    echo "       (Exemple: /media/Photos/Smartphones/Mobile/2023_best)"
    echo
    read -p "Chemin: " photo_source

    if [ ! -d "$photo_source" ]; then
        echo
        echo "[ERREUR] Le dossier n'existe pas!"
        read -p "Appuyez sur Entrée pour continuer..."
        return
    fi

    echo
    echo "[2/4] Dossier de destination du GPX (laissez vide = meme dossier):"
    echo "       (Exemple: /media/MesGPX ou laissez vide)"
    echo
    read -p "Chemin: " gpx_output

    if [ -z "$gpx_output" ]; then
        gpx_output="$photo_source"
    fi

    echo
    echo "[3/4] Voulez-vous anonymiser les coordonnees GPS ?"
    echo "       (Remplace coordonnees precises par centre-ville)"
    echo
    echo "  1. NON - Coordonnees exactes (defaut)"
    echo "  2. OUI - Coordonnees centre-ville (anonymise)"
    echo
    read -p "Votre choix (1-2) [1]: " anon_choice
    anon_choice=${anon_choice:-1}

    anonymize_flag=""
    [ "$anon_choice" = "2" ] && anonymize_flag="--anonymize"

    echo
    echo "========================================================================"
    echo "RESUME DE LA GENERATION GPX:"
    echo "========================================================================"
    echo "  Photos source:      $photo_source"
    echo "  Destination GPX:    $gpx_output"
    echo "  Anonymisation:      $anon_choice"
    if [ "$anon_choice" = "2" ]; then
        echo "                      (coordonnees centre-ville)"
    else
        echo "                      (coordonnees exactes)"
    fi
    echo "========================================================================"
    echo
    read -p "Appuyez sur Entrée pour lancer la generation..."

    echo
    echo "[4/4] Generation du GPX en cours..."
    echo

    if [ "$gpx_output" = "$photo_source" ]; then
        python3 photo_gps_to_gpx.py "$photo_source" $anonymize_flag
    else
        python3 photo_gps_to_gpx.py "$photo_source" "$gpx_output" $anonymize_flag
    fi

    if [ $? -ne 0 ]; then
        echo
        echo "[ERREUR] La generation du GPX a echoue!"
        read -p "Appuyez sur Entrée pour continuer..."
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
    echo "GPX GENERE AVEC SUCCES!"
    echo "========================================================================"
    echo "  Fichier: $generated_gpx"
    echo "========================================================================"
    echo
    read -p "Appuyez sur Entrée pour continuer..."
}

# Fonction pour synchroniser GPX vers photos
sync_gpx() {
    clear
    echo "========================================================================"
    echo "           ETAPE 2: SYNCHRONISER GPX VERS PHOTOS NIKON"
    echo "========================================================================"
    echo

    echo "[1/4] Dossier contenant les fichiers GPX:"
    echo "       (Exemple: /media/MesGPX)"
    echo
    read -p "Chemin: " gpx_folder

    if [ ! -d "$gpx_folder" ]; then
        echo
        echo "[ERREUR] Le dossier n'existe pas!"
        read -p "Appuyez sur Entrée pour continuer..."
        return
    fi

    echo
    echo "Recherche des fichiers GPX dans: $gpx_folder"
    echo

    # Lister les fichiers GPX disponibles
    declare -a gpx_files
    count=0
    while IFS= read -r -d '' file; do
        ((count++))
        gpx_files[$count]="$file"
        echo "  [$count] $(basename "$file")"
    done < <(find "$gpx_folder" -maxdepth 1 -name "*.gpx" -print0)

    if [ $count -eq 0 ]; then
        echo "[ERREUR] Aucun fichier GPX trouve dans ce dossier!"
        read -p "Appuyez sur Entrée pour continuer..."
        return
    fi

    echo
    echo "  [0] Entrer un chemin manuel"
    echo
    read -p "Choisissez un fichier (0-$count): " gpx_choice

    if [ "$gpx_choice" = "0" ]; then
        echo
        echo "Entrez le chemin complet du fichier GPX:"
        read -p "Chemin: " gpx_file
    else
        gpx_file="${gpx_files[$gpx_choice]}"
    fi

    if [ ! -f "$gpx_file" ]; then
        echo
        echo "[ERREUR] Le fichier GPX n'existe pas!"
        read -p "Appuyez sur Entrée pour continuer..."
        return
    fi

    echo
    echo "[2/4] Dossier contenant vos photos Nikon (NEF):"
    echo "       (Exemple: /media/Photos/NIKON/2018/juillet)"
    echo
    read -p "Chemin: " nef_folder

    if [ ! -d "$nef_folder" ]; then
        echo
        echo "[ERREUR] Le dossier n'existe pas!"
        read -p "Appuyez sur Entrée pour continuer..."
        return
    fi

    echo
    echo "[3/4] Voulez-vous creer une sauvegarde des fichiers originaux ?"
    echo "       (Recommande pour la premiere utilisation)"
    echo
    echo "  1. OUI - Creer .backup (recommande, defaut)"
    echo "  2. NON - Modifier directement"
    echo
    read -p "Votre choix (1-2) [1]: " backup_choice
    backup_choice=${backup_choice:-1}

    backup_flag=""
    [ "$backup_choice" = "1" ] && backup_flag="--backup"

    echo
    echo "[4/4] Mode de fonctionnement:"
    echo
    echo "  1. EXECUTION - Modifier reellement les fichiers (defaut)"
    echo "  2. SIMULATION (dry-run) - Tester sans modifier"
    echo
    read -p "Votre choix (1-2) [1]: " mode_choice
    mode_choice=${mode_choice:-1}

    dryrun_flag=""
    [ "$mode_choice" = "2" ] && dryrun_flag="--dry-run"

    echo
    echo "========================================================================"
    echo "RESUME DE LA SYNCHRONISATION:"
    echo "========================================================================"
    echo "  Fichier GPX:        $gpx_file"
    echo "  Photos NEF:         $nef_folder"
    echo "  Backup:             $backup_choice"
    if [ "$backup_choice" = "1" ]; then
        echo "                      (fichiers .backup crees)"
    else
        echo "                      (pas de backup)"
    fi
    echo "  Mode:               $mode_choice"
    if [ "$mode_choice" = "2" ]; then
        echo "                      (SIMULATION - aucune modification)"
    else
        echo "                      (EXECUTION - modifications reelles)"
    fi
    echo "========================================================================"
    echo

    if [ "$mode_choice" = "1" ]; then
        echo "ATTENTION: Les fichiers NEF vont etre modifies!"
        echo
    fi
    read -p "Appuyez sur Entrée pour lancer la synchronisation..."

    echo
    echo "Synchronisation en cours..."
    echo

    python3 sync_gpx_to_photos.py "$gpx_file" "$nef_folder" $backup_flag $dryrun_flag

    if [ $? -ne 0 ]; then
        echo
        echo "[ERREUR] La synchronisation a echoue!"
        read -p "Appuyez sur Entrée pour continuer..."
        return
    fi

    echo
    echo "========================================================================"
    echo "SYNCHRONISATION TERMINEE!"
    echo "========================================================================"
    if [ "$mode_choice" = "2" ]; then
        echo "  Mode: SIMULATION - Aucun fichier modifie"
    else
        echo "  Mode: EXECUTION - Fichiers mis a jour"
        if [ "$backup_choice" = "1" ]; then
            echo "  Backups: Disponibles dans $nef_folder (fichiers .backup)"
        fi
    fi
    echo "========================================================================"
    echo
    read -p "Appuyez sur Entrée pour continuer..."
}

# Fonction pour exécuter le pipeline complet
pipeline_complet() {
    clear
    echo "========================================================================"
    echo "            PIPELINE COMPLET: GENERATION + SYNCHRONISATION"
    echo "========================================================================"
    echo

    echo "----------------------------------------------------------------------"
    echo " ETAPE 1/2: GENERATION GPX"
    echo "----------------------------------------------------------------------"
    echo

    echo "[1/6] Dossier contenant vos photos smartphone:"
    echo
    read -p "Chemin: " photo_source

    if [ ! -d "$photo_source" ]; then
        echo "[ERREUR] Le dossier n'existe pas!"
        read -p "Appuyez sur Entrée pour continuer..."
        return
    fi

    echo
    echo "[2/6] Dossier de destination du GPX (laissez vide = meme dossier):"
    echo
    read -p "Chemin: " gpx_output

    if [ -z "$gpx_output" ]; then
        gpx_output="$photo_source"
    fi

    echo
    echo "[3/6] Anonymiser les coordonnees GPS ?"
    echo "  1. NON - Coordonnees exactes (defaut)"
    echo "  2. OUI - Coordonnees centre-ville"
    echo
    read -p "Choix (1-2) [1]: " anon_choice
    anon_choice=${anon_choice:-1}

    anonymize_flag=""
    [ "$anon_choice" = "2" ] && anonymize_flag="--anonymize"

    echo
    echo "----------------------------------------------------------------------"
    echo " ETAPE 2/2: SYNCHRONISATION GPX vers PHOTOS NEF"
    echo "----------------------------------------------------------------------"
    echo

    echo "[4/6] Dossier contenant vos photos Nikon (NEF):"
    echo
    read -p "Chemin: " nef_folder

    if [ ! -d "$nef_folder" ]; then
        echo "[ERREUR] Le dossier n'existe pas!"
        read -p "Appuyez sur Entrée pour continuer..."
        return
    fi

    echo
    echo "[5/6] Creer une sauvegarde des NEF ?"
    echo "  1. OUI - Creer .backup (recommande, defaut)"
    echo "  2. NON - Modifier directement"
    echo
    read -p "Choix (1-2) [1]: " backup_choice
    backup_choice=${backup_choice:-1}

    backup_flag=""
    [ "$backup_choice" = "1" ] && backup_flag="--backup"

    echo
    echo "[6/6] Mode de fonctionnement:"
    echo "  1. EXECUTION - Modifier reellement les fichiers (defaut)"
    echo "  2. SIMULATION (dry-run) - Tester sans modifier"
    echo
    read -p "Choix (1-2) [1]: " mode_choice
    mode_choice=${mode_choice:-1}

    dryrun_flag=""
    [ "$mode_choice" = "2" ] && dryrun_flag="--dry-run"

    echo
    echo "========================================================================"
    echo "RESUME DU PIPELINE COMPLET:"
    echo "========================================================================"
    echo "ETAPE 1 - GENERATION GPX:"
    echo "  Photos smartphone:  $photo_source"
    echo "  Destination GPX:    $gpx_output"
    echo "  Anonymisation:      $anon_choice"
    echo
    echo "ETAPE 2 - SYNCHRONISATION:"
    echo "  Photos NEF:         $nef_folder"
    echo "  Backup:             $backup_choice"
    echo "  Mode:               $mode_choice"
    echo "========================================================================"
    echo
    read -p "Appuyez sur Entrée pour lancer le pipeline complet..."

    echo
    echo "========================================================================"
    echo "[ETAPE 1/2] Generation du GPX..."
    echo "========================================================================"
    echo

    if [ "$gpx_output" = "$photo_source" ]; then
        python3 photo_gps_to_gpx.py "$photo_source" $anonymize_flag
    else
        python3 photo_gps_to_gpx.py "$photo_source" "$gpx_output" $anonymize_flag
    fi

    if [ $? -ne 0 ]; then
        echo
        echo "[ERREUR] La generation du GPX a echoue!"
        read -p "Appuyez sur Entrée pour continuer..."
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
    echo "GPX genere: $generated_gpx"
    sleep 2

    echo
    echo "========================================================================"
    echo "[ETAPE 2/2] Synchronisation GPX vers Photos NEF..."
    echo "========================================================================"
    echo

    python3 sync_gpx_to_photos.py "$generated_gpx" "$nef_folder" $backup_flag $dryrun_flag

    if [ $? -ne 0 ]; then
        echo
        echo "[ERREUR] La synchronisation a echoue!"
        read -p "Appuyez sur Entrée pour continuer..."
        return
    fi

    echo
    echo "========================================================================"
    echo "PIPELINE COMPLET TERMINE AVEC SUCCES!"
    echo "========================================================================"
    echo "  1. GPX genere:      $generated_gpx"
    echo "  2. Photos synchronisees dans: $nef_folder"
    if [ "$mode_choice" = "1" ]; then
        echo "  Mode: SIMULATION"
    else
        echo "  Mode: EXECUTION"
    fi
    echo "========================================================================"
    echo
    read -p "Appuyez sur Entrée pour continuer..."
}

# Boucle principale du menu
while true; do
    show_menu
    read -p "Votre choix (1-4): " choice
    case $choice in
        1) generate_gpx ;;
        2) sync_gpx ;;
        3) pipeline_complet ;;
        4)
            clear
            echo
            echo "========================================================================"
            echo "                     Au revoir!"
            echo "========================================================================"
            echo
            sleep 2
            exit 0
            ;;
        *) continue ;;
    esac
done