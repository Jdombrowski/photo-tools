#!/usr/bin/env python3
# File: test_exif.py
# Location: ./test_exif.py
# Purpose: Test script to extract and display all EXIF data from a single photo

import sys
import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import json
from datetime import datetime

def extract_all_exif(image_path):
    """Extract and display all EXIF data from an image"""
    
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        return None
    
    try:
        # Open image and get EXIF data
        with Image.open(image_path) as img:
            print(f"📸 Image: {os.path.basename(image_path)}")
            print(f"📏 Size: {img.size}")
            print(f"🎨 Format: {img.format}")
            print(f"🔧 Mode: {img.mode}")
            print("-" * 50)
            
            exif_data = img.getexif()
            
            if not exif_data:
                print("❌ No EXIF data found in this image")
                return None
            
            print(f"✅ Found {len(exif_data)} EXIF tags")
            print("=" * 50)
            
            # Process all EXIF tags
            readable_exif = {}
            gps_data = None
            
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, f"Unknown_{tag_id}")
                
                # Handle GPS data specially
                if tag_name == 'GPSInfo':
                    gps_data = {}
                    print("\n📍 GPS Information:")
                    for gps_tag_id, gps_value in value.items():
                        gps_tag_name = GPSTAGS.get(gps_tag_id, f"GPS_Unknown_{gps_tag_id}")
                        gps_data[gps_tag_name] = gps_value
                        print(f"  {gps_tag_name}: {gps_value}")
                    readable_exif[tag_name] = gps_data
                else:
                    readable_exif[tag_name] = value
                    # Format output nicely
                    if isinstance(value, bytes):
                        display_value = f"<bytes: {len(value)} bytes>"
                    elif isinstance(value, (list, tuple)) and len(str(value)) > 100:
                        display_value = f"<{type(value).__name__}: {len(value)} items>"
                    else:
                        display_value = str(value)[:100] + "..." if len(str(value)) > 100 else value
                    
                    print(f"{tag_name:25} : {display_value}")
            
            # Show GPS coordinates if available
            if gps_data and 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
                try:
                    lat = convert_gps_to_decimal(gps_data)
                    if lat[0] is not None and lat[1] is not None:
                        print(f"\n🌍 Decimal GPS: {lat[0]:.6f}, {lat[1]:.6f}")
                except:
                    print("\n⚠️ Could not convert GPS coordinates")
            
            return readable_exif
            
    except Exception as e:
        print(f"❌ Error reading image: {str(e)}")
        return None

def convert_gps_to_decimal(gps_info):
    """Convert GPS coordinates to decimal degrees"""
    if not gps_info or 'GPSLatitude' not in gps_info or 'GPSLongitude' not in gps_info:
        return None, None
        
    def convert_to_degrees(value):
        d, m, s = float(value[0]), float(value[1]), float(value[2])
        return d + (m / 60.0) + (s / 3600.0)
    
    lat = convert_to_degrees(gps_info['GPSLatitude'])
    lon = convert_to_degrees(gps_info['GPSLongitude'])
    
    # Check direction
    if gps_info.get('GPSLatitudeRef') == 'S':
        lat = -lat
    if gps_info.get('GPSLongitudeRef') == 'W':
        lon = -lon
        
    return lat, lon

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_exif.py <image_path>")
        print("Example: python test_exif.py /path/to/photo.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    print("🔍 EXIF Data Extraction Test")
    print("=" * 50)
    
    exif_data = extract_all_exif(image_path)
    
    if exif_data:
        # Save to JSON file for detailed inspection
        output_file = f"exif_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(output_file, 'w') as f:
                json.dump(exif_data, f, indent=2, default=str)
            print(f"\n💾 Detailed EXIF data saved to: {output_file}")
        except Exception as e:
            print(f"⚠️ Could not save JSON file: {str(e)}")
        
        print("\n✅ Test completed successfully!")
        print(f"📊 Total EXIF tags found: {len(exif_data)}")
    else:
        print("\n❌ No EXIF data could be extracted")
        print("This could mean:")
        print("  • Image has no EXIF data")
        print("  • Image format not supported") 
        print("  • File is corrupted")

if __name__ == "__main__":
    main()