#!/bin/bash
# ============================================================================
# Script d'installation des dépendances Python
# Pour les scripts: photo_gps_to_gpx.py et sync_gpx_to_photos.py
# ============================================================================

echo "========================================================================"
echo "Installation des dependances Python"
echo "========================================================================"
echo

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python n'est pas installe"
    echo
    echo "Installez Python avec votre gestionnaire de paquets:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  Fedora: sudo dnf install python3"
    exit 1
fi

echo "[OK] Python detecte:"
python3 --version
echo

# Vérifier si pip est installé
if ! command -v pip3 &> /dev/null; then
    echo "[ERREUR] pip n'est pas installe"
    echo
    echo "Installez pip avec votre gestionnaire de paquets:"
    echo "  Ubuntu/Debian: sudo apt install python3-pip"
    echo "  Fedora: sudo dnf install python3-pip"
    exit 1
fi

# Mettre à jour pip
echo "[1/2] Mise a jour de pip..."
python3 -m pip install --upgrade pip --quiet
if [ $? -ne 0 ]; then
    echo "[ERREUR] Echec de la mise a jour de pip"
    exit 1
fi
echo "[OK] pip mis a jour"
echo

# Installer les dépendances
echo "[2/2] Installation des bibliotheques..."
echo

echo "  - Pillow (traitement d'images)..."
python3 -m pip install Pillow --quiet
if [ $? -ne 0 ]; then
    echo "[ERREUR] Echec installation Pillow"
    exit 1
fi
echo "  [OK] Pillow installe"

echo "  - piexif (lecture EXIF pour NEF)..."
python3 -m pip install piexif --quiet
if [ $? -ne 0 ]; then
    echo "[ERREUR] Echec installation piexif"
    exit 1
fi
echo "  [OK] piexif installe"

echo "  - requests (requetes HTTP)..."
python3 -m pip install requests --quiet
if [ $? -ne 0 ]; then
    echo "[ERREUR] Echec installation requests"
    exit 1
fi
echo "  [OK] requests installe"

echo "  - pyexiv2 (metadata EXIF/IPTC pour RAW)..."
python3 -m pip install pyexiv2 --quiet
if [ $? -ne 0 ]; then
    echo "[ERREUR] Echec installation pyexiv2"
    exit 1
fi
echo "  [OK] pyexiv2 installe"

echo
echo "========================================================================"
echo "Installation terminee avec succes !"
echo "========================================================================"
echo
echo "Vous pouvez maintenant utiliser:"
echo "  - photo_gps_to_gpx.py       (generer GPX depuis photos)"
echo "  - sync_gpx_to_photos.py     (synchroniser GPX vers photos)"
echo