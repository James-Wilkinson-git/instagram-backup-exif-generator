#!/usr/bin/env python3
"""
Instagram Export Date Fixer
Extracts date taken from Instagram export HTML and updates image metadata
"""

import os
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
import piexif
import shutil

def parse_instagram_date(date_str):
    """Parse Instagram date formats"""
    # Try EXIF format: 2024:09:24 15:42:54
    try:
        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        pass
    
    # Try display format: Aug 06, 2012 4:13 pm
    try:
        return datetime.strptime(date_str, "%b %d, %Y %I:%M %p")
    except ValueError:
        pass
    
    return None

def find_date_in_html(html_content, debug=False):
    """Extract date from Instagram HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # First try to find the display date in div class="_3-94 _a6-o"
    date_div = soup.find('div', class_='_3-94 _a6-o')
    if date_div:
        date_text = date_div.get_text(strip=True)
        if debug:
            print(f"  Debug: Found display date div: '{date_text}'")
        date = parse_instagram_date(date_text)
        if date:
            if debug:
                print(f"  Debug: Parsed display date = {date}")
            return date
    
    # Fallback: try to find "Date taken" in metadata table
    rows = soup.find_all('tr')
    
    if debug:
        print(f"  Debug: Found {len(rows)} table rows")
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            # The label is in the first cell, value in the second
            label_div = cells[0].find('div', class_='_a6-q')
            # Value is nested: td -> div -> div (with class _a6-q)
            value_container = cells[1].find('div')
            if value_container:
                value_div = value_container.find('div', class_='_a6-q')
            else:
                value_div = None
            
            if label_div:
                label = label_div.get_text(strip=True)
                
                if debug:
                    value_text = value_div.get_text(strip=True) if value_div else "NO VALUE"
                    print(f"  Debug: Label='{label}', Value='{value_text}'")
                
                # Look for "Date taken" field
                if label == "Date taken" and value_div:
                    value = value_div.get_text(strip=True)
                    if value:
                        date = parse_instagram_date(value)
                        if debug:
                            print(f"  Debug: Parsed date from table = {date}")
                        return date
    
    return None

def find_images_in_html(html_content, html_file_path, debug=False):
    """Extract all image paths and their dates from HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all post containers
    posts = soup.find_all('div', class_='pam _3-95 _2ph- _a6-g uiBoxWhite noborder')
    
    images_with_dates = []
    
    for post in posts:
        # Find date in this post
        date_div = post.find('div', class_='_3-94 _a6-o')
        date = None
        if date_div:
            date_text = date_div.get_text(strip=True)
            date = parse_instagram_date(date_text)
        
        # If no display date, try metadata table
        if not date:
            rows = post.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label_div = cells[0].find('div', class_='_a6-q')
                    value_container = cells[1].find('div')
                    if value_container:
                        value_div = value_container.find('div', class_='_a6-q')
                    else:
                        value_div = None
                    
                    if label_div and value_div:
                        label = label_div.get_text(strip=True)
                        if label == "Date taken":
                            value = value_div.get_text(strip=True)
                            if value:
                                date = parse_instagram_date(value)
                                break
        
        # Find image in this post
        img_tag = post.find('img', class_='_a6_o _3-96')
        if img_tag and img_tag.get('src') and date:
            img_path = img_tag['src']
            
            # Find root by going up from your_instagram_activity
            path_parts = Path(html_file_path).parts
            try:
                activity_idx = path_parts.index('your_instagram_activity')
                root_path = Path(*path_parts[:activity_idx])
                full_path = root_path / img_path
                
                if full_path.exists():
                    images_with_dates.append((str(full_path), date))
                elif debug:
                    print(f"  Warning: Image not found: {full_path}")
            except (ValueError, IndexError):
                if debug:
                    print(f"  Warning: Could not determine root path")
    
    return images_with_dates

def update_image_metadata(image_path, date_taken):
    """Update image EXIF data and file timestamps"""
    if not os.path.exists(image_path):
        print(f"  Error: Image not found: {image_path}")
        return False
    
    try:
        # Create a backup
        backup_path = f"{image_path}.backup"
        shutil.copy2(image_path, backup_path)
        
        # Open image
        img = Image.open(image_path)
        
        # Format date for EXIF (YYYY:MM:DD HH:MM:SS)
        exif_date = date_taken.strftime("%Y:%m:%d %H:%M:%S")
        
        # Load existing EXIF data or create new
        try:
            exif_dict = piexif.load(image_path)
        except:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
        
        # Update EXIF fields
        exif_dict["0th"][piexif.ImageIFD.DateTime] = exif_date
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = exif_date
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = exif_date
        
        # Convert to bytes
        exif_bytes = piexif.dump(exif_dict)
        
        # Save image with updated EXIF
        img.save(image_path, exif=exif_bytes, quality=95)
        
        # Update file system timestamps
        timestamp = date_taken.timestamp()
        os.utime(image_path, (timestamp, timestamp))
        
        # Remove backup after successful update
        os.remove(backup_path)
        
        print(f"  ✓ Updated: {os.path.basename(image_path)} -> {date_taken}")
        return True
        
    except Exception as e:
        print(f"  Error updating {image_path}: {e}")
        # Restore from backup if it exists
        if os.path.exists(backup_path):
            shutil.move(backup_path, image_path)
        return False

def process_html_file(html_file_path, export_root, debug=False):
    """Process a single HTML file"""
    print(f"\nProcessing: {html_file_path}")
    
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extract all images and their dates
        images_with_dates = find_images_in_html(html_content, html_file_path, debug=debug)
        
        if not images_with_dates:
            print("  Warning: No images with dates found in HTML")
            return 0
        
        print(f"  Found {len(images_with_dates)} image(s)")
        
        # Update each image
        success_count = 0
        for image_path, date_taken in images_with_dates:
            if update_image_metadata(image_path, date_taken):
                success_count += 1
        
        return success_count
        
    except Exception as e:
        print(f"  Error processing file: {e}")
        return 0

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fix image dates from Instagram export HTML files'
    )
    parser.add_argument(
        'path',
        help='Path to HTML file or directory containing HTML files'
    )
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Search for HTML files recursively'
    )
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Show detailed parsing information'
    )
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        return
    
    # Determine export root directory
    export_root = path if path.is_dir() else path.parent
    export_root = export_root.resolve()
    
    if args.debug:
        print(f"Export root: {export_root}")
    
    # Collect HTML files
    html_files = []
    if path.is_file():
        if path.suffix.lower() == '.html':
            html_files = [path]
        else:
            print("Error: File must be an HTML file")
            return
    else:
        # Directory
        pattern = '**/*.html' if args.recursive else '*.html'
        html_files = list(path.glob(pattern))
    
    if not html_files:
        print(f"No HTML files found in: {path}")
        return
    
    print(f"Found {len(html_files)} HTML file(s)")
    
    # Process files
    success_count = 0
    total_images = 0
    for html_file in html_files:
        count = process_html_file(html_file, export_root, debug=args.debug)
        success_count += count
        total_images += count
    
    print(f"\n{'='*50}")
    print(f"Completed: {success_count} images updated successfully from {len(html_files)} HTML file(s)")

if __name__ == "__main__":
    main()