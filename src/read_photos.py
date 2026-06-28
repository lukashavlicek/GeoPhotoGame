"""Step 1: extract GPS + timestamp from photo EXIF into a tidy CSV."""

import csv
from pathlib import Path

import pillow_heif
from PIL import ExifTags, Image

pillow_heif.register_heif_opener()

PHOTOS_DIR = Path(__file__).resolve().parent.parent / "photos"
OUTPUT_CSV = Path(__file__).resolve().parent.parent / "output" / "photo_metadata.csv"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic"}


def _to_decimal_degrees(dms, ref):
    degrees, minutes, seconds = (float(v) for v in dms)
    decimal = degrees + minutes / 60 + seconds / 3600
    if ref in ("S", "W"):
        decimal = -decimal
    return decimal


def extract_gps(exif):
    gps_info = exif.get_ifd(ExifTags.IFD.GPSInfo)
    if not gps_info:
        return None

    gps_tags = {ExifTags.GPSTAGS.get(key, key): value for key, value in gps_info.items()}
    if "GPSLatitude" not in gps_tags or "GPSLongitude" not in gps_tags:
        return None

    lat = _to_decimal_degrees(gps_tags["GPSLatitude"], gps_tags.get("GPSLatitudeRef", "N"))
    lng = _to_decimal_degrees(gps_tags["GPSLongitude"], gps_tags.get("GPSLongitudeRef", "E"))
    return lat, lng


def extract_timestamp(exif):
    exif_tags = {ExifTags.TAGS.get(key, key): value for key, value in exif.items()}
    raw = exif_tags.get("DateTimeOriginal") or exif_tags.get("DateTime")
    if not raw:
        return None
    # EXIF format: "YYYY:MM:DD HH:MM:SS" -> ISO 8601
    date_part, time_part = raw.split(" ")
    return f"{date_part.replace(':', '-')}T{time_part}"


def read_photo_metadata(photo_path):
    row = {"filename": photo_path.name, "lat": None, "lng": None, "timestamp": None}
    try:
        with Image.open(photo_path) as image:
            exif = image.getexif()
            gps = extract_gps(exif)
            if gps:
                row["lat"], row["lng"] = gps
            row["timestamp"] = extract_timestamp(exif)
    except Exception as exc:
        print(f"warning: could not read EXIF from {photo_path.name}: {exc}")
        return row

    if gps is None:
        print(f"warning: no GPS data found in {photo_path.name}")
    if row["timestamp"] is None:
        print(f"warning: no timestamp found in {photo_path.name}")

    return row


def main():
    photo_paths = sorted(
        p for p in PHOTOS_DIR.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS
    )

    rows = [read_photo_metadata(p) for p in photo_paths]

    OUTPUT_CSV.parent.mkdir(exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "lat", "lng", "timestamp"])
        writer.writeheader()
        writer.writerows(rows)

    with_gps = sum(1 for row in rows if row["lat"] is not None)
    print(f"{len(rows)} photos found, {with_gps} with GPS, {len(rows) - with_gps} missing")
    print(f"wrote {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
