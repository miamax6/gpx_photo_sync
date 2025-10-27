#!/bin/bash
# ============================================================================
# Python dependencies installation script
# For scripts: photo_gps_to_gpx.py and sync_gpx_to_photos.py
# ============================================================================

echo "========================================================================"
echo "Python Dependencies Installation"
echo "========================================================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python is not installed"
    echo
    echo "Install Python with your package manager:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  Fedora: sudo dnf install python3"
    exit 1
fi

echo "[OK] Python detected:"
python3 --version
echo

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "[ERROR] pip is not installed"
    echo
    echo "Install pip with your package manager:"
    echo "  Ubuntu/Debian: sudo apt install python3-pip"
    echo "  Fedora: sudo dnf install python3-pip"
    exit 1
fi

# Update pip
echo "[1/2] Updating pip..."
python3 -m pip install --upgrade pip --quiet
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to update pip"
    exit 1
fi
echo "[OK] pip updated"
echo

# Install dependencies
echo "[2/2] Installing libraries..."
echo

echo "  - Pillow (image processing)..."
python3 -m pip install Pillow --quiet
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install Pillow"
    exit 1
fi
echo "  [OK] Pillow installed"

echo "  - piexif (EXIF reading for NEF)..."
python3 -m pip install piexif --quiet
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install piexif"
    exit 1
fi
echo "  [OK] piexif installed"

echo "  - requests (HTTP requests)..."
python3 -m pip install requests --quiet
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install requests"
    exit 1
fi
echo "  [OK] requests installed"

echo "  - pyexiv2 (EXIF/IPTC metadata for RAW)..."
python3 -m pip install pyexiv2 --quiet
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install pyexiv2"
    exit 1
fi
echo "  [OK] pyexiv2 installed"

echo
echo "========================================================================"
echo "Installation completed successfully!"
echo "========================================================================"
echo
echo "You can now use:"
echo "  - photo_gps_to_gpx.py       (generate GPX from photos)"
echo "  - sync_gpx_to_photos.py     (synchronize GPX to photos)"
echo