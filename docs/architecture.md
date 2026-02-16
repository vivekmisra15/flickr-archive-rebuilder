# Architecture

`flickr-archive-rebuilder` reconstructs a migration-ready media archive from a Flickr export by combining:
- Media files (photos/videos) in `data-download-*` folders
- Flickr JSON sidecars (`photo_<id>.json`) containing authoritative metadata (e.g., `date_taken`)

The pipeline is intentionally local-first and safe-by-default.

---

## High-level Flow (ASCII)

        +------------------------------+
        |      Flickr Export ZIP       |
        +------------------------------+
                 |
                 v
 +-------------------------------------------+
 | 1) Media files (data-download-*)          |
 |    - jpg/jpeg/png/heic/tif                |
 |    - mp4/mov/m4v                          |
 +-------------------------------------------+
                 |
                 |
                 +----------------------------------+
                 |                                  |
                 v                                  v
 +----------------------------------+   +----------------------------------+
 | 2) JSON sidecars (part1/part2)   |   | IDs embedded in filenames         |
 |    - photo_<id>.json             |   | e.g. *_<id>_o.jpg / *_<id>.mp4    |
 +----------------------------------+   +----------------------------------+
                 |                                  |
                 +---------------+------------------+
                                 |
                                 v
                 +-------------------------------------------+
                 | rebuild_archive.py (orchestrator)         |
                 |                                           |
                 | A) organize_by_year_month.py              |
                 |    -> output: YYYY/MM/ (copy/move)        |
                 |                                           |
                 | B) fix_photo_dates.py                     |
                 |    -> write DateTimeOriginal/CreateDate   |
                 |                                           |
                 | C) fix_video_dates.py                     |
                 |    -> write CreateDate/Track/Media dates  |
                 |                                           |
                 | D) embed_metadata.py (optional)           |
                 |    -> title/description/tags/GPS if present|
                 +-------------------------------------------+
                                 |
                                 v
                 +-------------------------------------------+
                 | Output Archive                             |
                 |  - Flickr Organized/YYYY/MM/...            |
                 |  - timeline-correct + migration-ready      |
                 +-------------------------------------------+

---

## High-level Flow (Mermaid)

```mermaid
flowchart TD
  A[Flickr Export] --> B[Media Files<br/>data-download-*]
  A --> C[JSON Sidecars<br/>photo_<id>.json<br/>part1/part2]

  B --> D[Extract Flickr ID from filename]
  C --> E[Load metadata by ID<br/>date_taken, tags, geo, etc.]

  D --> F[rebuild_archive.py<br/>(orchestrator)]
  E --> F

  F --> G[Organize<br/>YYYY/MM output]
  G --> H[Fix photo dates<br/>EXIF/XMP]
  H --> I[Fix video dates<br/>QuickTime/MP4 time tags]
  I --> J{Embed extra metadata?}
  J -->|Yes| K[embed_metadata.py<br/>title/desc/tags/geo]
  J -->|No| L[Skip]
  K --> M[Migration-ready archive]
  L --> M[Migration-ready archive]


Components
Orchestrator

scripts/rebuild_archive.py

Runs the full pipeline with safe defaults (operate on output folder, not originals).

Media Organizer

scripts/organize_by_year_month.py

Copies/moves media into YYYY/MM folders based on existing timestamps.

Photo Date Fix

scripts/fix_photo_dates.py

Uses date_taken from JSON to write EXIF date fields into photo files.

Video Date Fix

scripts/fix_video_dates.py

Writes video time tags correctly (noting QuickTime’s UTC behavior).

Metadata Embedding (Optional)

scripts/embed_metadata.py

Embeds title/description/tags/GPS where available in JSON.

Design Principles

Local-first: No network calls.

Safe-by-default: Originals untouched; work on copied output.

Idempotent-ish: Re-runs are supported with skip flags; avoid cloud-sync conflicts.

Standards-based: Uses EXIF/XMP/IPTC/QuickTime tags via ExifTool.
EOF