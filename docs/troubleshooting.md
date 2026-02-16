# Troubleshooting Guide

This document captures common issues encountered when rebuilding a Flickr archive.

---

## 1. "JSON dir not found"

**Error:**
[ERROR] JSON dir not found: /path/to/part1


**Cause:**
You used placeholder paths like `/path/to/...` instead of your real folders.

**Fix:**
Use full absolute paths:

/Users/yourname/Documents/Flickr Json Files/...


---

## 2. zsh: bad substitution

**Error:**
zsh: bad substitution


**Cause:**
The shell interpreted `${...}` inside an exiftool command instead of passing it literally.

**Fix:**
Wrap the exiftool argument in single quotes:

'-Directory</path/${DateTimeOriginal;DateFmt("%Y/%m")}'


Or use a Python script instead of inline shell formatting.

---

## 3. Long-running fix step appears frozen

During `fix_photo_dates.py`, there may be no output for several minutes.

**Why:**
The script processes files sequentially and does not print progress per file.

**Reality:**
ExifTool is running in the background.

To check:

ps aux | grep exiftool


If nothing appears and the process seems stuck for a long time, safely interrupt with:

Ctrl + C


---

## 4. Cloud sync errors ("Can't sync these files")

If Google Drive or another sync tool reports sync failures:

**Cause:**
Files were being rewritten by ExifTool while the sync client was reading them.

**Fix:**
- Stop the rebuild process.
- Let cloud sync finish.
- Never rewrite metadata in a directory actively syncing.

Recommended workflow:
1. Generate organized output folder.
2. Let it stabilize.
3. Upload the output folder.

---

## 5. Finder shows more files than Google uploaded

Example:
- Finder: 11,602 items
- Google: 11,543 items

**Why:**
Finder counts:
- Folders
- Hidden files (.DS_Store)
- Non-media files

Google counts:
- Only media files (jpg, mp4, etc.)


---

## 6. *_original files created

ExifTool creates backup files named:

filename.jpg_original


These are backups of the original file before metadata rewrite.

To avoid backups:
--overwrite-original


To delete backup files safely:
find "/path/to/downloads" -type f -name "*_original" -delete


---

## 7. Video dates appear shifted by hours

QuickTime stores timestamps in UTC.

Photo apps display in local time.

This is normal behavior and not data corruption.

---

## 8. JSON contains no tags, GPS, or descriptions

Some Flickr exports contain empty arrays:

"tags": []
"geo": []
"description": ""


In such cases, embedding metadata will skip those fields automatically.

---

## 9. Re-running pipeline multiple times

Re-running the tool will rewrite metadata again unless:

--skip-fix
--skip-organize


Use skip flags to avoid unnecessary processing.

---

## General Recommendation

Always treat the original Flickr export as read-only.

Work on a copied and organized output folder instead.
