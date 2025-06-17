"""Handle RAW files separately"""

import rawpy
import exifread

def process_raw_file(filepath):
    try:
        with rawpy.imread(filepath) as raw:
            # Extract EXIF from RAW
            exif_data = raw.metadata
            return exif_data
    except:
        # Fallback to exifread
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f)
            return {tag: str(tags[tag]) for tag in tags}