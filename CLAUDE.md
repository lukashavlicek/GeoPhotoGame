# Summer 2026 Memory Book — Project Anchor

> Single source of truth for this project. Saved as `CLAUDE.md` so Claude Code
> loads it automatically each session; a copy lives in the Claude Project
> knowledge so chat sessions share the same context. Update the **Decisions log**
> whenever a real choice is made — capture the *why*, not just the *what*.

---

## 1. What this is

A personal family project built around a 3-week summer holiday in **Póvoa de
Varzim**, near Porto, Portugal. We walk the town, beach and city park over the
three weeks, slowly completing small location-based tasks and photographing
each one. The result becomes a keepsake of the holiday.

It is also a deliberate **learning project**: the goal is to pick up real
geolocation / geodata skills (building on an existing SQL/data background) by
making something genuinely useful rather than doing abstract exercises.

**Players:** the parents run the game; the two ~2.5-year-old boys take part
naturally but don't operate phones or understand the "game" yet. The app is a
tool for the adults; the kids just have fun.

---

## 2. End product (locked)

A physical **"Summer 2026" memory book** the boys can flip through:

- Opens with the **photo-map** — a map of Póvoa with a pin for every task,
  showing where each photo was taken.
- Followed by **per-task pages** — each task with its photo(s) and a caption.

Plus a **digital twin**: an interactive, shareable photo-map (click a pin → see
the photo) generated from the same data.

Both outputs come from one clean dataset (see decision D6).

---

## 3. Architecture — two phases

The project splits into two halves that hand off through the photos:

**Phase 1 — Field app** (used on the phone during the holiday)
A web page showing a map of Póvoa with task pins, your live location, and a
checklist. You complete tasks in any order, shoot photos with the **native
camera**, and tick tasks off. Produces a small **completion log**.

**Phase 2 — Album generator** (Python, run before/after the trip)
Reads the geotagged photos, extracts their GPS, names the places, matches each
photo to a task, and renders both the interactive map and the print-ready book.

**Handoff:** the photos (carrying GPS + timestamp) + the completion log flow
from Phase 1 into Phase 2.

> Build order: **Phase 2 first** — it can be tested today with photos from home,
> and plays to existing Python/data strengths.

---

## 4. Data model (the spine)

One **shared task list** is the backbone — defined once, consumed by both phases.

**Task list — `tasks.geojson`** (single source of truth)
Each task is a GeoJSON Point feature:
- `id` — slug, e.g. `cafe-pastel`
- `title` — e.g. "Order pastéis de nata for everyone and take a photo"
- `type` — `go-to-place` | `find-and-count` | `spot-a-detail`
- `geometry` — Point `[lng, lat]`
- optional `notes` / `hint`

**Completion log** (written by the Phase 1 app)
- `task_id`
- `timestamp` (ISO)
- `location` (lat/lng at the moment of check-off) — optional, helps matching

**Photo record** (derived in Phase 2)
- `path` / filename
- `lat`, `lng` (from EXIF)
- `timestamp` (from EXIF)
- `place_name` (reverse-geocoded)
- `matched_task_id` (computed: nearest task, time as tie-breaker)

---

## 5. Roadmap (milestones)

**Phase 2 — album generator (start here)**
1. **Read photos + GPS.** Extract lat/lng + timestamp from photo EXIF → tidy
   table. *Testable today with local photos.*
2. **Map them.** Reverse-geocode to place names; plot photos as pins on an
   interactive Folium map with thumbnails in popups. *Testable today.*
3. **Group photos by task.** Assign each photo to its nearest task (spatial
   join; time as tie-breaker). *Can fake a few local "tasks" to test.*
4. **Build the printable book.** Static high-res map page + per-task photo pages
   → print-ready PDF.

**Phase 1 — field app (build as the trip approaches)**
5. **Static task map.** Web page showing Póvoa with task pins from `tasks.geojson`.
6. **"You are here" + nearby tasks.** Add browser Geolocation; highlight nearby tasks.
7. **Check off + record.** Tap a task → mark done → write the completion log.

**Assembly (during/after the holiday)**
8. **Play it.** Walk, shoot with native camera, tick off tasks over 3 weeks.
9. **Generate.** Photos + completion log → interactive map + printable book → print.

---

## 6. Tech stack

**Phase 2 (Python)**
- EXIF read: Pillow / piexif / exifread
- Spatial: GeoPandas + Shapely
- Reverse geocoding: geopy → Nominatim (OpenStreetMap)
- Interactive map: Folium
- Static/print map: matplotlib + contextily (basemap)
- Book/PDF layout: matplotlib PDF export (or reportlab if richer layout needed)

**Phase 1 (web)**
- Plain HTML/JS, Leaflet + OpenStreetMap tiles
- Browser Geolocation API
- `tasks.geojson` as the data file
- Hostable free on GitHub Pages

**Tooling**
- VS Code + Python extension
- `venv` + `pip` to start; fall back to `uv` or conda/miniforge if the geo
  stack (GDAL/GEOS) fights the install on Windows
- `git` + private GitHub repo from day one
- Claude Code Desktop for building

---

## 7. Geo concepts to learn (the thread)

- WGS84 latitude/longitude — what phones report; why you can't run Pythagoras on degrees
- EXIF GPS metadata — pulling location out of a photo
- Reverse geocoding — coordinates → place names
- Spatial join / nearest-neighbour — matching photos to tasks
- Haversine / great-circle distance — "which tasks are near me" in the field app
- GeoJSON — storing points
- Map tiles & Leaflet — how web maps draw the world
- Interactive vs static rendering; Web Mercator (EPSG:3857) basics
- GPS accuracy & generous trigger radius (field app)

---

## 8. Decisions log (the *why*)

- **D1 — End product = physical book + digital photo-map.** Wanted something
  tangible to give the boys, not just a digital file; the photo-map also directly
  supports the geolocation learning goal.
- **D2 — Native camera, not in-browser capture.** Photos taken through a web page
  usually lose their GPS data; the photo-map needs that GPS, so shoot with the
  normal phone camera.
- **D3 — Link photos to tasks by location + time, not by capturing in-app.** More
  robust over a relaxed 3-week trip (full-quality photos, auto-backup, GPS intact),
  and the matching is itself a useful spatial-join exercise.
- **D4 — One shared `tasks.geojson` as the spine.** Defined once; the field app
  reads it for pins, the generator reads it for matching.
- **D5 — Build Phase 2 first.** Testable locally before the holiday; plays to
  existing Python/data strengths.
- **D6 — Separate data from rendering.** Once the geotagged, task-linked dataset
  is clean, it pours into both an interactive map and a print PDF — no need to
  choose the output format early.
- **D7 — Generous geofence radius (~25–30 m) in the field app.** GPS wobbles near
  seafront buildings and over open beach; a tight radius would feel broken.

---

## 9. Working style

- Concept before code — finalise the plan, then build.
- Iterative, small, testable steps over big-bang builds.
- Validate against real data / real sources where possible.
- Prefer practical, use-case-specific guidance over abstract frameworks.

---

## 10. Status

- **Current step:** Phase 2 / Step 1 — read photos + GPS.
- **Next action:** take 3–4 photos around the local area (location enabled in
  camera) → write and test the EXIF-reading script.
