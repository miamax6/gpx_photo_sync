#!/usr/bin/env python3
"""
Script OPTIMISÉ pour créer un fichier GPX avec localisation à partir de photos géolocalisées
Sans modifier les photos originales !

OPTIMISATIONS:
- Cache intelligent pour coordonnées proches
- Regroupement des requêtes par zones
- Sauvegarde du cache entre sessions
- Traitement par lot
- Option d'anonymisation des coordonnées GPS

Utilisation: 
  python photo_gps_to_gpx.py chemin/vers/dossier/photos [dossier_destination_gpx] [--anonymize]
  
Options:
  --anonymize, -a : Remplace les coordonnées précises par celles du centre-ville
"""

import os
import sys
import json
import math
import argparse
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import requests
import time
from xml.dom import minidom
import platform

# Import conditionnel selon la plateforme
if platform.system() != 'Windows':
    import fcntl
else:
    import msvcrt

# Configuration du cache
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(SCRIPT_DIR, 'geocoding_cache.json')
CACHE_RADIUS_KM = 5  # Rayon de recherche dans le cache (en km)

class GeocodingCache:
    """Gestion du cache de géocodage avec persistance et verrouillage"""
    
    def __init__(self, cache_file=CACHE_FILE):
        self.cache_file = cache_file
        self.lock_file = cache_file + '.lock'
        self.cache = self.load_cache()
        self.hits = 0
        self.misses = 0
    
    def _acquire_lock(self, file_handle, timeout=30):
        """Acquiert un verrou sur le fichier (multi-plateforme)"""
        is_windows = platform.system() == 'Windows'
        start_time = time.time()
        
        while True:
            try:
                if is_windows:
                    # Windows: utiliser msvcrt
                    msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    # Linux/Mac: utiliser fcntl
                    import fcntl
                    fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except (IOError, OSError):
                if time.time() - start_time > timeout:
                    print(f"⚠️  Timeout lors de l'acquisition du verrou (cache utilisé par une autre instance)")
                    return False
                time.sleep(0.1)
    
    def _release_lock(self, file_handle):
        """Libère le verrou sur le fichier (multi-plateforme)"""
        is_windows = platform.system() == 'Windows'
        try:
            if is_windows:
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        except:
            pass
    
    def load_cache(self):
        """Charge le cache depuis le fichier avec verrouillage"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r+', encoding='utf-8') as f:
                    if self._acquire_lock(f):
                        try:
                            data = json.load(f)
                            print(f"📂 Cache chargé: {self.cache_file}")
                            return data
                        finally:
                            self._release_lock(f)
                    else:
                        # Si on ne peut pas verrouiller, charger quand même (lecture seule)
                        f.seek(0)
                        return json.load(f)
            except Exception as e:
                print(f"⚠️  Erreur lors du chargement du cache: {e}")
                return {}
        return {}
    
    def save_cache(self):
        """Sauvegarde le cache dans le fichier avec verrouillage"""
        try:
            # Créer le fichier s'il n'existe pas
            mode = 'r+' if os.path.exists(self.cache_file) else 'w+'
            
            with open(self.cache_file, mode, encoding='utf-8') as f:
                if self._acquire_lock(f, timeout=60):
                    try:
                        # Recharger le cache au cas où il aurait été modifié par une autre instance
                        if mode == 'r+':
                            f.seek(0)
                            try:
                                existing_cache = json.load(f)
                                # Fusionner avec notre cache
                                existing_cache.update(self.cache)
                                self.cache = existing_cache
                            except:
                                pass
                        
                        # Écrire le cache mis à jour
                        f.seek(0)
                        f.truncate()
                        json.dump(self.cache, f, ensure_ascii=False, indent=2)
                        f.flush()
                        os.fsync(f.fileno())
                        print(f"💾 Cache sauvegardé: {len(self.cache)} entrées")
                    finally:
                        self._release_lock(f)
                else:
                    print(f"⚠️  Impossible de sauvegarder le cache (verrouillé par une autre instance)")
        except Exception as e:
            print(f"⚠️  Erreur lors de la sauvegarde du cache: {e}")
    
    def distance(self, lat1, lon1, lat2, lon2):
        """Calcule la distance entre deux points GPS (en km)"""
        R = 6371  # Rayon de la Terre en km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def find_nearby(self, lat, lon, radius_km=CACHE_RADIUS_KM):
        """Trouve une entrée du cache proche des coordonnées"""
        for key, value in self.cache.items():
            cache_lat, cache_lon = map(float, key.split(','))
            if self.distance(lat, lon, cache_lat, cache_lon) <= radius_km:
                self.hits += 1
                # Retourner une copie pour éviter les modifications du cache
                return value.copy()
        self.misses += 1
        return None
    
    def add(self, lat, lon, location_data):
        """Ajoute une entrée au cache"""
        key = f"{lat:.6f},{lon:.6f}"
        self.cache[key] = location_data
    
    def get_stats(self):
        """Retourne les statistiques du cache"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return f"Cache: {self.hits} hits, {self.misses} misses (taux: {hit_rate:.1f}%)"

