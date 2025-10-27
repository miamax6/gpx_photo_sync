#!/usr/bin/env python3
"""
Script de synchronisation GPX → Photos (RAW et JPEG)
Synchronise les métadonnées GPS et de localisation d'un fichier GPX vers des photos

Fonctionnalités:
- Lit un fichier GPX (généré par photo_gps_to_gpx.py)
- Synchronise avec les photos (NEF, JPEG, etc.) par date/heure
- Ajoute GPS + Pays/État/Ville aux EXIF et IPTC des photos
- Ignore les photos > 1h d'écart avec le GPX
- Préserve les fichiers originaux (option backup)
- Compatible avec les fichiers RAW (NEF, CR2, etc.) via py3exiv2

Utilisation:
  python sync_gpx_to_photos.py fichier.gpx dossier_photos [--backup] [--dry-run]
  
Installation des dépendances:
  pip install Pillow piexif pyexiv2
  
  Note: pyexiv2 fonctionne directement sur Windows sans compilation
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET
from PIL import Image
from PIL.ExifTags import TAGS
import piexif
import pyexiv2

import tempfile, shutil, unicodedata

def needs_tempfile(path: Path) -> bool:
    """
    Retourne True si le chemin contient des caractères non-ASCII (accents, etc.)
    """
    s = str(path)
    try:
        s.encode("ascii")
        return False
    except UnicodeEncodeError:
        return True

# Seuil de temps maximum pour synchronisation (en secondes)
MAX_TIME_DIFF_SECONDS = 3600  # 1 heure

class GPXPoint:
    """Représente un point GPX avec toutes ses métadonnées"""
    
    def __init__(self, lat, lon, time, altitude=None, city=None, state=None, country=None, country_code=None):
        self.lat = lat
        self.lon = lon
        self.time = time
        self.altitude = altitude
        self.city = city
        self.state = state
        self.country = country
        self.country_code = country_code
    
    def __repr__(self):
        return f"GPXPoint({self.lat:.4f}, {self.lon:.4f}, {self.time}, {self.city}, {self.country})"

def parse_gpx(gpx_file):
    """Parse un fichier GPX et extrait tous les points avec métadonnées"""
    points = []
    
    try:
        tree = ET.parse(gpx_file)
        root = tree.getroot()
        
        # Afficher le namespace pour debug
        print(f"   🔍 Root tag: {root.tag}")
        
        # Gérer les namespaces GPX
        ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
        
        # Chercher tous les trackpoints avec et sans namespace
        trkpts = root.findall('.//gpx:trkpt', ns)
        if not trkpts:
            trkpts = root.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')
        if not trkpts:
            trkpts = root.findall('.//trkpt')
        
        print(f"   🔍 Trouvé {len(trkpts)} trackpoints bruts")
        
        for idx, trkpt in enumerate(trkpts):
            try:
                lat = float(trkpt.get('lat'))
                lon = float(trkpt.get('lon'))
            except:
                continue
            
            # Debug: afficher les enfants du premier trkpt
            if idx == 0:
                print(f"   🔍 Premier trkpt contient: {[child.tag for child in trkpt]}")
            
            # Altitude (optionnelle)
            altitude = None
            for child in trkpt:
                if 'ele' in child.tag.lower():
                    try:
                        altitude = float(child.text)
                    except:
                        pass
                    break
            
            # Temps (obligatoire pour sync) - chercher de toutes les façons possibles
            time_elem = None
            for child in trkpt:
                if 'time' in child.tag.lower():
                    time_elem = child
                    break
            
            if time_elem is None or not time_elem.text:
                if idx < 5:  # N'afficher que les 5 premiers pour pas polluer
                    print(f"   ⚠️  Point sans timestamp ignoré: {lat}, {lon}")
                continue
            
            try:
                # Parser le temps (format ISO 8601)
                time_str = time_elem.text.strip()
                # Gérer différents formats
                if time_str.endswith('Z'):
                    time_str = time_str[:-1]
                point_time = datetime.fromisoformat(time_str)
            except Exception as e:
                if idx < 5:
                    print(f"   ⚠️  Erreur parsing date '{time_elem.text}': {e}")
                continue
            
            # Description (contient ville, état, pays)
            desc_elem = None
            for child in trkpt:
                if 'desc' in child.tag.lower():
                    desc_elem = child
                    break
            
            city = None
            state = None
            country = None
            country_code = None
            
            if desc_elem is not None and desc_elem.text:
                # Format: "Ville, État, Pays (CODE)" ou "Ville, Pays (CODE)"
                desc = desc_elem.text.strip()
                
                # Extraire le code pays
                if '(' in desc and ')' in desc:
                    country_code = desc[desc.rfind('(')+1:desc.rfind(')')].strip()
                    desc = desc[:desc.rfind('(')].strip().rstrip(',').strip()
                
                # Parser ville, état, pays
                parts = [p.strip() for p in desc.split(',') if p.strip()]
                if len(parts) >= 3:
                    city, state, country = parts[0], parts[1], parts[2]
                elif len(parts) == 2:
                    city, country = parts[0], parts[1]
                elif len(parts) == 1:
                    city = parts[0]
            
            point = GPXPoint(lat, lon, point_time, altitude, city, state, country, country_code)
            points.append(point)
        
        print(f"📍 {len(points)} points GPX valides chargés depuis {gpx_file}")
        if points:
            print(f"   📅 Période: {points[0].time} → {points[-1].time}")
        return points
    
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier GPX: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def find_closest_gpx_point(photo_time, gpx_points, max_diff_seconds=MAX_TIME_DIFF_SECONDS):
    """Trouve le point GPX le plus proche d'une photo (par temps)"""
    if not photo_time:
        return None, None
    
    closest_point = None
    min_diff = float('inf')
    
    for point in gpx_points:
        diff = abs((photo_time - point.time).total_seconds())
        if diff < min_diff:
            min_diff = diff
            closest_point = point
    
    # Vérifier si la différence est acceptable
    if min_diff <= max_diff_seconds:
        return closest_point, min_diff
    else:
        return None, min_diff

