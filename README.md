# flickr-archive-rebuilder

Rebuild and reorganize a Flickr export into a clean, portable photo archive.

---

## 📸 Why This Exists

If you've downloaded your data from Flickr, you may have noticed:

- Photos and videos are stored in multiple `data-download-*` folders
- Important metadata (like the original capture date) is stored separately in JSON files
- Video timestamps may shift due to QuickTime/UTC formatting
- Albums are not reconstructed
- Uploading directly to Google Photos or Apple Photos can lead to incorrect timelines

Flickr provides the data — but not in a format that’s immediately migration-ready.

This tool fixes that.

---

## 🧠 What Problem Does It Solve?

When exporting from Flickr:

- The actual photo files may not contain correct `DateTimeOriginal`
- Videos may have shifted timestamps
- Metadata like titles, tags, or GPS is stored in separate JSON sidecar files
- Folder structure is fragmented

As a result:
- Your timeline may be incorrect in Google Photos
- Memories appear on wrong dates
- Media becomes harder to search and organize

This project reconstructs a clean, standards-compliant archive.

---

## 🧾 What Is EXIF?

**EXIF (Exchangeable Image File Format)** is metadata embedded inside image and video files.

It stores:
- Date taken
- Camera information
- GPS coordinates
- Orientation
- And more

Modern photo apps rely heavily on EXIF to build timelines and memories.

If EXIF timestamps are missing or incorrect, your media library becomes disorganized.

---

## 🔧 What This Tool Does

`flickr-archive-rebuilder`:

1️⃣ Restores correct photo capture dates from Flickr JSON  
2️⃣ Fixes video timestamps (QuickTime-safe handling)  
3️⃣ Reorganizes media into a clean `YYYY/MM` folder structure  
4️⃣ Optionally embeds titles, tags, descriptions, and GPS metadata  

All processing happens locally. No APIs. No uploads.

---

## 🛡 Safe-by-Default Design

- The original Flickr download is never modified.
- Media is first copied into an organized output folder.
- Metadata fixes are applied only to the output folder.
- Backups are created unless explicitly disabled.

This prevents:
- Cloud sync conflicts
- Accidental data corruption
- Polluting the original export

---

## 📂 Typical Flickr Export Structure

Flickr Downloads/
data-download-1/
data-download-2/
...

Flickr Json Files/
<export>_part1/
<export>_part2/


---

## 🚀 Recommended Workflow

```bash
python3 scripts/rebuild_archive.py \
  --downloads "/path/to/Flickr Downloads" \
  --json "/path/to/part1" "/path/to/part2" \
  --out "/path/to/Flickr Organized"
This will:

Create a YYYY/MM folder structure
Restore photo and video timestamps
Leave the original download untouched

Optional:

--embed
to embed titles, tags, and GPS (if present).

⚠️ Cloud Sync Warning
Do not run metadata-rewrite steps while a cloud sync client (Google Drive, Dropbox, etc.) is uploading the same directory.

Recommended:

Generate the organized archive.
Let it stabilize.
Then upload that folder.

---

📦 Result

You end up with:

Flickr Organized/
  2016/11/
  2017/06/
  ...
With correct timestamps and searchable metadata.

Ready for:

Google Photos
Apple Photos
NAS storage

Long-term archival

---

🔒 Privacy
All processing is done locally.
No network requests are made.

---

📜 License
MIT