def get_exif_data(image_path):
    """Extrait les données EXIF d'une image"""
    try:
        image = Image.open(image_path)
        exif_data = {}
        info = image._getexif()
        
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                exif_data[decoded] = value
        
        return exif_data
    except Exception as e:
        return None

def get_gps_data(exif_data):
    """Extrait les données GPS des EXIF"""
    if not exif_data or 'GPSInfo' not in exif_data:
        return None
    
    gps_info = {}
    for key in exif_data['GPSInfo'].keys():
        decode = GPSTAGS.get(key, key)
        gps_info[decode] = exif_data['GPSInfo'][key]
    
    return gps_info

def convert_to_degrees(value):
    """Convertit les coordonnées GPS en degrés décimaux"""
    d, m, s = value
    return d + (m / 60.0) + (s / 3600.0)

def get_lat_lon(gps_data):
    """Récupère latitude et longitude"""
    if not gps_data:
        return None, None
    
    try:
        lat = convert_to_degrees(gps_data['GPSLatitude'])
        lon = convert_to_degrees(gps_data['GPSLongitude'])
        
        if gps_data['GPSLatitudeRef'] == 'S':
            lat = -lat
        if gps_data['GPSLongitudeRef'] == 'W':
            lon = -lon
        
        return lat, lon
    except Exception as e:
        return None, None

def get_altitude(gps_data):
    """Récupère l'altitude"""
    if not gps_data or 'GPSAltitude' not in gps_data:
        return None
    
    try:
        altitude = float(gps_data['GPSAltitude'])
        if 'GPSAltitudeRef' in gps_data and gps_data['GPSAltitudeRef'] == 1:
            altitude = -altitude
        return altitude
    except:
        return None

def get_datetime(exif_data):
    """Récupère la date/heure de prise de vue"""
    if not exif_data:
        return None
    
    for key in ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']:
        if key in exif_data:
            try:
                dt_str = exif_data[key]
                dt = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
                return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            except:
                pass
    return None

def get_city_center_coordinates(city, state, country):
    """
    Récupère les coordonnées du centre-ville pour anonymisation
    """
    # Construire la requête de recherche
    query_parts = [city]
    if state:
        query_parts.append(state)
    if country:
        query_parts.append(country)
    
    query = ', '.join(query_parts)
    
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': query,
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'PhotoGPSTracker/2.0'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            return float(data['lat']), float(data['lon'])
    except:
        pass
    
    return None, None

