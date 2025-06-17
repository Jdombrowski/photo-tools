import os
import pandas as pd
import PIL.Image
from PIL.ExifTags import TAGS, GPSTAGS
import json
from datetime import datetime
from pathlib import Path
import plotly.graph_objects as go

class PhotoMetadataAnalyzer:
    def __init__(self):
        self.metadata_cache = {}
        self.supported_formats = ['.jpg', '.jpeg', '.tiff', '.tif']
        
    def extract_exif_data(self, image_path):
        """Extract EXIF data from a single image file"""
        try:
            with PIL.Image.open(image_path) as img:
                exif_data = img.getexif()
                
            if not exif_data:
                return None
                
            # Convert EXIF data to readable format
            readable_exif = {}
            
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                
                # Handle GPS data separately
                if tag == 'GPSInfo':
                    gps_data = {}
                    for gps_tag_id, gps_value in value.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = gps_value
                    readable_exif[tag] = gps_data
                else:
                    readable_exif[tag] = value
                    
            return readable_exif
            
        except Exception as e:
            print(f"Error processing {image_path}: {str(e)}")
            return None
    
    def convert_gps_to_decimal(self, gps_info):
        """Convert GPS coordinates from EXIF format to decimal degrees"""
        if not gps_info or 'GPSLatitude' not in gps_info or 'GPSLongitude' not in gps_info:
            return None, None
            
        def convert_to_degrees(value):
            d, m, s = float(value[0]), float(value[1]), float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        
        lat = convert_to_degrees(gps_info['GPSLatitude'])
        lon = convert_to_degrees(gps_info['GPSLongitude'])
        
        # Check for direction
        if gps_info.get('GPSLatitudeRef') == 'S':
            lat = -lat
        if gps_info.get('GPSLongitudeRef') == 'W':
            lon = -lon
            
        return lat, lon
    
    def parse_camera_settings(self, exif_data):
        """Extract and normalize camera settings"""
        settings = {}
        
        # Aperture
        if 'FNumber' in exif_data:
            settings['aperture'] = f"f/{exif_data['FNumber']:.1f}"
        elif 'ApertureValue' in exif_data:
            aperture = 2 ** (exif_data['ApertureValue'] / 2)
            settings['aperture'] = f"f/{aperture:.1f}"
            
        # Shutter Speed
        if 'ExposureTime' in exif_data:
            exp_time = exif_data['ExposureTime']
            if exp_time < 1:
                settings['shutter_speed'] = f"1/{int(1/exp_time)}"
            else:
                settings['shutter_speed'] = f"{exp_time}s"
                
        # ISO
        if 'ISOSpeedRatings' in exif_data:
            settings['iso'] = exif_data['ISOSpeedRatings']
        elif 'ISO' in exif_data:
            settings['iso'] = exif_data['ISO']
            
        # Focal Length
        if 'FocalLength' in exif_data:
            settings['focal_length'] = f"{exif_data['FocalLength']}mm"
            
        # Camera and Lens
        settings['camera'] = exif_data.get('Model', 'Unknown')
        settings['make'] = exif_data.get('Make', 'Unknown')
        settings['lens'] = exif_data.get('LensModel', 'Unknown')
        
        # Date/Time
        if 'DateTime' in exif_data:
            try:
                settings['datetime'] = datetime.strptime(exif_data['DateTime'], '%Y:%m:%d %H:%M:%S')
            except:
                settings['datetime'] = None
                
        return settings
    
    def process_photo_directory(self, directory_path, recursive=True):
        """Process all photos in a directory and extract metadata"""
        photo_data = []
        
        directory = Path(directory_path)
        
        if recursive:
            image_files = []
            for ext in self.supported_formats:
                image_files.extend(directory.rglob(f"*{ext}"))
                image_files.extend(directory.rglob(f"*{ext.upper()}"))
        else:
            image_files = []
            for ext in self.supported_formats:
                image_files.extend(directory.glob(f"*{ext}"))
                image_files.extend(directory.glob(f"*{ext.upper()}"))
        
        for img_path in image_files:
            exif_data = self.extract_exif_data(img_path)
            
            if exif_data:
                # Parse camera settings
                settings = self.parse_camera_settings(exif_data)
                
                # GPS coordinates
                gps_info = exif_data.get('GPSInfo', {})
                lat, lon = self.convert_gps_to_decimal(gps_info)
                
                # Combine all data
                photo_record = {
                    'filename': img_path.name,
                    'filepath': str(img_path),
                    'file_size_mb': img_path.stat().st_size / (1024 * 1024),
                    'latitude': lat,
                    'longitude': lon,
                    **settings
                }
                
                photo_data.append(photo_record)
        
        return pd.DataFrame(photo_data)
    
    def generate_insights(self, df):
        """Generate analytical insights from the photo metadata"""
        insights = {}
        
        # Camera usage statistics
        insights['camera_usage'] = df['camera'].value_counts().to_dict()
        insights['lens_usage'] = df['lens'].value_counts().to_dict()
        
        # Settings analysis
        if 'iso' in df.columns:
            insights['avg_iso'] = df['iso'].mean()
            insights['iso_distribution'] = df['iso'].value_counts().to_dict()
        
        # Time-based patterns
        if 'datetime' in df.columns and df['datetime'].notna().any():
            df['hour'] = df['datetime'].dt.hour
            df['month'] = df['datetime'].dt.month
            df['year'] = df['datetime'].dt.year
            
            insights['shooting_hours'] = df['hour'].value_counts().sort_index().to_dict()
            insights['shooting_months'] = df['month'].value_counts().sort_index().to_dict()
            insights['photos_per_year'] = df['year'].value_counts().sort_index().to_dict()
        
        # Location insights (if GPS data available)
        gps_photos = df.dropna(subset=['latitude', 'longitude'])
        insights['gps_enabled_photos'] = len(gps_photos)
        insights['total_photos'] = len(df)
        insights['gps_percentage'] = (len(gps_photos) / len(df)) * 100 if len(df) > 0 else 0
        
        return insights

# Example usage and testing
def main():
    analyzer = PhotoMetadataAnalyzer()
    
    # For testing - replace with your photo directory
    photo_directory = "/path/to/your/photos"
    
    if os.path.exists(photo_directory):
        print("Processing photos...")
        df = analyzer.process_photo_directory(photo_directory)
        
        print(f"Processed {len(df)} photos")
        print("\nSample data:")
        print(df.head())
        
        # Generate insights
        insights = analyzer.generate_insights(df)
        print("\nInsights:")
        print(json.dumps(insights, indent=2, default=str))
        
        # Save to CSV for further analysis
        df.to_csv('photo_metadata.csv', index=False)
        print("\nData saved to photo_metadata.csv")
    else:
        print(f"Directory {photo_directory} not found. Update the path to test.")

if __name__ == "__main__":
    main()