def get_photo_datetime(image_path):
    """Extrait la date/heure d'une photo depuis les EXIF"""
    try:
        # Essayer avec piexif d'abord (plus fiable pour NEF)
        exif_dict = piexif.load(str(image_path))
        for tag in ["DateTimeOriginal", "DateTimeDigitized", "DateTime"]:
            if tag in piexif.ExifIFD.__dict__:
                key = piexif.ExifIFD.__dict__[tag]
                if key in exif_dict["Exif"]:
                    dt_bytes = exif_dict["Exif"][key]
                    if isinstance(dt_bytes, bytes):
                        dt_str = dt_bytes.decode(errors="ignore")
                    else:
                        dt_str = str(dt_bytes)
                    try:
                        return datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                    except:
                        pass
        
        # Sinon fallback avec Pillow
        image = Image.open(image_path)
        exif_data = image.getexif()
        if not exif_data:
            return None
        
        for key, value in exif_data.items():
            tag = TAGS.get(key, key)
            if tag in ["DateTimeOriginal", "DateTimeDigitized", "DateTime"]:
                dt_str = value.decode() if isinstance(value, bytes) else str(value)
                try:
                    return datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                except:
                    pass
        
        return None
    except Exception as e:
        print(f"   [DEBUG] Erreur lecture EXIF: {e}")
        return None