def reverse_geocode_single(lat, lon, zoom=18):
    """
    Géocodage inverse pour une coordonnée avec niveau de zoom
    zoom=18 : très précis (rue/quartier)
    zoom=12 : ville/région
    zoom=5 : pays/continent
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        'lat': lat,
        'lon': lon,
        'format': 'json',
        'accept-language': 'fr',
        'zoom': zoom
    }
    headers = {
        'User-Agent': 'PhotoGPSTracker/2.0'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})
            
            city = (address.get('city') or 
                   address.get('town') or 
                   address.get('village') or 
                   address.get('municipality') or 
                   address.get('county') or
                   address.get('state_district') or
                   None)
            
            state = address.get('state', '')
            country = address.get('country', '')
            country_code = address.get('country_code', '').upper()
            
            # Si pas de ville trouvée, essayer avec le type de lieu
            if not city:
                # Chercher d'autres types de lieux
                city = (address.get('suburb') or
                       address.get('neighbourhood') or
                       address.get('hamlet') or
                       address.get('locality') or
                       data.get('display_name', '').split(',')[0] if data.get('display_name') else None)
            
            return {
                'city': city,
                'state': state,
                'country': country,
                'country_code': country_code,
                'found': city is not None,
                'lat': lat,
                'lon': lon
            }
        else:
            print(f"\n      ⚠ Erreur HTTP {response.status_code}")
            return {
                'city': None,
                'state': '',
                'country': '',
                'country_code': '',
                'found': False,
                'lat': lat,
                'lon': lon
            }
    except requests.exceptions.Timeout:
        print(f"\n      ⚠ Timeout de connexion")
        return {
            'city': None,
            'state': '',
            'country': '',
            'country_code': '',
            'found': False,
            'lat': lat,
            'lon': lon
        }
    except Exception as e:
        print(f"\n      ⚠ Erreur: {e}")
        return {
            'city': None,
            'state': '',
            'country': '',
            'country_code': '',
            'found': False,
            'lat': lat,
            'lon': lon
        }

def reverse_geocode_with_fallback(lat, lon, anonymize=False):
    """
    Géocodage avec stratégie de fallback en cascade
    1. Essai précis (zoom 18)
    2. Si échec, essai ville/région (zoom 12)
    3. Si échec, essai pays (zoom 5)
    4. Si échec final, utiliser coordonnées GPS
    
    Si anonymize=True, remplace les coordonnées par celles du centre-ville
    """
    # Tentative 1 : Précis
    result = reverse_geocode_single(lat, lon, zoom=18)
    
    if result['found'] and result['city']:
        # Si mode anonymisation, récupérer les coordonnées du centre-ville
        if anonymize and result['city']:
            city_lat, city_lon = get_city_center_coordinates(
                result['city'], 
                result['state'], 
                result['country']
            )
            if city_lat and city_lon:
                result['lat'] = city_lat
                result['lon'] = city_lon
                result['anonymized'] = True
                print(f" [anonymisé]", end='', flush=True)
            time.sleep(0.5)  # Pause pour la requête supplémentaire
        return result
    
    # Tentative 2 : Zoom out (ville/région)
    print(" → Retry zoom-", end='', flush=True)
    time.sleep(0.5)  # Petit délai entre requêtes
    result = reverse_geocode_single(lat, lon, zoom=12)
    
    if result['found'] and result['city']:
        if anonymize and result['city']:
            city_lat, city_lon = get_city_center_coordinates(
                result['city'], 
                result['state'], 
                result['country']
            )
            if city_lat and city_lon:
                result['lat'] = city_lat
                result['lon'] = city_lon
                result['anonymized'] = True
                print(f" [anonymisé]", end='', flush=True)
            time.sleep(0.5)
        return result
    
    # Tentative 3 : Zoom out max (pays/région large)
    print(" → Retry zoom--", end='', flush=True)
    time.sleep(0.5)
    result = reverse_geocode_single(lat, lon, zoom=5)
    
    if result['found'] and result['city']:
        if anonymize and result['city']:
            city_lat, city_lon = get_city_center_coordinates(
                result['city'], 
                result['state'], 
                result['country']
            )
            if city_lat and city_lon:
                result['lat'] = city_lat
                result['lon'] = city_lon
                result['anonymized'] = True
                print(f" [anonymisé]", end='', flush=True)
            time.sleep(0.5)
        return result
    
    # Fallback final : coordonnées GPS
    print(" → Fallback GPS", end='', flush=True)
    return {
        'city': f"GPS {lat:.4f}, {lon:.4f}",
        'state': result.get('state', ''),
        'country': result.get('country', 'Inconnu'),
        'country_code': result.get('country_code', ''),
        'found': True,
        'lat': lat,
        'lon': lon
    }

def reverse_geocode_batch(coordinates_list, cache, anonymize=False):
    """
    Géocodage inverse optimisé par lot
    Utilise le cache et regroupe les requêtes
    """
    results = {}
    to_fetch = []
    
    # Vérifier le cache d'abord
    print(f"   🔍 Vérification du cache...")
    for item in coordinates_list:
        idx, lat, lon = item
        cached = cache.find_nearby(lat, lon)
        if cached:
            # Si mode anonymisation et que le cache contient des coordonnées non-anonymisées
            if anonymize and cached.get('city'):
                # Vérifier si les coordonnées sont déjà anonymisées (approximativement au centre-ville)
                # Si les coordonnées sont très précises, ré-anonymiser
                if 'anonymized' not in cached or not cached.get('anonymized'):
                    city_lat, city_lon = get_city_center_coordinates(
                        cached['city'], 
                        cached.get('state', ''), 
                        cached.get('country', '')
                    )
                    if city_lat and city_lon:
                        cached['lat'] = city_lat
                        cached['lon'] = city_lon
                        cached['anonymized'] = True
                        time.sleep(0.5)  # Pause pour la requête
            results[idx] = cached
        else:
            to_fetch.append((idx, lat, lon))
    
    print(f"   📊 Cache: {len(results)} hits, {len(to_fetch)} requêtes à faire")
    
    # Requêtes pour les coordonnées non-cachées
    if to_fetch:
        print(f"   🌐 Début des requêtes API...")
        if anonymize:
            print(f"   🔒 Mode anonymisation activé : coordonnées remplacées par centre-ville")
        for i, (idx, lat, lon) in enumerate(to_fetch, 1):
            print(f"   [{i}/{len(to_fetch)}] Géocodage {lat:.4f}, {lon:.4f}...", end=' ', flush=True)
            location_data = reverse_geocode_with_fallback(lat, lon, anonymize=anonymize)
            print(f"→ {location_data['city']}, {location_data['state']}, {location_data['country']}")
            results[idx] = location_data
            cache.add(lat, lon, location_data)
            
            # Pause pour respecter les limites de l'API
            if i < len(to_fetch):  # Pas de pause après la dernière requête
                time.sleep(1.1)
    
    return results

def process_photos(folder_path, cache, anonymize=False):
    """Traite toutes les photos d'un dossier (version optimisée)"""
    photo_data = []
    coordinates_to_geocode = []
    
    # Extensions supportées
    extensions = ('.jpg', '.jpeg', '.JPG', '.JPEG')
    
    print(f"🔍 Recherche de photos dans: {folder_path}")
    
    # Phase 1: Extraction des coordonnées GPS (rapide)
    print("\n📸 Phase 1: Extraction des données GPS...")
    file_list = list(Path(folder_path).rglob('*'))
    photo_files = [f for f in file_list if f.suffix in extensions]
    
    print(f"   Trouvé {len(photo_files)} photos")
    
    for idx, file_path in enumerate(photo_files):
        exif_data = get_exif_data(file_path)
        if not exif_data:
            continue
        
        gps_data = get_gps_data(exif_data)
        if not gps_data:
            continue
        
        lat, lon = get_lat_lon(gps_data)
        if lat is None or lon is None:
            continue
        
        altitude = get_altitude(gps_data)
        dt = get_datetime(exif_data)
        
        photo_data.append({
            'idx': idx,
            'filename': file_path.name,
            'lat': lat,
            'lon': lon,
            'altitude': altitude,
            'datetime': dt,
            'city': None,
            'state': None,
            'country': None,
            'country_code': None
        })
        
        coordinates_to_geocode.append((idx, lat, lon))
    
    if not photo_data:
        return []
    
    print(f"   ✓ {len(photo_data)} photos avec GPS trouvées")
    
    # Phase 2: Géocodage inverse optimisé (avec cache)
    print(f"\n🌍 Phase 2: Géocodage inverse ({len(coordinates_to_geocode)} requêtes potentielles)...")
    
    location_results = reverse_geocode_batch(coordinates_to_geocode, cache, anonymize=anonymize)
    
    # Phase 3: Association des résultats
    print("\n📋 Phase 3: Association des données...")
    for photo in photo_data:
        idx = photo['idx']
        if idx in location_results:
            loc = location_results[idx]
            photo['city'] = loc['city']
            photo['state'] = loc['state']
            photo['country'] = loc['country']
            photo['country_code'] = loc['country_code']
            # Utiliser les coordonnées anonymisées si disponibles
            if anonymize and 'lat' in loc and 'lon' in loc:
                photo['lat'] = loc['lat']
                photo['lon'] = loc['lon']
            # Affichage conditionnel selon la présence de l'état
            if loc['state']:
                print(f"   ✓ {photo['filename']}: {loc['city']}, {loc['state']}, {loc['country']}")
            else:
                print(f"   ✓ {photo['filename']}: {loc['city']}, {loc['country']}")
    
    # Tri par date
    photo_data.sort(key=lambda x: x['datetime'] if x['datetime'] else '')
    
    return photo_data

