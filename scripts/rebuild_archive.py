#!/usr/bin/env python3
"""
Unified entrypoint for flickr-archive-rebuilder.

Runs:
1. Photo date restoration
2. Video date restoration
3. Year/month organization
4. Optional metadata embedding
"""

import argparse
import subprocess
import sys
from pathlib import Path

def run(cmd):
    print(f"\n[RUN] {' '.join(cmd)}\n")
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print("[ERROR] Step failed. Aborting.")
        sys.exit(res.returncode)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--downloads", required=True)
    ap.add_argument("--json", required=True, nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--embed", action="store_true")
    ap.add_argument("--overwrite-original", action="store_true")
    args = ap.parse_args()

    base = Path(__file__).parent

    # 1️⃣ Fix photo dates
    run([
        "python3", str(base / "fix_photo_dates.py"),
        "--downloads", args.downloads,
        "--json", *args.json
    ])

    # 2️⃣ Fix video dates
    run([
        "python3", str(base / "fix_video_dates.py"),
        "--downloads", args.downloads,
        "--json", *args.json
    ])

    # 3️⃣ Organize
    run([
        "python3", str(base / "organize_by_year_month.py"),
        "--downloads", args.downloads,
        "--out", args.out,
        "--mode", "copy"
    ])

    # 4️⃣ Optional embed
    if args.embed:
        embed_cmd = [
            "python3", str(base / "embed_metadata.py"),
            "--media-root", args.out,
            "--json", *args.json,
            "--title", "--description", "--tags", "--geo"
        ]
        if args.overwrite_original:
            embed_cmd.append("--overwrite-original")

        run(embed_cmd)

    print("\n[SUCCESS] Archive rebuild complete.\n")

if __name__ == "__main__":
    main()
