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




