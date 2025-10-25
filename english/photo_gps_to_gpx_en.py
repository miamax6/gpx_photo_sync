#!/usr/bin/env python3
"""
OPTIMIZED script to create a GPX file with locations from geotagged photos
Without modifying original photos!

OPTIMIZATIONS:
- Smart cache for nearby coordinates
- Batch request grouping by zones
- Persistent cache between sessions
- Batch processing
- GPS coordinates anonymization option

Usage: 
  python photo_gps_to_gpx.py path/to/photos/folder [gpx_destination_folder] [--anonymize]
  
Options:
  --anonymize, -a : Replace exact coordinates with city center coordinates
"""

import os
import sys
import time
import math
import json
import fcntl
import msvcrt
import platform
import argparse
import requests
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import unicodedata
from xml.dom import minidom
import threading

# Conditional import based on platform
if platform.system() != 'Windows':
    import fcntl
else:
    import msvcrt

# Cache configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(SCRIPT_DIR, 'geocoding_cache.json')
CACHE_RADIUS_KM = 5  # Cache search radius (in km)

class GeocodingCache:
    """Geocoding cache management with persistence and locking"""
    
    def __init__(self, cache_file=CACHE_FILE):
        self.cache_file = cache_file
        self.lock_file = cache_file + '.lock'
        self.cache = self.load_cache()
        self.hits = 0
        self.misses = 0
    
    def _acquire_lock(self, file_handle, timeout=30):
        """Acquires a file lock (cross-platform)"""
        is_windows = platform.system() == 'Windows'
        start_time = time.time()
        
        while True:
            try:
                if is_windows:
                    msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except (IOError, OSError):
                if time.time() - start_time > timeout:
                    print(f"⚠️  Lock timeout after {timeout}s")
                    return False
                time.sleep(0.1)
    
    def _release_lock(self, file_handle):
        """Releases the file lock (cross-platform)"""
        is_windows = platform.system() == 'Windows'
        try:
            if is_windows:
                msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
        except:
            pass
    
    def load_cache(self):
        """Loads cache from file with locking"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    if self._acquire_lock(f):
                        try:
                            cache_data = json.load(f)
                            print(f"   📂 Cache loaded: {len(cache_data)} entries")
                            return cache_data
                        except json.JSONDecodeError:
                            print("⚠️  Cache file corrupted, starting fresh")
                        finally:
                            self._release_lock(f)
                    else:
                        print("⚠️  Could not acquire cache lock, starting fresh")
            except Exception as e:
                print(f"⚠️  Cache loading error: {e}")
        
        return {}
    
    def save_cache(self):
        """Saves cache to file with locking"""
        try:
            # Create file if it doesn't exist
            mode = 'r+' if os.path.exists(self.cache_file) else 'w+'
            
            with open(self.cache_file, mode, encoding='utf-8') as f:
                if self._acquire_lock(f):
                    try:
                        f.seek(0)
                        json.dump(self.cache, f, indent=2)
                        f.truncate()
                    finally:
                        self._release_lock(f)
                else:
                    print("⚠️  Could not acquire lock for saving cache")
        except Exception as e:
            print(f"⚠️  Cache saving error: {e}")
    
    def distance(self, lat1, lon1, lat2, lon2):
        """Calculates distance between two GPS points (in km)"""
        R = 6371  # Earth radius in km
        
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
        """Finds a cache entry near coordinates"""
        for key, value in self.cache.items():
            cache_lat, cache_lon = map(float, key.split(','))
            if self.distance(lat, lon, cache_lat, cache_lon) <= radius_km:
                self.hits += 1
                return value
        
        self.misses += 1
        return None
    
    def add(self, lat, lon, location_data):
        """Adds an entry to cache"""
        key = f"{lat:.6f},{lon:.6f}"
        self.cache[key] = location_data
    
    def get_stats(self):
        """Returns cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return f"Cache: {self.hits} hits, {self.misses} misses (rate: {hit_rate:.1f}%)"

def get_exif_data(image_path):
    """Extracts EXIF data from an image"""
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
    """Extracts GPS data from EXIF"""
    if not exif_data or 'GPSInfo' not in exif_data:
        return None
    
    gps_info = {}
    for key in exif_data['GPSInfo'].keys():
        decode = GPSTAGS.get(key, key)
        gps_info[decode] = exif_data['GPSInfo'][key]
    
    return gps_info

def convert_to_degrees(value):
    """Converts GPS coordinates to decimal degrees"""
    d, m, s = value
    return d + (m / 60.0) + (s / 3600.0)

