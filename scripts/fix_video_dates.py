#!/usr/bin/env python3
import argparse, json, re, subprocess, sys
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
                obj = json.loads(p.read_text(encoding="utf-8"))
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
        pid = m[-1]
        id_to_files.setdefault(pid, []).append(p)

    print(f"[INFO] Media files scanned (photos+videos): {scanned:,} | matched IDs: {len(id_to_files):,}")
    return id_to_files

def pick_best_file(paths):
    paths = sorted(paths, key=lambda x: x.name.lower())
    for p in paths:
        if "_o." in p.name.lower():
            return p
    return paths[0]

def to_exiftool_dt(dt):
    # "YYYY-MM-DD HH:MM:SS" -> "YYYY:MM:DD HH:MM:SS"
    dt = dt.strip()
    if len(dt) >= 19 and dt[4] == "-" and dt[7] == "-" and dt[10] == " ":
        return dt[:10].replace("-", ":") + dt[10:19]
    return None

def run_exiftool_photo(file_path, exif_dt, overwrite_original):
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

def run_exiftool_video(file_path, exif_dt, overwrite_original):
    # For MP4/MOV: set QuickTime/MP4 time tags commonly used by Photos/Google Photos.
    args = ["exiftool"]
    if overwrite_original:
        args += ["-overwrite_original"]
    args += [
        f'-CreateDate={exif_dt}',
        f'-ModifyDate={exif_dt}',
        f'-TrackCreateDate={exif_dt}',
        f'-TrackModifyDate={exif_dt}',
        f'-MediaCreateDate={exif_dt}',
        f'-MediaModifyDate={exif_dt}',
        str(file_path),
    ]
    return subprocess.run(args, capture_output=True, text=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--downloads", required=True)
    ap.add_argument("--json", required=True, nargs="+")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--overwrite-original", action="store_true")
    ap.add_argument("--mode", choices=["photos", "videos", "both"], default="videos")
    args = ap.parse_args()

    id_to_date = load_id_to_date(args.json)
    id_to_files = find_media(args.downloads)

    work = []
    for pid, paths in id_to_files.items():
        dt = id_to_date.get(pid)
        if not dt:
            continue
        best = pick_best_file(paths)
        exif_dt = to_exiftool_dt(dt)
        if not exif_dt:
            continue
        ext = best.suffix.lower()
        kind = "photo" if ext in PHOTO_EXTS else ("video" if ext in VIDEO_EXTS else None)
        if not kind:
            continue
        if args.mode == "photos" and kind != "photo":
            continue
        if args.mode == "videos" and kind != "video":
            continue
        work.append((pid, best, exif_dt, kind))

    work.sort(key=lambda x: str(x[1]).lower())
    print(f"[INFO] Files to process in mode={args.mode}: {len(work):,}")

    if args.limit and args.limit > 0:
        work = work[:args.limit]
        print(f"[INFO] Limiting to first {len(work)} files for this run")

    updated = 0
    for pid, path, exif_dt, kind in work:
        if args.dry_run:
            print(f"[DRY] {kind} {pid}  {path}  <= {exif_dt}")
            continue
        if kind == "photo":
            res = run_exiftool_photo(path, exif_dt, args.overwrite_original)
        else:
            res = run_exiftool_video(path, exif_dt, args.overwrite_original)
        if res.returncode == 0:
            updated += 1
        else:
            print(f"[ERROR] exiftool failed for {path}\n{res.stderr}", file=sys.stderr)

    if args.dry_run:
        print("[DONE] Dry run complete.")
    else:
        print(f"[DONE] Updated {updated:,} files.")

if __name__ == "__main__":
    main()
