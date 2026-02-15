#!/usr/bin/env python3
import argparse
import csv
import os
import shutil
import subprocess
from pathlib import Path

PHOTO_EXTS = {".jpg",".jpeg",".png",".heic",".tif",".tiff"}
VIDEO_EXTS = {".mp4",".mov",".m4v"}

def run_exiftool_csv(downloads_root: Path, csv_path: Path):
    # One fast scan for all media with both DateTimeOriginal + CreateDate
    cmd = [
        "exiftool", "-r", "-csv",
        "-DateTimeOriginal", "-CreateDate",
        "-FileName", "-Directory",
        str(downloads_root)
    ]
    print("[INFO] Scanning files with exiftool (this may take a bit)...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or "exiftool failed")
    csv_path.write_text(res.stdout, encoding="utf-8")
    print(f"[INFO] Wrote manifest: {csv_path}")

def pick_dt(row: dict, ext: str) -> str | None:
    # Photos: DateTimeOriginal preferred. Videos: CreateDate.
    dto = (row.get("DateTimeOriginal") or "").strip()
    cd  = (row.get("CreateDate") or "").strip()
    if ext in PHOTO_EXTS:
        return dto or cd or None
    if ext in VIDEO_EXTS:
        return cd or dto or None
    return None

def year_month(dt: str) -> tuple[str,str] | None:
    # Expect "YYYY:MM:DD HH:MM:SS" or "YYYY:MM:DD HH:MM:SS+08:00" etc
    if len(dt) < 7:
        return None
    y = dt[0:4]
    m = dt[5:7]
    if not (y.isdigit() and m.isdigit()):
        return None
    return y, m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--downloads", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["copy","move"], default="copy")
    args = ap.parse_args()

    downloads = Path(args.downloads).expanduser()
    out_root  = Path(args.out).expanduser()

    out_root.mkdir(parents=True, exist_ok=True)

    manifest = Path("exif_manifest.csv")
    run_exiftool_csv(downloads, manifest)

    copied = 0
    skipped = 0

    with manifest.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = row.get("Directory")
            fn = row.get("FileName")
            if not d or not fn:
                skipped += 1
                continue

            src = Path(d) / fn
            ext = src.suffix.lower()
            if ext not in PHOTO_EXTS and ext not in VIDEO_EXTS:
                continue

            dt = pick_dt(row, ext)
            if not dt:
                skipped += 1
                continue

            ym = year_month(dt)
            if not ym:
                skipped += 1
                continue

            y, m = ym
            dest_dir = out_root / y / m
            dest_dir.mkdir(parents=True, exist_ok=True)

            dest = dest_dir / src.name

            # Avoid overwriting: if filename collides, add _1, _2, ...
            if dest.exists():
                stem = dest.stem
                suf = dest.suffix
                i = 1
                while True:
                    candidate = dest_dir / f"{stem}_{i}{suf}"
                    if not candidate.exists():
                        dest = candidate
                        break
                    i += 1

            if args.mode == "move":
                shutil.move(str(src), str(dest))
            else:
                shutil.copy2(str(src), str(dest))
            copied += 1

    print(f"[DONE] {args.mode.upper()} complete. Files processed: {copied:,}. Skipped (no date): {skipped:,}.")

if __name__ == "__main__":
    main()