def get_lat_lon(gps_data):
    """Gets latitude and longitude"""
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
    """Gets altitude"""
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
    """Gets photo capture date/time"""
    if not exif_data:
        return None
    
    for key in ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']:
        if key in exif_data:
            try:
                return datetime.strptime(str(exif_data[key]), '%Y:%m:%d %H:%M:%S')
            except:
                continue
    return None

def get_city_center_coordinates(city, state, country):
    """
    Gets city center coordinates for anonymization
    """
    # Build search query
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
    Reverse geocoding for coordinates with zoom level
    zoom=18: very precise (street/area)
    zoom=12: city/region
    zoom=5: country/continent
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        'lat': lat,
        'lon': lon,
        'format': 'json',
        'accept-language': 'en',  # English results
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
            
            # If no city found, try with place type
            if not city:
                place_type = next((k for k in ['city', 'town', 'village', 
                                             'municipality', 'county', 'state_district']
                                 if k in address), None)
                if place_type:
                    city = address[place_type]
            
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
            print(f"\n      ⚠ HTTP Error {response.status_code}")

    except requests.exceptions.Timeout:
        print(f"\n      ⚠ Connection timeout")
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
        print(f"\n      ⚠ Error: {e}")
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
    Geocoding with cascading fallback strategy
    1. Try precise (zoom 18)
    2. If fails, try city/region (zoom 12)
    3. If fails, try country (zoom 5)
    4. Final fallback: use GPS coordinates
    
    If anonymize=True, replace coordinates with city center
    """
    # Attempt 1: Precise
    result = reverse_geocode_single(lat, lon, zoom=18)
    
    if result['found'] and result['city']:
        # If anonymization mode, get city center coordinates
        if anonymize and result['city']:
            print(" → Anonymizing", end='', flush=True)
            city_lat, city_lon = get_city_center_coordinates(
                result['city'], result['state'], result['country']
            )
            if city_lat and city_lon:
                result['lat'] = city_lat
                result['lon'] = city_lon
                print(" ✓", end='', flush=True)
            else:
                print(" ❌", end='', flush=True)
        return result
    
    # Attempt 2: Zoom out (city/region)
    print(" → Retry zoom-", end='', flush=True)
    time.sleep(0.5)  # Small delay between requests
    result = reverse_geocode_single(lat, lon, zoom=12)
    
    if result['found'] and result['city']:
        if anonymize and result['city']:
            print(" → Anonymizing", end='', flush=True)
            city_lat, city_lon = get_city_center_coordinates(
                result['city'], result['state'], result['country']
            )
            if city_lat and city_lon:
                result['lat'] = city_lat
                result['lon'] = city_lon
                print(" ✓", end='', flush=True)
            else:
                print(" ❌", end='', flush=True)
        return result
    
    # Attempt 3: Max zoom out (country/wide region)
    print(" → Retry zoom--", end='', flush=True)
    time.sleep(0.5)
    result = reverse_geocode_single(lat, lon, zoom=5)
    
    if result['found'] and result['city']:
        if anonymize and result['city']:
            print(" → Anonymizing", end='', flush=True)
            city_lat, city_lon = get_city_center_coordinates(
                result['city'], result['state'], result['country']
            )
            if city_lat and city_lon:
                result['lat'] = city_lat
                result['lon'] = city_lon
                print(" ✓", end='', flush=True)
            else:
                print(" ❌", end='', flush=True)
        return result
    
    # Final fallback: GPS coordinates
    print(" → GPS fallback", end='', flush=True)
    return {
        'city': f"GPS {lat:.4f}, {lon:.4f}",
        'state': result.get('state', ''),
        'country': result.get('country', 'Unknown'),
        'country_code': result.get('country_code', ''),
        'found': True,
        'lat': lat,
        'lon': lon
    }

def reverse_geocode_batch(coordinates_list, cache, anonymize=False):
    """
    Optimized batch reverse geocoding
    Uses cache and groups requests
    """
    results = {}
    to_fetch = []
    
    # Check cache first
    print(f"   🔍 Checking cache...")
    for item in coordinates_list:
        idx, lat, lon = item
        cached = cache.find_nearby(lat, lon)
        if cached:
            # If anonymization requested and we have city info
            if anonymize and cached['city'] and not cached.get('anonymized'):
                city_lat, city_lon = get_city_center_coordinates(
                    cached['city'], cached['state'], cached['country']
                )
                if city_lat and city_lon:
                    cached['lat'] = city_lat
                    cached['lon'] = city_lon
                    cached['anonymized'] = True
            results[idx] = cached
        else:
            to_fetch.append(item)
    
    print(f"   📊 Cache: {len(results)} hits, {len(to_fetch)} requests needed")
    
    # Requests for non-cached coordinates
    if to_fetch:
        print(f"   🌐 Starting API requests...")
        if anonymize:
            print("   🔒 Anonymization mode active")
        for i, (idx, lat, lon) in enumerate(to_fetch, 1):
            print(f"   [{i}/{len(to_fetch)}] {lat:.4f}, {lon:.4f}", end='', flush=True)
            result = reverse_geocode_with_fallback(lat, lon, anonymize=anonymize)
            print()  # New line
            
            results[idx] = result
            cache.add(lat, lon, result)
            
            # Rate limiting
            if i < len(to_fetch):
                time.sleep(1)
    
    return results

def process_photos(folder_path, cache, anonymize=False):
    """Processes all photos in a folder (optimized version)"""
    photo_data = []
    coordinates_to_geocode = []
    
    # Supported extensions
    extensions = ('.jpg', '.jpeg', '.JPG', '.JPEG')
    
    print(f"🔍 Searching for photos in: {folder_path}")
    
    # Phase 1: GPS coordinates extraction (fast)
    print("\n📸 Phase 1: GPS data extraction...")
    file_list = list(Path(folder_path).rglob('*'))
    photo_files = [f for f in file_list if f.suffix in extensions]
    
    print(f"   Found {len(photo_files)} photos")
    
    for idx, file_path in enumerate(photo_files):
        exif_data = get_exif_data(file_path)
        if not exif_data:
            print(f"   ⚠️ No EXIF data: {file_path.name}")
            continue
        
        gps_data = get_gps_data(exif_data)
        if not gps_data:
            print(f"   ⚠️ No GPS data: {file_path.name}")
            continue
        
        lat, lon = get_lat_lon(gps_data)
        if lat is None or lon is None:
            print(f"   ⚠️ Invalid GPS: {file_path.name}")
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
    
    print(f"   ✓ {len(photo_data)} photos with GPS found")
    
    # Phase 2: Optimized reverse geocoding (with cache)
    print(f"\n🌍 Phase 2: Reverse geocoding ({len(coordinates_to_geocode)} potential requests)...")
    
    location_results = reverse_geocode_batch(coordinates_to_geocode, cache, anonymize=anonymize)
    
    # Phase 3: Results association
    print("\n📋 Phase 3: Data association...")
    for photo in photo_data:
        idx = photo['idx']
        if idx in location_results:
            result = location_results[idx]
            photo.update({
                'lat': result['lat'],  # Use potentially anonymized coordinates
                'lon': result['lon'],
                'city': result['city'],
                'state': result['state'],
                'country': result['country'],
                'country_code': result['country_code']
            })
    
    # Sort by date
    photo_data.sort(key=lambda x: x['datetime'] if x['datetime'] else '')
    
    return photo_data

def get_versioned_filename(folder_path, base_filename):
    """
    Generates a versioned filename to avoid overwriting
    Ex: gps_track_with_locations.gpx, gps_track_with_locations_v2.gpx, etc.
    """
    filepath = os.path.join(folder_path, base_filename)
    
    # If file doesn't exist, return as is
    if not os.path.exists(filepath):
        return filepath
    
    # Otherwise, find next available version
    base_name, extension = os.path.splitext(base_filename)
    version = 2
    
    while True:
        versioned_name = f"{base_name}_v{version}{extension}"
        versioned_path = os.path.join(folder_path, versioned_name)
        
        if not os.path.exists(versioned_path):
            return versioned_path
        
        version += 1

def create_gpx(photo_data, output_file):
    """Creates GPX file"""
    doc = minidom.Document()
    
    # GPX root
    gpx = doc.createElement('gpx')
    gpx.setAttribute('version', '1.1')
    gpx.setAttribute('creator', 'Photo GPS Tracker v2.0 - Optimized')
    gpx.setAttribute('xmlns', 'http://www.topografix.com/GPX/1/1')
    gpx.setAttribute('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    gpx.setAttribute('xsi:schemaLocation', 
                    'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd')
    doc.appendChild(gpx)
    
    # Metadata
    metadata = doc.createElement('metadata')
    name = doc.createElement('name')
    name.appendChild(doc.createTextNode('GPS Track from photos'))
    metadata.appendChild(name)
    
    desc = doc.createElement('desc')
    desc.appendChild(doc.createTextNode('Track automatically generated with geolocation'))
    metadata.appendChild(desc)
    gpx.appendChild(metadata)
    
    # Track
    trk = doc.createElement('trk')
    trk_name = doc.createElement('name')
    trk_name.appendChild(doc.createTextNode('My photo track'))
    trk.appendChild(trk_name)
    
    trkseg = doc.createElement('trkseg')
    
    # Track points
    for data in photo_data:
        trkpt = doc.createElement('trkpt')
        trkpt.setAttribute('lat', str(data['lat']))
        trkpt.setAttribute('lon', str(data['lon']))
        
        if data['altitude']:
            ele = doc.createElement('ele')
            ele.appendChild(doc.createTextNode(str(data['altitude'])))
            trkpt.appendChild(ele)
        
        if data['datetime']:
            time = doc.createElement('time')
            time.appendChild(doc.createTextNode(data['datetime'].isoformat()))
            trkpt.appendChild(time)
        
        name_elem = doc.createElement('name')
        name_elem.appendChild(doc.createTextNode(data['filename']))
        trkpt.appendChild(name_elem)
        
        desc_elem = doc.createElement('desc')
        # Show state only if it exists and isn't empty
        if data['state']:
            location_text = f"{data['city']}, {data['state']}, {data['country']} ({data['country_code']})"
        else:
            location_text = f"{data['city']}, {data['country']} ({data['country_code']})"
        desc_elem.appendChild(doc.createTextNode(location_text))
        trkpt.appendChild(desc_elem)
        
        trkseg.appendChild(trkpt)
    
    trk.appendChild(trkseg)
    gpx.appendChild(trk)
    
    # Write file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(doc.toprettyxml(indent='  '))
    
    print(f"\n✅ GPX file created: {output_file}")
    print(f"📊 {len(photo_data)} track points generated")

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Generate a GPX file with locations from geotagged photos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python photo_gps_to_gpx.py C:\\Photos\\Vacation
  python photo_gps_to_gpx.py C:\\Photos\\Vacation D:\\MyGPX
  python photo_gps_to_gpx.py C:\\Photos\\Vacation --anonymize
  python photo_gps_to_gpx.py C:\\Photos\\Vacation D:\\MyGPX -a
        """
    )
    
    parser.add_argument('folder_path', help='Folder containing photos')
    parser.add_argument('output_folder', nargs='?', help='GPX destination folder (optional)')
    parser.add_argument('--anonymize', '-a', action='store_true', 
                       help='Replace exact coordinates with city center coordinates')
    
    args = parser.parse_args()
    
    folder_path = args.folder_path
    anonymize = args.anonymize
    
    # GPX destination folder (optional)
    if args.output_folder:
        output_folder = args.output_folder
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
    else:
        output_folder = folder_path  # Default: same folder as photos
    
    if not os.path.exists(folder_path):
        print(f"❌ Error: Folder '{folder_path}' does not exist")
        sys.exit(1)
    
    print("=" * 70)
    print("🗺️  PHOTO GPS TO GPX TRACKER v2.0 - OPTIMIZED")
    if anonymize:
        print("🔒 ANONYMIZATION MODE ENABLED")
    print("=" * 70)
    
    start_time = time.time()
    
    # Cache initialization
    cache = GeocodingCache()
    
    # Process photos
    photo_data = process_photos(folder_path, cache, anonymize=anonymize)
    
    if not photo_data:
        print("\n❌ No photos with GPS data found!")
        sys.exit(1)
    
    # Save cache
    cache.save_cache()
    
    # GPX generation with versioning
    folder_name = os.path.basename(os.path.normpath(folder_path))
    if anonymize:
        base_filename = f'gps_track_{folder_name}_anonymized.gpx'
    else:
        base_filename = f'gps_track_{folder_name}.gpx'
    output_file = get_versioned_filename(output_folder, base_filename)
    create_gpx(photo_data, output_file)
    
    # Final statistics
    elapsed = time.time() - start_time
    print(f"\n📈 Statistics:")
    print(f"   ⏱️  Total time: {elapsed:.1f} seconds")
    print(f"   ⚡ Speed: {len(photo_data)/elapsed:.1f} photos/sec")
    print(f"   {cache.get_stats()}")
    
    print("\n🎉 Done! You can open the GPX file with:")
    print("   - Google Earth")
    print("   - https://gpx.studio/")
    print("   - QGIS")
    print("   - Garmin BaseCamp")

if __name__ == '__main__':
    main()