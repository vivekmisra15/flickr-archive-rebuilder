# flickr-archive-rebuilder

Reconstruct and reorganize a Flickr export using official JSON sidecar metadata.

## ✨ Overview

Flickr exports media separately from its metadata.

This project restores:

-   📅 Correct capture timestamps (photos + videos)
    
-   🎬 Proper QuickTime video dates (UTC-safe)
    
-   🗂 Clean `YYYY/MM` archive structure
    
-   🏷 Optional embedding of titles, descriptions, tags, and GPS
    
-   ☁ Ready-for-upload structure for Google Photos or long-term storage
    

Everything runs locally. No external APIs.

----------

## 🔧 Requirements

-   Python 3.9+
    
-   ExifTool installed and available in PATH
    

Install ExifTool (macOS):

`brew install exiftool` 

----------

## 📁 Typical Flickr Export

`Flickr Downloads/ data-download-1/ data-download-2/
  ...

Flickr Json Files/
  <export>_part1/
  <export>_part2/` 

----------

# 🛠 Workflow

## 1️⃣ Fix Photo Dates

`python3 scripts/fix_photo_dates.py \
  --downloads "/path/to/Flickr Downloads" \
  --json "/path/to/part1"  "/path/to/part2"` 

Writes:

-   DateTimeOriginal
    
-   CreateDate
    
-   ModifyDate
    

----------

## 2️⃣ Fix Video Dates (MP4/MOV)

`python3 scripts/fix_video_dates.py \
  --downloads "/path/to/Flickr Downloads" \
  --json "/path/to/part1"  "/path/to/part2"` 

Handles QuickTime UTC properly.

----------

## 3️⃣ Organize into Year/Month

`python3 scripts/organize_by_year_month.py \
  --downloads "/path/to/Flickr Downloads" \
  --out "/path/to/Flickr Organized" \
  --mode copy` 

Creates:

`Flickr  Organized/  2016/11/  2017/06/` 

----------

## 4️⃣ Optional: Embed Additional Metadata

`python3 scripts/embed_metadata.py \
  --media-root "/path/to/Flickr Organized" \
  --json "/path/to/part1"  "/path/to/part2" \
  --title --description --tags --geo` 

Writes only fields present in JSON.

----------

# 📦 Output

A clean, portable archive:

`YYYY/MM/media files...` 

Ready for:

-   Google Photos
    
-   Apple Photos
    
-   NAS storage
    
-   Cold archive backup
    

----------

# ⚠ Design Notes

-   JSON is treated as authoritative for capture date.
    
-   Video timestamps stored internally in UTC (per QuickTime spec).
    
-   ID matching uses Flickr photo ID embedded in filename.
    
-   Non-destructive by default.
    

----------

# 🔒 Privacy

All processing happens locally.  
No network requests are made.

----------

# 📜 License

MIT