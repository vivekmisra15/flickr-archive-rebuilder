#!/usr/bin/env python3
"""
Embed Flickr JSON metadata (title/description/tags/geo) into media files.

Matches media to JSON via Flickr photo ID in the filename.

Safe defaults:
- Writes only fields enabled by flags
- Never blanks fields when JSON is empty
- Creates *_original backups unless --overwrite-original is used
"""

import argparse, json, re, subprocess, sys
from pathlib import Path

ID_RE = re.compile(r'(?<!\d)(\d{10,12})(?!\d)')

PHOTO_EXTS = {".jpg",".jpeg",".png",".heic",".tif",".tiff"}
VIDEO_EXTS = {".mp4",".mov",".m4v"}
MEDIA_EXTS = PHOTO_EXTS | VIDEO_EXTS

def load_json_records(json_dirs):
    out = {}
    scanned = 0
    for d in map(Path, json_dirs):
        d = d.expanduser()
        if not d.exists():
            print(f"[ERROR] JSON dir not found: {d}", file=sys.stderr)
            sys.exit(1)
        for p in d.rglob("photo_*.json"):
            scanned += 1
            try:
                obj = json.loads(p.read_text(encoding="utf-8"))
                pid = str(obj.get("id","")).strip()
                if not pid:
                    continue

                title = (obj.get("name") or "").strip()
                desc  = (obj.get("description") or "").strip()

                tags_raw = obj.get("tags") or []
                tags = []
                if isinstance(tags_raw, list):
                    for t in tags_raw:
                        if isinstance(t, str) and t.strip():
                            tags.append(t.strip())
                        elif isinstance(t, dict):
                            for k in ("raw","tag","name","text","value"):
                                v = t.get(k)
                                if isinstance(v, str) and v.strip():
                                    tags.append(v.strip())
                                    break
                seen = set()
                tags = [x for x in tags if not (x.lower() in seen or seen.add(x.lower()))]

                geo = None
                g = obj.get("geo")
                if isinstance(g, dict):
                    lat = g.get("latitude") or g.get("lat")
                    lon = g.get("longitude") or g.get("lon") or g.get("lng")
                    if lat is not None and lon is not None:
                        geo = {"lat": lat, "lon": lon}
                elif isinstance(g, list) and len(g) > 0 and isinstance(g[0], dict):
                    lat = g[0].get("latitude") or g[0].get("lat")
                    lon = g[0].get("longitude") or g[0].get("lon") or g[0].get("lng")
                    if lat is not None and lon is not None:
                        geo = {"lat": lat, "lon": lon}

                out[pid] = {"title": title, "description": desc, "tags": tags, "geo": geo}
            except Exception:
                continue

    print(f"[INFO] JSON files scanned: {scanned:,} | mapped IDs: {len(out):,}")
    return out

def exiftool_write(path, rec, *, title, description, tags, geo, overwrite_original):
    ext = path.suffix.lower()
    is_photo = ext in PHOTO_EXTS
    is_video = ext in VIDEO_EXTS
    if not (is_photo or is_video):
        return None

    args = ["exiftool"]
    if overwrite_original:
        args += ["-overwrite_original"]

    if title and rec["title"]:
        args += [f"-XMP:Title={rec['title']}"]
        if is_photo:
            args += [f"-IPTC:ObjectName={rec['title']}"]

    if description and rec["description"]:
        args += [f"-XMP:Description={rec['description']}"]
        if is_photo:
            args += [f"-IPTC:Caption-Abstract={rec['description']}"]

    if tags and rec["tags"]:
        for t in rec["tags"]:
            args += [f"-XMP:Subject+={t}"]
            if is_photo:
                args += [f"-IPTC:Keywords+={t}"]

    if geo and rec["geo"]:
        lat = rec["geo"]["lat"]
        lon = rec["geo"]["lon"]
        if is_photo:
            args += [f"-GPSLatitude={lat}", f"-GPSLongitude={lon}"]
        # Best-effort for videos/other tools
        args += [f"-XMP:GPSLatitude={lat}", f"-XMP:GPSLongitude={lon}"]

    if len(args) == (2 if overwrite_original else 1):
        return None

    args += [str(path)]
    return subprocess.run(args, capture_output=True, text=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--media-root", required=True)
    ap.add_argument("--json", required=True, nargs="+")
    ap.add_argument("--title", action="store_true")
    ap.add_argument("--description", action="store_true")
    ap.add_argument("--tags", action="store_true")
    ap.add_argument("--geo", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--overwrite-original", action="store_true")
    args = ap.parse_args()

    records = load_json_records(args.json)

    root = Path(args.media_root).expanduser()
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in MEDIA_EXTS]
    files.sort(key=lambda x: str(x).lower())
    print(f"[INFO] Media files found: {len(files):,}")

    updated = 0
    skipped_no_id = 0
    skipped_no_json = 0
    skipped_missing = 0

    for p in files:
        m = ID_RE.findall(p.name)
        if not m:
            skipped_no_id += 1
            continue
        pid = m[-1]
        rec = records.get(pid)
        if not rec:
            skipped_no_json += 1
            continue

        has_any = (
            (args.title and rec["title"]) or
            (args.description and rec["description"]) or
            (args.tags and rec["tags"]) or
            (args.geo and rec["geo"])
        )
        if not has_any:
            skipped_missing += 1
            continue

        if args.dry_run:
            print(f"[DRY] {pid}  {p.name}")
            updated += 1
            if args.limit and updated >= args.limit:
                break
            continue

        res = exiftool_write(
            p, rec,
            title=args.title, description=args.description, tags=args.tags, geo=args.geo,
            overwrite_original=args.overwrite_original
        )
        if res is None:
            skipped_missing += 1
            continue
        if res.returncode != 0:
            print(f"[ERROR] exiftool failed for {p}\n{res.stderr}", file=sys.stderr)
            continue

        updated += 1
        if args.limit and updated >= args.limit:
            break

    if args.dry_run:
        print(f"[DONE] Dry run listed: {updated:,}")
    else:
        print(f"[DONE] Updated: {updated:,}")

    print(f"[INFO] Skipped (no ID in filename): {skipped_no_id:,}")
    print(f"[INFO] Skipped (no JSON match): {skipped_no_json:,}")
    print(f"[INFO] Skipped (requested fields missing): {skipped_missing:,}")

if __name__ == "__main__":
    main()