def get_versioned_filename(folder_path, base_filename):
    """
    Génère un nom de fichier versionné pour éviter d'écraser les fichiers existants
    Ex: trace_gps_avec_lieux.gpx, trace_gps_avec_lieux_v2.gpx, etc.
    """
    filepath = os.path.join(folder_path, base_filename)
    
    # Si le fichier n'existe pas, on le retourne tel quel
    if not os.path.exists(filepath):
        return filepath
    
    # Sinon, on cherche la prochaine version disponible
    base_name, extension = os.path.splitext(base_filename)
    version = 2
    
    while True:
        versioned_name = f"{base_name}_v{version}{extension}"
        versioned_path = os.path.join(folder_path, versioned_name)
        
        if not os.path.exists(versioned_path):
            print(f"ℹ️  Le fichier existe déjà, création de: {versioned_name}")
            return versioned_path
        
        version += 1

def create_gpx(photo_data, output_file):
    """Crée le fichier GPX"""
    doc = minidom.Document()
    
    # Racine GPX
    gpx = doc.createElement('gpx')
    gpx.setAttribute('version', '1.1')
    gpx.setAttribute('creator', 'Photo GPS Tracker v2.0 - Optimized')
    gpx.setAttribute('xmlns', 'http://www.topografix.com/GPX/1/1')
    gpx.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    gpx.setAttribute('xsi:schemaLocation', 
                    'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd')
    doc.appendChild(gpx)
    
    # Métadonnées
    metadata = doc.createElement('metadata')
    name = doc.createElement('name')
    name.appendChild(doc.createTextNode('Trace GPS depuis photos'))
    metadata.appendChild(name)
    
    desc = doc.createElement('desc')
    desc.appendChild(doc.createTextNode('Tracé généré automatiquement avec géolocalisation'))
    metadata.appendChild(desc)
    gpx.appendChild(metadata)
    
    # Track
    trk = doc.createElement('trk')
    trk_name = doc.createElement('name')
    trk_name.appendChild(doc.createTextNode('Mon parcours photo'))
    trk.appendChild(trk_name)
    
    trkseg = doc.createElement('trkseg')
    
    # Points de trace
    for data in photo_data:
        trkpt = doc.createElement('trkpt')
        trkpt.setAttribute('lat', str(data['lat']))
        trkpt.setAttribute('lon', str(data['lon']))
        
        if data['altitude']:
            ele = doc.createElement('ele')
            ele.appendChild(doc.createTextNode(str(data['altitude'])))
            trkpt.appendChild(ele)
        
        if data['datetime']:
            time_elem = doc.createElement('time')
            time_elem.appendChild(doc.createTextNode(data['datetime']))
            trkpt.appendChild(time_elem)
        
        name_elem = doc.createElement('name')
        name_elem.appendChild(doc.createTextNode(data['filename']))
        trkpt.appendChild(name_elem)
        
        desc_elem = doc.createElement('desc')
        # Afficher l'état seulement s'il existe et n'est pas vide
        if data['state']:
            location_text = f"{data['city']}, {data['state']}, {data['country']} ({data['country_code']})"
        else:
            location_text = f"{data['city']}, {data['country']} ({data['country_code']})"
        desc_elem.appendChild(doc.createTextNode(location_text))
        trkpt.appendChild(desc_elem)
        
        trkseg.appendChild(trkpt)
    
    trk.appendChild(trkseg)
    gpx.appendChild(trk)
    
    # Écriture du fichier
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(doc.toprettyxml(indent='  '))
    
    print(f"\n✅ Fichier GPX créé: {output_file}")
    print(f"📊 {len(photo_data)} points de trace générés")

