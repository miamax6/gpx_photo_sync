- [English 🇬🇧](#%EF%B8%8F-photo-gps-sync---automatic-photo-geotagging)
- [Français 🇫🇷](#%EF%B8%8F-photo-gps-sync---géotaggage-automatique-de-photos)
___

# 📸🗺️ GPX PHOTO SYNC - Automatic Photo Geotagging

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

If you want to buy me a beer or a coffee for the time invested 😉🙏 www.paypal.me/miamax
____

# 📸🗺️ GPX PHOTO SYNC - Géotaggage automatique de photos

Solution complète pour générer des traces GPX depuis vos photos smartphone et synchroniser automatiquement les données GPS et de localisation vers vos photos RAW (Nikon NEF, Canon CR2, Sony ARW) ou JPEG.

## ✨ Fonctionnalités

### 📍 Génération de traces GPX (`photo_gps_to_gpx.py`)
- **Extraction GPS** : Lit les coordonnées GPS depuis les métadonnées EXIF de vos photos
- **Géocodage inverse automatique** : Récupère automatiquement ville, région, pays et code pays via OpenStreetMap
- **Cache intelligent** : Système de cache performant pour accélérer les traitements répétés (jusqu'à 200x plus rapide)
- **Anonymisation** : Option pour remplacer les coordonnées précises par celles du centre-ville (protection vie privée)
- **Versioning automatique** : Génère des fichiers avec versioning pour éviter les écrasements
- **Support multi-plateforme** : Windows, Linux, macOS
- **Gestion d'erreurs robuste** : Retry automatique, fallback intelligent

### 🔄 Synchronisation GPX vers photos (`sync_gpx_to_photos.py`)
- **Synchronisation temporelle** : Match automatique des photos avec les points GPX par date/heure
- **Support RAW** : Compatible NEF (Nikon), CR2 (Canon), ARW (Sony), JPEG et autres formats
- **Écriture EXIF + IPTC** : Écrit les coordonnées GPS et les tags IPTC (City, State, Country, Country Code)
- **Backup automatique** : Option pour créer des copies de sauvegarde avant modification
- **Mode dry-run** : Tester sans modifier les fichiers
- **Filtrage intelligent** : Ignore les photos > 1h d'écart avec le GPX
- **Gestion des accents** : Support complet des chemins avec caractères spéciaux

### 🎮 Interface interactive (`gpx_sync_interactive.bat`)
- **Menu intuitif** : Interface en ligne de commande guidée
- **Pipeline complet** : Option pour enchaîner génération + synchronisation automatiquement
- **Sélection de fichiers** : Liste et choix interactif des fichiers GPX
- **Valeurs par défaut** : Configuration optimale préconfigurée (appuyez juste sur Entrée)

## 🚀 Installation

### Prérequis
- **Python 3.7+** : [Télécharger Python](https://www.python.org/downloads/)
- **Windows, Linux ou macOS**

### Installation automatique (Windows)

Double-cliquez sur `install_dependencies.bat` ou exécutez :

```batch
install_dependencies.bat
```

### Installation manuelle

```bash
pip install -r requirements.txt
```

ou

```bash
pip install Pillow piexif requests pyexiv2
```

## 📖 Utilisation

### Option 1 : Interface interactive (recommandé)

Double-cliquez sur `gpx_sync_interactive.bat` et laissez-vous guider !

Le script propose 3 options :
1. **Générer GPX depuis photos smartphone**
2. **Synchroniser GPX vers photos Nikon (NEF)**
3. **Pipeline complet** (1 + 2 automatique)

### Option 2 : Ligne de commande

#### Générer un fichier GPX depuis des photos

```bash
# Basique
python photo_gps_to_gpx.py "F:\Photos\Smartphone\2023"

# Avec destination personnalisée
python photo_gps_to_gpx.py "F:\Photos\Smartphone\2023" "E:\MesGPX"

# Avec anonymisation (coordonnées centre-ville)
python photo_gps_to_gpx.py "F:\Photos\Smartphone\2023" --anonymize
```

#### Synchroniser un GPX vers des photos

```bash
# Basique
python sync_gpx_to_photos.py trace_gps_2023.gpx "M:\Photos\NIKON\2023"

# Avec backup des originaux (recommandé)
python sync_gpx_to_photos.py trace_gps_2023.gpx "M:\Photos\NIKON\2023" --backup

# Mode test (dry-run)
python sync_gpx_to_photos.py trace_gps_2023.gpx "M:\Photos\NIKON\2023" --dry-run
```

## 🎯 Cas d'usage typique

**Situation** : Vous avez pris des photos avec votre smartphone (avec GPS) et votre appareil photo Nikon (sans GPS) lors d'un voyage.

**Solution** :

1. **Génération du GPX** depuis vos photos smartphone :
   ```bash
   python photo_gps_to_gpx.py "F:\Photos\Smartphone\Voyage_Italie_2023"
   ```
   → Crée `trace_gps_Voyage_Italie_2023.gpx` avec coordonnées GPS + lieux (villes, pays)

2. **Synchronisation** vers vos photos Nikon :
   ```bash
   python sync_gpx_to_photos.py trace_gps_Voyage_Italie_2023.gpx "M:\Photos\NIKON\Voyage_Italie_2023" --backup
   ```
   → Vos photos NEF contiennent maintenant les GPS + métadonnées de localisation !

3. **Visualisation** : Ouvrez vos photos dans GeoSetter, Lightroom, ou tout logiciel compatible EXIF/IPTC.

## 🔧 Configuration avancée

### Cache de géocodage

Le fichier `geocoding_cache.json` stocke les résultats de géocodage inverse. 

- **Emplacement** : À côté du script `photo_gps_to_gpx.py`
- **Persistant** : Réutilisé entre les sessions
- **Multi-instance** : Verrouillage de fichier pour exécution parallèle sécurisée
- **Gain de performance** : Jusqu'à 99%+ de cache hit sur zones déjà visitées

### Seuil de synchronisation

Par défaut, les photos avec > 1h d'écart sont ignorées. Pour modifier :

Éditez `sync_gpx_to_photos.py` ligne 30 :
```python
MAX_TIME_DIFF_SECONDS = 3600  # Changer la valeur (en secondes)
```

### Anonymisation

L'option `--anonymize` remplace les coordonnées GPS précises par celles du centre de la ville correspondante.

**Utile pour** :
- Protection de la vie privée (ne pas révéler votre adresse exacte)
- Photos partagées publiquement
- Réseaux sociaux

## 📁 Structure des fichiers

```
photo-gps-sync/
├── photo_gps_to_gpx.py           # Script génération GPX
├── sync_gpx_to_photos.py         # Script synchronisation
├── gpx_sync_interactive.bat      # Interface interactive Windows
├── install_dependencies.bat      # Installation automatique (Windows)
├── requirements.txt              # Dépendances Python
├── README.md                     # Ce fichier
└── geocoding_cache.json          # Cache (créé automatiquement)
```

## 🛠️ Dépannage

### "Aucune date EXIF trouvée"

Les fichiers NEF peuvent parfois avoir des métadonnées dans des tags non-standard. Le script essaie plusieurs méthodes de lecture. Si le problème persiste, vérifiez que vos photos ont bien une date avec un autre logiciel (ExifTool, GeoSetter).

### "Erreur pyexiv2 avec chemins accentués"

Le script gère automatiquement les chemins avec accents en utilisant des fichiers temporaires. Si vous rencontrez des problèmes, évitez les chemins avec caractères spéciaux.

### "Le cache ne fonctionne pas en parallèle"

Le système de verrouillage de fichier gère automatiquement les exécutions parallèles. Si deux instances tournent simultanément, l'une attend que l'autre ait fini d'écrire le cache.

### Performance lente

**Première exécution** : ~1-1.5 sec/photo (géocodage API)
**Exécutions suivantes** : ~0.01 sec/photo (cache)

Si c'est lent :
- Vérifiez votre connexion internet
- Le cache est-il correctement chargé ? (message au démarrage)
- Trop de photos dans des zones jamais visitées = beaucoup de requêtes API

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

## 📄 Licence

MIT License - Vous êtes libre d'utiliser, modifier et distribuer ce code.

## 🙏 Remerciements

- **OpenStreetMap Nominatim** pour le géocodage inverse gratuit
- **Pillow** pour le traitement d'images
- **pyexiv2** pour la gestion des métadonnées RAW
- **piexif** pour la lecture EXIF robuste

## 📞 Support

Pour toute question ou problème :
- Ouvrez une **issue** sur GitHub
- Consultez les exemples dans ce README

## 🗺️ Roadmap

- [ ] Support XMP sidecar comme alternative
- [ ] Interface graphique (GUI)
- [ ] Support GPX avec waypoints
- [ ] Export vers Google Earth KML
- [ ] Batch processing optimisé
- [ ] Application mobile Android/iOS

---

⭐ **Si ce projet vous a été utile, n'hésitez pas à lui donner une étoile !** ⭐

Si voulez me payer une bière ou un café pour le temps investi 😉🙏 www.paypal.me/miamax