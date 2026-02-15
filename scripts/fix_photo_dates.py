#!/usr/bin/env python3
import argparse, json, os, re, subprocess, sys
from pathlib import Path

# Flickr photo IDs in filenames are typically 10-12 digits. (Avoid 8-digit dates like 20140603.)
ID_RE = re.compile(r'(?<!\d)(\d{10,12})(?!\d)')

PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v"}  # we'll handle videos later; included for mapping visibility

def load_id_to_date(json_dirs):
    id_to_date = {}
    total = 0
    for d in json_dirs:
        d = Path(d).expanduser()
        if not d.exists():
            print(f"[ERROR] JSON dir not found: {d}", file=sys.stderr)
            sys.exit(1)
        for p in d.rglob("photo_*.json"):
            total += 1
            try:
                with p.open("r", encoding="utf-8") as f:
                    obj = json.load(f)
                pid = str(obj.get("id", "")).strip()
                dt  = str(obj.get("date_taken", "")).strip()
                if pid and dt:
                    id_to_date[pid] = dt
            except Exception as e:
                print(f"[WARN] Failed to read {p}: {e}", file=sys.stderr)
    print(f"[INFO] JSON files scanned: {total:,} | with date_taken: {len(id_to_date):,}")
    return id_to_date

def find_media(download_root):
    download_root = Path(download_root).expanduser()
    if not download_root.exists():
        print(f"[ERROR] Downloads root not found: {download_root}", file=sys.stderr)
        sys.exit(1)

    id_to_files = {}
    scanned = 0

    for p in download_root.rglob("*"):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext not in PHOTO_EXTS and ext not in VIDEO_EXTS:
            continue

        scanned += 1
        m = ID_RE.findall(p.name)
        if not m:
            continue

        # Prefer the LAST match (usually the Flickr ID is near the end)
        pid = m[-1]

        id_to_files.setdefault(pid, []).append(p)

    print(f"[INFO] Media files scanned (photos+videos): {scanned:,} | matched IDs: {len(id_to_files):,}")
    return id_to_files

def pick_best_file(paths):
    # Prefer originals (_o) if present
    paths = sorted(paths, key=lambda x: x.name.lower())
    for p in paths:
        if "_o." in p.name.lower():
            return p
    return paths[0]

def to_exiftool_dt(dt):
    # JSON: "YYYY-MM-DD HH:MM:SS"  -> ExifTool: "YYYY:MM:DD HH:MM:SS"
    dt = dt.strip()
    if len(dt) >= 19 and dt[4] == "-" and dt[7] == "-" and dt[10] == " ":
        return dt[:10].replace("-", ":") + dt[10:19]
    return None

def run_exiftool(file_path, exif_dt, overwrite_original):
    args = ["exiftool"]
    if overwrite_original:
        args += ["-overwrite_original"]
    args += [
        f'-DateTimeOriginal={exif_dt}',
        f'-CreateDate={exif_dt}',
        f'-ModifyDate={exif_dt}',
        str(file_path),
    ]
    return subprocess.run(args, capture_output=True, text=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--downloads", required=True, help="Root folder containing data-download-* folders")
    ap.add_argument("--json", required=True, nargs="+", help="One or more JSON folders (part1 part2)")
    ap.add_argument("--limit", type=int, default=0, help="Process only N files (for testing). 0 = no limit")
    ap.add_argument("--dry-run", action="store_true", help="Do not write, just print what would happen")
    ap.add_argument("--overwrite-original", action="store_true",
                    help="Do NOT create *_original backups. Use only after you're confident.")
    args = ap.parse_args()

    id_to_date = load_id_to_date(args.json)
    id_to_files = find_media(args.downloads)

    # Build worklist (photos only for now)
    work = []
    for pid, paths in id_to_files.items():
        dt = id_to_date.get(pid)
        if not dt:
            continue
        best = pick_best_file(paths)
        ext = best.suffix.lower()
        if ext not in PHOTO_EXTS:
            continue  # videos later
        exif_dt = to_exiftool_dt(dt)
        if not exif_dt:
            continue
        work.append((pid, best, exif_dt))

    work.sort(key=lambda x: str(x[1]).lower())
    print(f"[INFO] Photo files with matching JSON date_taken: {len(work):,}")

    if args.limit and args.limit > 0:
        work = work[:args.limit]
        print(f"[INFO] Limiting to first {len(work)} files for this run")

    updated = 0
    for pid, path, exif_dt in work:
        if args.dry_run:
            print(f"[DRY] {pid}  {path}  <= {exif_dt}")
            continue
        res = run_exiftool(path, exif_dt, overwrite_original=args.overwrite_original)
        if res.returncode == 0:
            updated += 1
        else:
            print(f"[ERROR] exiftool failed for {path}\n{res.stderr}", file=sys.stderr)

    if args.dry_run:
        print("[DONE] Dry run complete.")
    else:
        print(f"[DONE] Updated {updated:,} photo files.")

if __name__ == "__main__":
    main()