def main():
    # Parse des arguments
    parser = argparse.ArgumentParser(
        description='Génère un fichier GPX avec localisation depuis photos géolocalisées',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python photo_gps_to_gpx.py C:\\Photos\\Vacances
  python photo_gps_to_gpx.py C:\\Photos\\Vacances D:\\MesGPX
  python photo_gps_to_gpx.py C:\\Photos\\Vacances --anonymize
  python photo_gps_to_gpx.py C:\\Photos\\Vacances D:\\MesGPX -a
        """
    )
    
    parser.add_argument('folder_path', help='Dossier contenant les photos')
    parser.add_argument('output_folder', nargs='?', help='Dossier de destination du GPX (optionnel)')
    parser.add_argument('--anonymize', '-a', action='store_true', 
                       help='Remplace les coordonnées précises par celles du centre-ville')
    
    args = parser.parse_args()
    
    folder_path = args.folder_path
    anonymize = args.anonymize
    
    # Dossier de destination pour le GPX (optionnel)
    if args.output_folder:
        output_folder = args.output_folder
        if not os.path.exists(output_folder):
            print(f"❌ Erreur: Le dossier de destination '{output_folder}' n'existe pas")
            sys.exit(1)
    else:
        output_folder = folder_path  # Par défaut, même dossier que les photos
    
    if not os.path.exists(folder_path):
        print(f"❌ Erreur: Le dossier '{folder_path}' n'existe pas")
        sys.exit(1)
    
    print("=" * 70)
    print("🗺️  PHOTO GPS TO GPX TRACKER v2.0 - OPTIMISÉ")
    if anonymize:
        print("🔒 MODE ANONYMISATION ACTIVÉ")
    print("=" * 70)
    
    start_time = time.time()
    
    # Initialisation du cache
    cache = GeocodingCache()
    
    # Traitement des photos
    photo_data = process_photos(folder_path, cache, anonymize=anonymize)
    
    if not photo_data:
        print("\n❌ Aucune photo avec données GPS trouvée!")
        sys.exit(1)
    
    # Sauvegarde du cache
    cache.save_cache()
    
    # Génération du GPX avec versioning
    folder_name = os.path.basename(os.path.normpath(folder_path))
    if anonymize:
        base_filename = f'trace_gps_{folder_name}_anonymized.gpx'
    else:
        base_filename = f'trace_gps_{folder_name}.gpx'
    output_file = get_versioned_filename(output_folder, base_filename)
    create_gpx(photo_data, output_file)
    
    # Statistiques finales
    elapsed = time.time() - start_time
    print(f"\n📈 Statistiques:")
    print(f"   ⏱️  Temps total: {elapsed:.1f} secondes")
    print(f"   ⚡ Vitesse: {len(photo_data)/elapsed:.1f} photos/sec")
    print(f"   {cache.get_stats()}")
    
    print("\n🎉 Terminé! Vous pouvez ouvrir le fichier GPX avec:")
    print("   - Google Earth")
    print("   - https://gpx.studio/")
    print("   - QGIS")
    print("   - Garmin BaseCamp")

if __name__ == '__main__':
    main()