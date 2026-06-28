"""Step 2: reverse-geocode photos and plot them on an interactive map."""

import base64
import csv
import json
from io import BytesIO
from pathlib import Path

import folium
import pillow_heif
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from PIL import Image

pillow_heif.register_heif_opener()

ROOT_DIR = Path(__file__).resolve().parent.parent
PHOTOS_DIR = ROOT_DIR / "photos"
METADATA_CSV = ROOT_DIR / "output" / "photo_metadata.csv"
GEOCODE_CACHE_JSON = ROOT_DIR / "output" / "geocode_cache.json"
MAP_HTML = ROOT_DIR / "output" / "photo_map.html"

THUMBNAIL_WIDTH = 300
COORD_PRECISION = 4


def load_photo_rows():
    rows = []
    with open(METADATA_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row["lat"] or not row["lng"]:
                print(f"warning: skipping {row['filename']} (no GPS data)")
                continue
            row["lat"] = float(row["lat"])
            row["lng"] = float(row["lng"])
            rows.append(row)
    return rows


def load_geocode_cache():
    if GEOCODE_CACHE_JSON.exists():
        return json.loads(GEOCODE_CACHE_JSON.read_text(encoding="utf-8"))
    return {}


def save_geocode_cache(cache):
    GEOCODE_CACHE_JSON.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def coord_key(lat, lng):
    return f"{round(lat, COORD_PRECISION)},{round(lng, COORD_PRECISION)}"


def reverse_geocode_all(rows, cache):
    geolocator = Nominatim(user_agent="geophoto-game")
    reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)

    place_names = {}
    for row in rows:
        key = coord_key(row["lat"], row["lng"])
        if key not in cache:
            location = reverse((row["lat"], row["lng"]))
            cache[key] = location.address if location else "Unknown location"
        place_names[row["filename"]] = cache[key]
    return place_names


def make_thumbnail_base64(photo_path):
    with Image.open(photo_path) as image:
        image = image.convert("RGB")
        width, height = image.size
        new_height = int(height * (THUMBNAIL_WIDTH / width))
        thumbnail = image.resize((THUMBNAIL_WIDTH, new_height))

        buffer = BytesIO()
        thumbnail.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")


def build_map(rows, place_names):
    avg_lat = sum(row["lat"] for row in rows) / len(rows)
    avg_lng = sum(row["lng"] for row in rows) / len(rows)
    photo_map = folium.Map(location=[avg_lat, avg_lng])

    for row in rows:
        thumbnail_b64 = make_thumbnail_base64(PHOTOS_DIR / row["filename"])
        place_name = place_names[row["filename"]]
        popup_html = (
            f'<img src="data:image/jpeg;base64,{thumbnail_b64}" width="{THUMBNAIL_WIDTH}"><br>'
            f"<b>{place_name}</b>"
        )
        folium.Marker(
            location=[row["lat"], row["lng"]],
            popup=folium.Popup(popup_html, max_width=THUMBNAIL_WIDTH + 20),
        ).add_to(photo_map)

    photo_map.fit_bounds([[row["lat"], row["lng"]] for row in rows])
    return photo_map


def main():
    rows = load_photo_rows()
    if not rows:
        print("no photos with GPS data found, nothing to map")
        return

    cache = load_geocode_cache()
    place_names = reverse_geocode_all(rows, cache)
    save_geocode_cache(cache)

    photo_map = build_map(rows, place_names)
    photo_map.save(MAP_HTML)
    print(f"plotted {len(rows)} photos")
    print(f"wrote {MAP_HTML}")


if __name__ == "__main__":
    main()
