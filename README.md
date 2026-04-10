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

Flickr provides the data — but not in a format that's immediately migration-ready.

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
4️⃣ Recovers files that have no EXIF date by falling back to Flickr JSON
5️⃣ Optionally embeds titles, tags, descriptions, and GPS metadata

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

## 📦 Requirements

### Python

Python 3.10 or newer. No third-party Python packages required — the scripts only use the standard library.

### exiftool (required)

This project relies on **[exiftool](https://exiftool.org/)** to read and write EXIF metadata. It must be installed at the system level — it is **not** a Python package and cannot be installed via `pip` or a `venv`.

**Windows (recommended — winget):**
```powershell
winget install OliverBetz.ExifTool
```
Close and reopen your terminal after installation so the `PATH` is refreshed.

**Windows (manual):**
1. Download the Windows executable from https://exiftool.org/
2. Unzip it
3. Rename `exiftool(-k).exe` to `exiftool.exe`
4. Move it to a folder in your `PATH` (e.g. `C:\Windows\`)

**macOS:**
```bash
brew install exiftool
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install libimage-exiftool-perl
```

**Verify the installation:**
```bash
exiftool -ver
```
You should see a version number (e.g. `13.55`).

---

## 📂 Typical Flickr Export Structure

```
Flickr Downloads/
  data-download-1/
  data-download-2/
  ...

Flickr Json Files/
  <export>_part1/
  <export>_part2/
```

---

## 🚀 Recommended Workflow

### On Linux / macOS

```bash
python3 scripts/rebuild_archive.py \
  --downloads "/path/to/Flickr Downloads" \
  --json "/path/to/part1" "/path/to/part2" \
  --out "/path/to/Flickr Organized"
```

### On Windows (PowerShell)

PowerShell does **not** use `\` as a line-continuation character like bash. Either keep the whole command on a single line:

```powershell
python scripts/rebuild_archive.py --downloads "C:\path\to\Flickr Downloads" --json "C:\path\to\Flickr Json Files" --out "C:\path\to\Flickr Organized"
```

…or use the PowerShell backtick `` ` `` (it must be the very last character on the line, with no trailing space):

```powershell
python scripts/rebuild_archive.py `
  --downloads "C:\path\to\Flickr Downloads" `
  --json "C:\path\to\Flickr Json Files" `
  --out "C:\path\to\Flickr Organized"
```

### What the main script does

1. Copies files from `Flickr Downloads` into `Flickr Organized/YYYY/MM/` based on their EXIF date
2. Fixes photo dates in the output folder by matching each file's Flickr ID against the JSON `date_taken`
3. Fixes video dates the same way (QuickTime-safe)

The original download is left untouched.

### Useful flags

- `--overwrite-original` — avoid creating `*_original` backup files when exiftool rewrites metadata
- `--embed` — also embed titles, descriptions, tags and GPS coordinates from the JSON sidecar files
- `--skip-organize` / `--skip-fix` / `--skip-embed` — run only specific stages
- `--mode move` — move files instead of copying (only use if you have a backup of `Flickr Downloads`)

---

## 🩹 Recovering Files With No EXIF Date

During the organize step you may see output like:

```
[DONE] COPY complete. Files processed: 539. Skipped (no date): 107.
```

The skipped files have no usable `DateTimeOriginal` or `CreateDate` in their EXIF, so `organize_by_year_month.py` doesn't know which `YYYY/MM/` folder to place them in. They stay in `Flickr Downloads` and are **not** copied into the organized archive.

To recover them using the Flickr JSON `date_taken` as a fallback, run:

```powershell
python scripts/organize_missing_by_json.py `
  --downloads "C:\path\to\Flickr Downloads" `
  --json "C:\path\to\Flickr Json Files" `
  --out "C:\path\to\Flickr Organized" `
  --overwrite-original
```

Add `--dry-run` first if you want to preview what would be recovered without touching any files.

**What it does:**

1. Lists every file already present in `Flickr Organized` (by filename)
2. Scans `Flickr Downloads` for photos/videos that are missing from the output
3. For each missing file, extracts the Flickr ID from the filename and looks up `date_taken` in the JSON folders
4. Copies the file to `Flickr Organized/YYYY/MM/` and stamps EXIF dates with exiftool
5. Prints a summary: recovered / no Flickr ID in filename / no JSON match / errors

---

## 🧹 Cleaning Up `*_original` Backups

By default, exiftool creates a `*_original` backup every time it writes metadata. If you ran the scripts without `--overwrite-original`, you'll find files like `annecy_30539565508_o.jpg_original` next to the actual JPEGs.

These backups are byte-identical to your untouched originals in `Flickr Downloads`, so they're safe to delete:

```powershell
# Preview what would be removed
Get-ChildItem "C:\path\to\Flickr Organized" -Recurse -Filter "*_original" | Measure-Object

# Actually remove them
Get-ChildItem "C:\path\to\Flickr Organized" -Recurse -Filter "*_original" | Remove-Item
```

On Linux / macOS:
```bash
find "/path/to/Flickr Organized" -name "*_original" -delete
```

To avoid creating them in the first place, always pass `--overwrite-original`.

---

## ⚠️ Cloud Sync Warning

Do **not** run metadata-rewrite steps while a cloud sync client (Google Drive, Dropbox, iCloud, OneDrive, etc.) is actively syncing the same directory. Concurrent writes from exiftool and the sync client can corrupt files or cause endless re-uploads.

Recommended workflow:

1. Generate the organized archive into a local folder outside any sync root
2. Let it finish completely
3. Then move or upload the final folder to your cloud storage

---

## 📦 Result

You end up with:

```
Flickr Organized/
  2016/11/
  2017/06/
  ...
```

With correct timestamps and searchable metadata.

Ready for:

- Google Photos
- Apple Photos
- NAS storage
- Long-term archival

---

## 🔒 Privacy

All processing is done locally. No network requests are made.

---

## 📜 License

MIT
