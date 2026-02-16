#!/usr/bin/env python3
"""
Unified entrypoint for flickr-archive-rebuilder (safe-by-default).

SAFE DEFAULTS:
- Does NOT modify the original Flickr downloads.
- First organizes into --out (YYYY/MM) using --mode (default: copy).
- Then fixes photo/video dates on the --out folder.
- Optional metadata embedding also runs on --out.

Why: avoids polluting the original export with *_original backups and prevents
cloud-sync conflicts.

Example:
python3 scripts/rebuild_archive.py \
  --downloads "/path/to/Flickr Downloads" \
  --json "/path/to/part1" "/path/to/part2" \
  --out "/path/to/Flickr Organized" \
  --mode copy
"""

import argparse
import subprocess
import sys
from pathlib import Path

def die(msg: str, code: int = 2):
    print(msg, file=sys.stderr)
    sys.exit(code)

def validate_paths(downloads: str, json_dirs: list[str], out: str):
    d = Path(downloads).expanduser()
    if not d.exists():
        die(f"[ERROR] Downloads path not found: {d}")

    missing = []
    for j in json_dirs:
        jp = Path(j).expanduser()
        if not jp.exists():
            missing.append(str(jp))
    if missing:
        die("[ERROR] JSON dir(s) not found:\n  " + "\n  ".join(missing))

    outp = Path(out).expanduser()
    outp.parent.mkdir(parents=True, exist_ok=True)

def run(cmd: list[str]):
    print(f"\n[RUN] {' '.join(cmd)}\n")
    res = subprocess.run(cmd)
    if res.returncode != 0:
        die("[ERROR] Step failed. Aborting.", res.returncode)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--downloads", required=True, help="Root of Flickr media export (data-download-* folders)")
    ap.add_argument("--json", required=True, nargs="+", help="One or more Flickr JSON folders (part1, part2, ...)")
    ap.add_argument("--out", required=True, help="Output folder (YYYY/MM structure)")
    ap.add_argument("--mode", choices=["copy", "move"], default="copy", help="Organize mode (default: copy)")
    ap.add_argument("--embed", action="store_true", help="Also embed title/description/tags/geo if present in JSON")
    ap.add_argument("--overwrite-original", action="store_true", help="Avoid *_original backups when writing metadata")
    ap.add_argument("--skip-organize", action="store_true")
    ap.add_argument("--skip-fix", action="store_true", help="Skip both photo+video fix steps")
    ap.add_argument("--skip-embed", action="store_true")
    args = ap.parse_args()

    validate_paths(args.downloads, args.json, args.out)

    base = Path(__file__).parent

    # 1) Organize into YYYY/MM (copy/move)
    if not args.skip_organize:
        run([
            "python3", str(base / "organize_by_year_month.py"),
            "--downloads", args.downloads,
            "--out", args.out,
            "--mode", args.mode
        ])

    # 2) Fix photo + video dates ON THE OUTPUT folder (safe)
    if not args.skip_fix:
        photo_cmd = [
            "python3", str(base / "fix_photo_dates.py"),
            "--downloads", args.out,
            "--json", *args.json,
        ]
        if args.overwrite_original:
            photo_cmd.append("--overwrite-original")
        run(photo_cmd)

        video_cmd = [
            "python3", str(base / "fix_video_dates.py"),
            "--downloads", args.out,
            "--json", *args.json,
        ]
        if args.overwrite_original:
            video_cmd.append("--overwrite-original")
        run(video_cmd)

    # 3) Optional: embed additional metadata ON THE OUTPUT folder
    if args.embed and not args.skip_embed:
        cmd = [
            "python3", str(base / "embed_metadata.py"),
            "--media-root", args.out,
            "--json", *args.json,
            "--title", "--description", "--tags", "--geo",
        ]
        if args.overwrite_original:
            cmd.append("--overwrite-original")
        run(cmd)

    print("\n[SUCCESS] Archive rebuild complete.\n")

if __name__ == "__main__":
    main()
