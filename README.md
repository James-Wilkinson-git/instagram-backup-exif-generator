# Instagram Export Date Fixer

A Python script that extracts photo dates from Instagram export HTML files and updates image metadata (EXIF data and file timestamps) so photos appear on the correct dates when uploaded to Google Photos or other photo management services.

## Problem

When you export your Instagram data, the downloaded images lose their original date metadata. This causes them to appear with incorrect dates (usually the download date) when you upload them to services like Google Photos.

This script solves that problem by:

1. Reading the original photo dates from Instagram's HTML export files
2. Updating the image EXIF data with the correct date
3. Updating the file system timestamps to match

## Requirements

- Python 3.6 or higher
- Required Python packages:
  - beautifulsoup4
  - Pillow
  - piexif

## Installation

1. **Clone this repository:**

   ```bash
   git clone https://github.com/yourusername/instagram-date-fixer.git
   cd instagram-date-fixer
   ```

2. **Install dependencies:**

   ```bash
   pip install beautifulsoup4 pillow piexif
   ```

   Or using requirements.txt:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Download Your Instagram Data

1. Go to Instagram Settings → Security → Download Data
2. Request your data export (this may take a few days)
3. Download and extract the ZIP file

Your export will have a structure like:

```
instagram-export/
├── media/
│   └── other/
│       └── [your images]
└── your_instagram_activity/
    ├── media/
    │   └── posts_1.html
    └── messages/
        └── inbox/
            └── [message folders with HTML files]
```

### Run the Script

**Process all HTML files recursively (recommended):**

```bash
python instagram_date_fixer.py your_instagram_activity/ --recursive
```

**Process a single HTML file:**

```bash
python instagram_date_fixer.py your_instagram_activity/media/posts_1.html
```

**Enable debug mode to see detailed information:**

```bash
python instagram_date_fixer.py your_instagram_activity/ --recursive --debug
```

### Command Line Options

- `path` - Path to an HTML file or directory containing HTML files
- `--recursive` or `-r` - Search for HTML files in subdirectories
- `--debug` or `-d` - Show detailed parsing and path resolution information

## How It Works

1. **Finds HTML files** - Locates Instagram export HTML files in the specified directory
2. **Extracts dates** - Parses each HTML file to find photo dates (supports both display format like "Aug 06, 2012 4:13 pm" and EXIF format like "2024:09:24 15:42:54")
3. **Locates images** - Resolves image paths from the HTML to find the actual image files
4. **Updates metadata** - For each image:
   - Creates a backup
   - Updates EXIF fields (DateTime, DateTimeOriginal, DateTimeDigitized)
   - Updates file system timestamps (modification and access times)
   - Removes backup on success

## Safety Features

- **Automatic backups** - Creates a `.backup` file before modifying each image
- **Error handling** - Continues processing other images if one fails
- **Backup restoration** - Automatically restores from backup if an update fails
- **Quality preservation** - Saves images at 95% quality to minimize re-compression

## Example Output

```
Found 150 HTML file(s)

Processing: your_instagram_activity/media/posts_1.html
  Found 25 image(s)
  ✓ Updated: image1.jpg -> 2024-04-12 06:29:00
  ✓ Updated: image2.jpg -> 2024-03-15 14:22:00
  ...

Processing: your_instagram_activity/messages/inbox/user/message_1.html
  Found 3 image(s)
  ✓ Updated: image3.jpg -> 2023-12-01 18:45:00
  ...

==================================================
Completed: 450 images updated successfully from 150 HTML file(s)
```

## Troubleshooting

### "Image not found" errors

Run with `--debug` to see the exact paths being checked:

```bash
python instagram_date_fixer.py your_instagram_activity/ --recursive --debug
```

The script expects this folder structure:

- Images in: `instagram-export/media/other/`
- HTML files in: `instagram-export/your_instagram_activity/`

### "Could not find date" warnings

Some Instagram posts may not have date information in the export. These will be skipped.

### Permission errors

Make sure you have write permissions for the image files and directory.

## After Running the Script

Once all images have been updated:

1. The images now have correct EXIF dates and file timestamps
2. You can upload them to Google Photos, iCloud, or any other photo service
3. They will appear on the correct dates in your photo library

## License

MIT License - feel free to use and modify as needed.

## Contributing

Issues and pull requests are welcome! If you encounter problems with specific Instagram export formats, please open an issue with a sample of the HTML structure.

## Disclaimer

This tool modifies your image files. While it creates backups and has been tested, always keep a copy of your original Instagram export before running the script.
