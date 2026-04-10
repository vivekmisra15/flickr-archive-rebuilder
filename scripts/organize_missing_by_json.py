#!/usr/bin/env python3
"""
Recover files that were skipped by organize_by_year_month.py because they
had no usable EXIF date. Uses Flickr JSON date_taken as the source of truth.

Steps:
- Scan --downloads for all photos/videos.
- Skip files already present (by name) in --out.
- For each remaining file, extract its Flickr ID from the filename and look
  up date_taken in the provided JSON folders.
- Copy to --out/YYYY/MM/ and stamp EXIF dates with exiftool.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ID_RE = re.compile(r'(?<!\d)(\d{10,12})(?!\d)')
PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v"}

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

def to_exiftool_dt(dt):
    dt = dt.strip()
    if len(dt) >= 19 and dt[4] == "-" and dt[7] == "-" and dt[10] == " ":
        return dt[:10].replace("-", ":") + dt[10:19]
    return None

def year_month_from_json(dt):
    # "YYYY-MM-DD HH:MM:SS"
    if len(dt) < 7:
        return None
    y, m = dt[0:4], dt[5:7]
    if not (y.isdigit() and m.isdigit()):
        return None
    return y, m

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
    ap.add_argument("--downloads", required=True)
    ap.add_argument("--json", required=True, nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--overwrite-original", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    downloads = Path(args.downloads).expanduser()
    out_root = Path(args.out).expanduser()
    if not downloads.exists():
        print(f"[ERROR] Downloads not found: {downloads}", file=sys.stderr)
        sys.exit(1)
    out_root.mkdir(parents=True, exist_ok=True)

    # Build set of filenames already present in out_root (recursive)
    existing = {p.name.lower() for p in out_root.rglob("*") if p.is_file()}
    print(f"[INFO] Files already in out: {len(existing):,}")

    id_to_date = load_id_to_date(args.json)

    # Find candidates in downloads not yet in out
    candidates = []
    for p in downloads.rglob("*"):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext not in PHOTO_EXTS and ext not in VIDEO_EXTS:
            continue
        if p.name.lower() in existing:
            continue
        candidates.append(p)

    print(f"[INFO] Missing media candidates: {len(candidates):,}")

    recovered = 0
    no_id = 0
    no_json = 0
    bad_dt = 0
    errors = 0

    for src in candidates:
        ids = ID_RE.findall(src.name)
        if not ids:
            no_id += 1
            continue
        pid = ids[-1]
        dt = id_to_date.get(pid)
        if not dt:
            no_json += 1
            continue
        ym = year_month_from_json(dt)
        exif_dt = to_exiftool_dt(dt)
        if not ym or not exif_dt:
            bad_dt += 1
            continue

        y, m = ym
        dest_dir = out_root / y / m
        dest = dest_dir / src.name
        if dest.exists():
            stem, suf = dest.stem, dest.suffix
            i = 1
            while True:
                cand = dest_dir / f"{stem}_{i}{suf}"
                if not cand.exists():
                    dest = cand
                    break
                i += 1

        if args.dry_run:
            print(f"[DRY] {src}  =>  {dest}  ({exif_dt})")
            recovered += 1
            continue

        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dest))
        res = run_exiftool(dest, exif_dt, overwrite_original=args.overwrite_original)
        if res.returncode != 0:
            errors += 1
            print(f"[ERROR] exiftool failed for {dest}\n{res.stderr}", file=sys.stderr)
            continue
        recovered += 1

    print(
        f"[DONE] Recovered: {recovered:,} | "
        f"no Flickr ID in name: {no_id:,} | "
        f"no JSON date: {no_json:,} | "
        f"bad date format: {bad_dt:,} | "
        f"exiftool errors: {errors:,}"
    )

if __name__ == "__main__":
    main()
