#!/usr/bin/env python3
import argparse, json, re, subprocess, sys
from pathlib import Path

ID_RE = re.compile(r'(?<!\d)(\d{10,12})(?!\d)')

PHOTO_EXTS = {".jpg",".jpeg",".png",".heic",".tif",".tiff"}
VIDEO_EXTS = {".mp4",".mov",".m4v"}

def load_titles(json_dirs):
    m = {}
    total = 0
    for d in map(Path, json_dirs):
        d = d.expanduser()
        for p in d.rglob("photo_*.json"):
            total += 1
            try:
                obj = json.loads(p.read_text(encoding="utf-8"))
                pid = str(obj.get("id","")).strip()
                title = (obj.get("name") or "").strip()
                if pid and title:
                    m[pid] = title
            except:
                pass
    print(f"[INFO] JSON scanned: {total:,} | titles mapped: {len(m):,}")
    return m

def set_title(path: Path, title: str, overwrite_original: bool):
    ext = path.suffix.lower()
    is_photo = ext in PHOTO_EXTS
    is_video = ext in VIDEO_EXTS
    if not (is_photo or is_video):
        return None

    args = ["exiftool"]
    if overwrite_original:
        args += ["-overwrite_original"]

    # XMP Title is broadly supported; IPTC ObjectName helps legacy photo tools.
    args += [f"-XMP:Title={title}"]
    if is_photo:
        args += [f"-IPTC:ObjectName={title}"]

    args += [str(path)]
    return subprocess.run(args, capture_output=True, text=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--organized", required=True)
    ap.add_argument("--json", required=True, nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--overwrite-original", action="store_true")
    args = ap.parse_args()

    titles = load_titles(args.json)

    organized = Path(args.organized).expanduser()
    files = [p for p in organized.rglob("*") if p.is_file() and p.suffix.lower() in (PHOTO_EXTS | VIDEO_EXTS)]
    files.sort(key=lambda x: str(x).lower())
    print(f"[INFO] Media files found: {len(files):,}")

    updated = 0
    skipped_no_id = 0
    skipped_no_json = 0

    for p in files:
        m = ID_RE.findall(p.name)
        if not m:
            skipped_no_id += 1
            continue
        pid = m[-1]
        title = titles.get(pid)
        if not title:
            skipped_no_json += 1
            continue

        if args.dry_run:
            print(f"[DRY] {pid}  {p.name}  title='{title[:80]}'")
            updated += 1
            if args.limit and updated >= args.limit:
                break
            continue

        res = set_title(p, title, args.overwrite_original)
        if res is None:
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
    print(f"[INFO] Skipped (no JSON match/title): {skipped_no_json:,}")

if __name__ == "__main__":
    main()