def decimal_to_dms_string(decimal, is_latitude):
    """Convertit des coordonnées décimales en format DMS string pour EXIF"""
    is_positive = decimal >= 0
    decimal = abs(decimal)
    
    degrees = int(decimal)
    minutes_decimal = (decimal - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60
    
    # Format: "deg/1 min/1 sec/100"
    dms = f"{degrees}/1 {minutes}/1 {int(seconds * 100)}/100"
    
    # Référence
    if is_latitude:
        ref = 'N' if is_positive else 'S'
    else:
        ref = 'E' if is_positive else 'W'
    
    return dms, ref

def update_photo_metadata(image_path, gpx_point, backup=True, dry_run=False):
    """Met à jour les métadonnées EXIF et IPTC d'une photo (NEF, JPEG, etc.) avec pyexiv2"""
    try:
        # Backup si demandé
        if backup and not dry_run:
            backup_path = str(image_path) + '.backup'
            if not os.path.exists(backup_path):
                shutil.copy2(image_path, backup_path)
        
        if dry_run:
            print(f"      [DRY-RUN] Modification simulée")
            return True
        
        # Vérifier si le chemin contient des accents
        if needs_tempfile(image_path):
            # Créer un fichier temporaire sans accent
            tmpdir = tempfile.mkdtemp()
            tmpfile = os.path.join(tmpdir, os.path.basename(image_path))
            shutil.copy2(image_path, tmpfile)
            work_path = tmpfile
            use_temp = True
        else:
            work_path = str(image_path)
            use_temp = False

        # Ouvrir l'image avec pyexiv2
        img = pyexiv2.Image(work_path)
        
        # === Mise à jour des tags EXIF GPS ===
        exif_dict = {}
        
        # Coordonnées GPS
        lat_dms, lat_ref = decimal_to_dms_string(gpx_point.lat, True)
        lon_dms, lon_ref = decimal_to_dms_string(gpx_point.lon, False)
        
        exif_dict['Exif.GPSInfo.GPSVersionID'] = '2 3 0 0'
        exif_dict['Exif.GPSInfo.GPSLatitude'] = lat_dms
        exif_dict['Exif.GPSInfo.GPSLatitudeRef'] = lat_ref
        exif_dict['Exif.GPSInfo.GPSLongitude'] = lon_dms
        exif_dict['Exif.GPSInfo.GPSLongitudeRef'] = lon_ref
        
        # Altitude (si disponible)
        if gpx_point.altitude is not None:
            exif_dict['Exif.GPSInfo.GPSAltitude'] = f"{int(abs(gpx_point.altitude) * 100)}/100"
            exif_dict['Exif.GPSInfo.GPSAltitudeRef'] = '0' if gpx_point.altitude >= 0 else '1'
        
        # Écrire les EXIF
        img.modify_exif(exif_dict)
        
        # === Mise à jour des tags IPTC ===
        iptc_dict = {}
        
        # City (Ville)
        if gpx_point.city:
            iptc_dict['Iptc.Application2.City'] = gpx_point.city
        
        # Province/State (État/Région)
        if gpx_point.state:
            iptc_dict['Iptc.Application2.ProvinceState'] = gpx_point.state
        
        # Country Name (Nom du pays)
        if gpx_point.country:
            iptc_dict['Iptc.Application2.CountryName'] = gpx_point.country
        
        # Country Code (Code ISO du pays)
        if gpx_point.country_code:
            iptc_dict['Iptc.Application2.CountryCode'] = gpx_point.country_code
        
        # Écrire les IPTC
        if iptc_dict:
            img.modify_iptc(iptc_dict)
        
        # Fermer et sauvegarder
        img.close()

        # Si on a utilisé un fichier temporaire, recopier le résultat
        if use_temp:
            shutil.move(work_path, image_path)
        
        print(f"      ✓ GPS et IPTC mis à jour")
        return True
    
    except Exception as e:
        print(f"      ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_photos(photos_folder, gpx_points, backup=True, dry_run=False):
    """Traite toutes les photos d'un dossier"""
    # Extensions supportées (RAW et JPEG)
    extensions = ('.nef', '.NEF', '.jpg', '.jpeg', '.JPG', '.JPEG', '.cr2', '.CR2', '.arw', '.ARW')
    
    print(f"\n🔍 Recherche de photos dans: {photos_folder}")
    
    photo_files = list(Path(photos_folder).rglob('*'))
    photo_files = [f for f in photo_files if f.suffix in extensions and '.backup' not in str(f)]
    
    print(f"   Trouvé {len(photo_files)} photos\n")
    
    stats = {
        'total': len(photo_files),
        'synced': 0,
        'skipped_no_date': 0,
        'skipped_too_far': 0,
        'errors': 0
    }
    
    for photo_path in photo_files:
        print(f"📸 {photo_path.name}")
        
        # Récupérer la date de la photo
        photo_time = get_photo_datetime(photo_path)
        
        if not photo_time:
            print(f"   ⚠️  Aucune date EXIF trouvée - IGNORÉ")
            stats['skipped_no_date'] += 1
            continue
        
        # Trouver le point GPX le plus proche
        closest_point, time_diff = find_closest_gpx_point(photo_time, gpx_points)
        
        if closest_point is None:
            print(f"   ⏱️  Écart > 1h ({time_diff/60:.1f} min) - IGNORÉ")
            stats['skipped_too_far'] += 1
            continue
        
        # Afficher les infos
        print(f"   ✓ Match trouvé (écart: {time_diff:.0f}s)")
        print(f"   📍 GPS: {closest_point.lat:.6f}, {closest_point.lon:.6f}")
        if closest_point.city or closest_point.country:
            loc_parts = []
            if closest_point.city:
                loc_parts.append(closest_point.city)
            if closest_point.state:
                loc_parts.append(closest_point.state)
            if closest_point.country:
                loc_parts.append(f"{closest_point.country} ({closest_point.country_code})")
            print(f"   🌍 Lieu: {', '.join(loc_parts)}")
        
        # Mettre à jour les métadonnées
        if update_photo_metadata(photo_path, closest_point, backup=backup, dry_run=dry_run):
            stats['synced'] += 1
        else:
            stats['errors'] += 1
        
        print()
    
    return stats

def main():
    parser = argparse.ArgumentParser(
        description='Synchronise un fichier GPX avec des photos (RAW/JPEG)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python sync_gpx_to_photos.py trace.gpx M:\\Photos\\NIKON\\2018
  python sync_gpx_to_photos.py trace.gpx M:\\Photos\\NIKON\\2018 --backup
  python sync_gpx_to_photos.py trace.gpx M:\\Photos\\NIKON\\2018 --dry-run

Installation:
  pip install Pillow piexif pyexiv2

Notes:
  - Les photos > 1h d'écart avec le GPX sont ignorées
  - Le script prend le point GPX le plus proche par date/heure
  - Option --backup crée des copies .backup des photos originales
  - Option --dry-run simule sans modifier les photos
  - Compatible avec NEF, CR2, ARW, JPEG et autres formats supportés par exiv2
  - Tags IPTC écrits: City, Province/State, Country Name, Country Code
        """
    )
    
    parser.add_argument('gpx_file', help='Fichier GPX source')
    parser.add_argument('photos_folder', help='Dossier contenant les photos à synchroniser')
    parser.add_argument('--backup', action='store_true', help='Créer une sauvegarde des photos originales')
    parser.add_argument('--dry-run', action='store_true', help='Simuler sans modifier les photos')
    
    args = parser.parse_args()
    
    # Vérifications
    if not os.path.exists(args.gpx_file):
        print(f"❌ Erreur: Le fichier GPX '{args.gpx_file}' n'existe pas")
        sys.exit(1)
    
    if not os.path.exists(args.photos_folder):
        print(f"❌ Erreur: Le dossier '{args.photos_folder}' n'existe pas")
        sys.exit(1)
    
    print("=" * 70)
    print("📷 SYNC GPX → PHOTOS (RAW/JPEG)")
    if args.dry_run:
        print("🔍 MODE DRY-RUN (simulation)")
    if args.backup:
        print("💾 MODE BACKUP activé")
    print("=" * 70)
    
    # Charger le GPX
    gpx_points = parse_gpx(args.gpx_file)
    
    if not gpx_points:
        print("❌ Aucun point GPX trouvé dans le fichier")
        sys.exit(1)
    
    # Traiter les photos
    stats = process_photos(args.photos_folder, gpx_points, backup=args.backup, dry_run=args.dry_run)
    
    # Afficher le résumé
    print("=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    print(f"Total photos:           {stats['total']}")
    print(f"✅ Synchronisées:       {stats['synced']}")
    print(f"⏱️  Ignorées (> 1h):     {stats['skipped_too_far']}")
    print(f"⚠️  Ignorées (pas date): {stats['skipped_no_date']}")
    print(f"❌ Erreurs:              {stats['errors']}")
    print()
    
    if args.dry_run:
        print("ℹ️  Mode dry-run: Aucune photo n'a été modifiée")
    elif stats['synced'] > 0:
        print("🎉 Synchronisation terminée!")
        if args.backup:
            print("💾 Les fichiers .backup contiennent les originaux")
    
    print()

if __name__ == '__main__':
    main()