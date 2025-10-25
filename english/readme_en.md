# 📸🗺️ Photo GPS Sync - Automatic Photo Geotagging

Complete solution to generate GPX tracks from your smartphone photos and automatically synchronize GPS and location data to your RAW photos (Nikon NEF, Canon CR2, Sony ARW) or JPEG.

## ✨ Features

### 📍 GPX Track Generation (`photo_gps_to_gpx.py`)
- **GPS Extraction**: Reads GPS coordinates from EXIF metadata in your photos
- **Automatic Reverse Geocoding**: Automatically retrieves city, region, country and country code via OpenStreetMap
- **Smart Caching**: High-performance caching system to speed up repeated processing (up to 200x faster)
- **Anonymization**: Option to replace precise coordinates with city center coordinates (privacy protection)
- **Automatic Versioning**: Generates versioned files to avoid overwrites
- **Multi-platform Support**: Windows, Linux, macOS
- **Robust Error Handling**: Automatic retry, intelligent fallback

### 🔄 GPX to Photos Synchronization (`sync_gpx_to_photos.py`)
- **Time-based Synchronization**: Automatic matching of photos with GPX points by date/time
- **RAW Support**: Compatible with NEF (Nikon), CR2 (Canon), ARW (Sony), JPEG and other formats
- **EXIF + IPTC Writing**: Writes GPS coordinates and IPTC tags (City, State, Country, Country Code)
- **Automatic Backup**: Option to create backup copies before modification
- **Dry-run Mode**: Test without modifying files
- **Smart Filtering**: Ignores photos > 1h offset from GPX
- **Accent Handling**: Full support for paths with special characters

### 🎮 Interactive Interface (`gpx_sync_interactive.bat`)
- **Intuitive Menu**: Guided command-line interface
- **Complete Pipeline**: Option to chain generation + synchronization automatically
- **File Selection**: Interactive listing and selection of GPX files
- **Default Values**: Pre-configured optimal settings (just press Enter)

## 🚀 Installation

### Prerequisites
- **Python 3.7+**: [Download Python](https://www.python.org/downloads/)
- **Windows, Linux or macOS**

### Automatic Installation (Windows)

Double-click `install_dependencies.bat` or run:

```batch
install_dependencies.bat
```

### Manual Installation

```bash
pip install -r requirements.txt
```

or

```bash
pip install Pillow piexif requests pyexiv2
```

## 📖 Usage

### Option 1: Interactive Interface (recommended for beginners)

Double-click `gpx_sync_interactive.bat` and follow the guide!

The script offers 3 options:
1. **Generate GPX from smartphone photos**
2. **Synchronize GPX to Nikon photos (NEF)**
3. **Complete Pipeline** (1 + 2 automatic)

### Option 2: Command Line

#### Generate a GPX file from photos

```bash
# Basic
python photo_gps_to_gpx.py "F:\Photos\Smartphone\2023"

# With custom destination
python photo_gps_to_gpx.py "F:\Photos\Smartphone\2023" "E:\MyGPX"

# With anonymization (city center coordinates)
python photo_gps_to_gpx.py "F:\Photos\Smartphone\2023" --anonymize
```

#### Synchronize a GPX to photos

```bash
# Basic
python sync_gpx_to_photos.py trace_gps_2023.gpx "M:\Photos\NIKON\2023"

# With backup of originals (recommended)
python sync_gpx_to_photos.py trace_gps_2023.gpx "M:\Photos\NIKON\2023" --backup

# Test mode (dry-run)
python sync_gpx_to_photos.py trace_gps_2023.gpx "M:\Photos\NIKON\2023" --dry-run
```

## 🎯 Typical Use Case

**Situation**: You took photos with your smartphone (with GPS) and your Nikon camera (without GPS) during a trip.

**Solution**:

1. **Generate GPX** from your smartphone photos:
   ```bash
   python photo_gps_to_gpx.py "F:\Photos\Smartphone\Italy_Trip_2023"
   ```
   → Creates `trace_gps_Italy_Trip_2023.gpx` with GPS coordinates + locations (cities, countries)

2. **Synchronize** to your Nikon photos:
   ```bash
   python sync_gpx_to_photos.py trace_gps_Italy_Trip_2023.gpx "M:\Photos\NIKON\Italy_Trip_2023" --backup
   ```
   → Your NEF photos now contain GPS + location metadata!

3. **Visualization**: Open your photos in GeoSetter, Lightroom, or any EXIF/IPTC compatible software.

## 🔧 Advanced Configuration

### Geocoding Cache

The `geocoding_cache.json` file stores reverse geocoding results.

- **Location**: Next to the `photo_gps_to_gpx.py` script
- **Persistent**: Reused between sessions
- **Multi-instance**: File locking for secure parallel execution
- **Performance Gain**: Up to 99%+ cache hit rate on previously visited areas

### Synchronization Threshold

By default, photos with > 1h offset are ignored. To modify:

Edit `sync_gpx_to_photos.py` line 30:
```python
MAX_TIME_DIFF_SECONDS = 3600  # Change the value (in seconds)
```

### Anonymization

The `--anonymize` option replaces precise GPS coordinates with the corresponding city center coordinates.

**Useful for**:
- Privacy protection (don't reveal your exact address)
- Publicly shared photos
- Social media

## 📁 File Structure

```
photo-gps-sync/
├── photo_gps_to_gpx.py           # GPX generation script
├── sync_gpx_to_photos.py         # Synchronization script
├── gpx_sync_interactive.bat      # Interactive Windows interface
├── install_dependencies.bat      # Automatic installation (Windows)
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── geocoding_cache.json          # Cache (created automatically)
```

## 🛠️ Troubleshooting

### "No EXIF date found"

NEF files can sometimes have metadata in non-standard tags. The script tries multiple reading methods. If the problem persists, verify that your photos have a date with another software (ExifTool, GeoSetter).

### "pyexiv2 error with accented paths"

The script automatically handles paths with accents using temporary files. If you encounter issues, avoid paths with special characters.

### "Cache doesn't work in parallel"

The file locking system automatically handles parallel executions. If two instances run simultaneously, one waits for the other to finish writing the cache.

### Slow Performance

**First execution**: ~1-1.5 sec/photo (API geocoding)
**Subsequent executions**: ~0.01 sec/photo (cache)

If it's slow:
- Check your internet connection
- Is the cache properly loaded? (message at startup)
- Too many photos in never-visited areas = many API requests

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Propose improvements
- Submit pull requests

## 📄 License

MIT License - You are free to use, modify and distribute this code.

## 🙏 Acknowledgments

- **OpenStreetMap Nominatim** for free reverse geocoding
- **Pillow** for image processing
- **pyexiv2** for RAW metadata management
- **piexif** for robust EXIF reading

## 📞 Support

For any questions or issues:
- Open an **issue** on GitHub
- Refer to the examples in this README

## 🗺️ Roadmap

- [ ] XMP sidecar support as alternative
- [ ] Graphical User Interface (GUI)
- [ ] GPX support with waypoints
- [ ] Export to Google Earth KML
- [ ] Optimized batch processing
- [ ] Android/iOS mobile application

---

⭐ **If this project was useful to you, don't hesitate to give it a star!** ⭐