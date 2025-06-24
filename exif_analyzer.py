#!/usr/bin/env python3
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, Union

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError:
    print("❌ Error: Pillow library not found.")
    print("Install with: pip install Pillow")
    sys.exit(1)

class ExifValueConverter:
    """Handles safe conversion of EXIF values to usable formats"""
    
    @staticmethod
    def to_float(value, value_name="unknown"):
        """
        Safely convert EXIF values to float, handling all possible formats
        Returns: (float_value, conversion_info) or (None, error_info)
        """
        try:
            if value is None:
                return None, "None value"
            
            # Handle tuple fractions (most common for camera settings)
            if isinstance(value, (tuple, list)) and len(value) >= 2:
                numerator, denominator = value[0], value[1]
                if denominator == 0:
                    return None, f"Division by zero in fraction {value}"
                result = float(numerator) / float(denominator)
                return result, f"Fraction {numerator}/{denominator} = {result}"
            
            # Handle direct numeric values
            elif isinstance(value, (int, float)):
                return float(value), f"Direct numeric: {value}"
            
            # Handle string values
            elif isinstance(value, str):
                try:
                    return float(value), f"String parsed: '{value}'"
                except ValueError:
                    return None, f"Non-numeric string: '{value}'"
            
            # Handle bytes (should not be converted to numeric)
            elif isinstance(value, bytes):
                return None, f"Bytes data ({len(value)} bytes) - not numeric"
            
            # Handle single-item tuples/lists
            elif isinstance(value, (tuple, list)) and len(value) == 1:
                return ExifValueConverter.to_float(value[0], f"{value_name}[0]")
            
            # Unknown type
            else:
                return None, f"Unknown type {type(value)}: {value}"
                
        except Exception as e:
            return None, f"Conversion error: {str(e)}"
    
    @staticmethod
    def format_shutter_speed(time_seconds):
        """Format shutter speed for display"""
        if time_seconds is None:
            return "Unknown"
        
        if time_seconds < 1:
            try:
                reciprocal = int(round(1 / time_seconds))
                return f"1/{reciprocal}"
            except:
                return f"{time_seconds:.6f}s"
        else:
            return f"{time_seconds}s"
    
    @staticmethod
    def format_aperture(f_number):
        """Format aperture for display"""
        return f"f/{f_number:.1f}" if f_number is not None else "Unknown"
    
    @staticmethod
    def format_iso(iso_value):
        """Format ISO for display"""
        return f"ISO {int(iso_value)}" if iso_value is not None else "Unknown"
    
    @staticmethod
    def format_datetime(dt_string):
        """Format EXIF datetime strings"""
        if not dt_string:
            return "Unknown"
        
        try:
            # EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
            dt = datetime.strptime(dt_string, "%Y:%m:%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                # Try alternative format
                dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                return f"Invalid format: {dt_string}"
    
    @staticmethod
    def decode_flash_value(flash_value):
        """Decode flash mode from numeric value"""
        if flash_value is None:
            return "Unknown"
        
        flash_modes = {
            0: "No flash",
            1: "Flash fired",
            5: "Strobe return light not detected",
            7: "Strobe return light detected",
            9: "Flash fired, compulsory flash mode",
            13: "Flash fired, compulsory flash mode, return light not detected",
            15: "Flash fired, compulsory flash mode, return light detected",
            16: "Flash did not fire, compulsory flash mode",
            24: "Flash did not fire, auto mode",
            25: "Flash fired, auto mode",
            29: "Flash fired, auto mode, return light not detected",
            31: "Flash fired, auto mode, return light detected",
            32: "No flash function",
            65: "Flash fired, red-eye reduction mode",
            69: "Flash fired, red-eye reduction mode, return light not detected",
            71: "Flash fired, red-eye reduction mode, return light detected",
            73: "Flash fired, compulsory flash mode, red-eye reduction mode",
            77: "Flash fired, compulsory flash mode, red-eye reduction mode, return light not detected",
            79: "Flash fired, compulsory flash mode, red-eye reduction mode, return light detected",
            89: "Flash fired, auto mode, red-eye reduction mode",
            93: "Flash fired, auto mode, return light not detected, red-eye reduction mode",
            95: "Flash fired, auto mode, return light detected, red-eye reduction mode"
        }
        
        return flash_modes.get(int(flash_value), f"Unknown mode ({flash_value})")
    
    @staticmethod
    def decode_metering_mode(mode_value):
        """Decode metering mode from numeric value"""
        if mode_value is None:
            return "Unknown"
        
        metering_modes = {
            0: "Unknown",
            1: "Average",
            2: "Center-weighted average",
            3: "Spot",
            4: "Multi-spot",
            5: "Pattern",
            6: "Partial",
            255: "Other"
        }
        
        return metering_modes.get(int(mode_value), f"Unknown mode ({mode_value})")
    
    @staticmethod
    def decode_white_balance(wb_value):
        """Decode white balance from numeric value"""
        if wb_value is None:
            return "Unknown"
        
        wb_modes = {
            0: "Auto",
            1: "Manual",
            2: "Auto (warm light)",
            3: "Auto (cool light)",
            4: "Auto (daylight)",
            5: "Auto (cloudy)",
            6: "Auto (tungsten)",
            7: "Auto (fluorescent)",
            8: "Auto (flash)",
            9: "Manual",
            10: "Cloudy",
            11: "Shade",
            17: "Manual",
            18: "Daylight fluorescent",
            19: "Day white fluorescent",
            20: "Cool white fluorescent",
            21: "White fluorescent",
            22: "Warm white fluorescent",
            23: "Standard light A",
            24: "Standard light B",
            25: "Standard light C",
            26: "D55",
            27: "D65",
            28: "D75",
            29: "D50",
            30: "ISO studio tungsten"
        }
        
        return wb_modes.get(int(wb_value), f"Unknown mode ({wb_value})")

class CameraSettingsExtractor:
    """Extracts and analyzes camera settings from EXIF data"""
    
    def __init__(self, verbose=True):
        self.converter = ExifValueConverter()
        self.verbose = verbose
    
    def _print(self, message):
        """Print message only if verbose mode is enabled"""
        if self.verbose:
            print(message)
    
    def extract_setting(self, exif_data, tag_name, setting_type):
        """Generic method to extract and convert a camera setting"""
        if tag_name not in exif_data:
            return None, f"Tag '{tag_name}' not found"
        
        raw_value = exif_data[tag_name]
        self._print(f"  ✅ {tag_name} found: {raw_value} (type: {type(raw_value)})")
        
        converted_value, conversion_info = self.converter.to_float(raw_value, tag_name)
        self._print(f"     Conversion: {conversion_info}")
        
        return converted_value, conversion_info
    
    def extract_aperture(self, exif_data):
        """Extract aperture values using multiple methods"""
        self._print("\n🔍 APERTURE EXTRACTION:")
        aperture_results = {}
        
        # Method 1: FNumber (most common)
        f_number, _ = self.extract_setting(exif_data, 'FNumber', 'aperture')
        if f_number is not None:
            aperture_results['FNumber'] = f_number
            self._print(f"     Final aperture: {self.converter.format_aperture(f_number)}")
        
        # Method 2: ApertureValue (APEX system)
        apex_value, _ = self.extract_setting(exif_data, 'ApertureValue', 'aperture')
        if apex_value is not None:
            try:
                f_stop = 2 ** (apex_value / 2)
                aperture_results['ApertureValue'] = f_stop
                self._print(f"     APEX calculation: 2^({apex_value}/2) = {self.converter.format_aperture(f_stop)}")
            except Exception as e:
                self._print(f"     ❌ APEX calculation failed: {str(e)}")
        
        # Method 3: MaxApertureValue
        max_aperture, _ = self.extract_setting(exif_data, 'MaxApertureValue', 'aperture')
        if max_aperture is not None:
            try:
                max_f_stop = 2 ** (max_aperture / 2)
                aperture_results['MaxApertureValue'] = max_f_stop
                self._print(f"     Max aperture: {self.converter.format_aperture(max_f_stop)}")
            except Exception as e:
                self._print(f"     ❌ Max aperture calculation failed: {str(e)}")
        
        if not aperture_results:
            self._print("  ❌ No usable aperture data found")
        
        return aperture_results
    
    def extract_shutter_speed(self, exif_data):
        """Extract shutter speed values using multiple methods"""
        self._print("\n⚡ SHUTTER SPEED EXTRACTION:")
        shutter_results = {}
        
        # Method 1: ExposureTime (most common)
        exposure_time, _ = self.extract_setting(exif_data, 'ExposureTime', 'shutter')
        if exposure_time is not None:
            shutter_results['ExposureTime'] = exposure_time
            self._print(f"     Decimal seconds: {exposure_time:.6f}")
            self._print(f"     Display format: {self.converter.format_shutter_speed(exposure_time)}")
        
        # Method 2: ShutterSpeedValue (APEX system)
        apex_value, _ = self.extract_setting(exif_data, 'ShutterSpeedValue', 'shutter')
        if apex_value is not None:
            try:
                calculated_time = 2 ** (-apex_value)
                shutter_results['ShutterSpeedValue'] = calculated_time
                self._print(f"     APEX calculation: 2^(-{apex_value}) = {calculated_time:.6f}s")
                self._print(f"     Display format: {self.converter.format_shutter_speed(calculated_time)}")
            except Exception as e:
                self._print(f"     ❌ APEX calculation failed: {str(e)}")
        
        if not shutter_results:
            self._print("  ❌ No usable shutter speed data found")
        
        return shutter_results
    
    def extract_iso(self, exif_data):
        """Extract ISO values using multiple methods"""
        self._print("\n📊 ISO EXTRACTION:")
        iso_results = {}
        
        # List of ISO tags to check
        iso_tags = [
            'ISOSpeedRatings',
            'ISO', 
            'RecommendedExposureIndex',
            'PhotographicSensitivity'
        ]
        
        for tag in iso_tags:
            if tag in exif_data:
                raw_value = exif_data[tag]
                self._print(f"  ✅ {tag} found: {raw_value} (type: {type(raw_value)})")
                
                # Handle array/tuple of ISO values
                if isinstance(raw_value, (list, tuple)):
                    self._print(f"     Multiple values found: {raw_value}")
                    if len(raw_value) > 0:
                        iso_value, conversion_info = self.converter.to_float(raw_value[0], f"{tag}[0]")
                        self._print(f"     Using first value - Conversion: {conversion_info}")
                        if iso_value is not None:
                            iso_results[tag] = iso_value
                            self._print(f"     Final: {self.converter.format_iso(iso_value)}")
                else:
                    iso_value, conversion_info = self.converter.to_float(raw_value, tag)
                    self._print(f"     Conversion: {conversion_info}")
                    if iso_value is not None:
                        iso_results[tag] = iso_value
                        self._print(f"     Final: {self.converter.format_iso(iso_value)}")
        
        if not iso_results:
            self._print("  ❌ No usable ISO data found")
        
        return iso_results
    
    def extract_focal_length(self, exif_data):
        """Extract focal length information"""
        self._print("\n🔍 FOCAL LENGTH EXTRACTION:")
        focal_results = {}
        
        # Standard focal length
        focal_value, _ = self.extract_setting(exif_data, 'FocalLength', 'focal_length')
        if focal_value is not None:
            focal_results['FocalLength'] = focal_value
            self._print(f"     Final focal length: {focal_value:.1f}mm")
        
        # 35mm equivalent focal length
        focal_35mm, _ = self.extract_setting(exif_data, 'FocalLengthIn35mmFilm', 'focal_length_35mm')
        if focal_35mm is not None:
            focal_results['FocalLengthIn35mmFilm'] = focal_35mm
            self._print(f"     35mm equivalent: {focal_35mm:.1f}mm")
        
        if not focal_results:
            self._print("  ❌ No focal length data found")
        
        return focal_results
    
    def extract_exposure_info(self, exif_data):
        """Extract exposure-related information"""
        self._print("\n💡 EXPOSURE INFO EXTRACTION:")
        exposure_results = {}
        
        exposure_fields = {
            'ExposureMode': 'Exposure Mode',
            'ExposureProgram': 'Exposure Program',
            'ExposureBiasValue': 'Exposure Bias',
            'MeteringMode': 'Metering Mode',
            'LightSource': 'Light Source',
            'Flash': 'Flash',
            'WhiteBalance': 'White Balance',
            'SceneCaptureType': 'Scene Type',
            'GainControl': 'Gain Control',
            'Contrast': 'Contrast',
            'Saturation': 'Saturation',
            'Sharpness': 'Sharpness'
        }
        
        for tag, description in exposure_fields.items():
            if tag in exif_data:
                raw_value = exif_data[tag]
                numeric_value, _ = self.converter.to_float(raw_value, tag)
                
                # Decode special values
                decoded_value = raw_value
                if tag == 'Flash' and numeric_value is not None:
                    decoded_value = self.converter.decode_flash_value(numeric_value)
                elif tag == 'MeteringMode' and numeric_value is not None:
                    decoded_value = self.converter.decode_metering_mode(numeric_value)
                elif tag == 'WhiteBalance' and numeric_value is not None:
                    decoded_value = self.converter.decode_white_balance(numeric_value)
                
                exposure_results[tag] = {
                    'raw': raw_value,
                    'numeric': numeric_value,
                    'decoded': decoded_value
                }
                
                self._print(f"  {description:20}: {raw_value} → {decoded_value}")
        
        return exposure_results
    
    def extract_additional_info(self, exif_data):
        """Extract additional camera information"""
        self._print("\n📸 ADDITIONAL CAMERA INFO:")
        
        text_fields = {
            'Make': 'Camera Make',
            'Model': 'Camera Model', 
            'LensModel': 'Lens Model',
            'LensMake': 'Lens Make',
            'Software': 'Software',
            'DateTime': 'Date/Time',
            'DateTimeOriginal': 'Original Date/Time',
            'DateTimeDigitized': 'Digitized Date/Time',
            'Artist': 'Artist',
            'Copyright': 'Copyright',
            'ImageDescription': 'Description'
        }
        
        results = {}
        
        # Extract text fields
        for tag, description in text_fields.items():
            if tag in exif_data:
                value = exif_data[tag]
                if tag in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
                    formatted_value = self.converter.format_datetime(value)
                    results[tag] = {'raw': value, 'formatted': formatted_value}
                    self._print(f"  {description:25}: {formatted_value}")
                else:
                    results[tag] = value
                    self._print(f"  {description:25}: {value}")
        
        return results

class GPSExtractor:
    """Specialized class for GPS data extraction and conversion"""
    
    def __init__(self, verbose=True):
        self.converter = ExifValueConverter()
        self.verbose = verbose
    
    def _print(self, message):
        """Print message only if verbose mode is enabled"""
        if self.verbose:
            print(message)
    
    def extract_gps_info(self, gps_value):
        """Extract and convert GPS information"""
        if not gps_value:
            return None
        
        self._print(f"\n📍 GPS INFORMATION:")
        gps_data = {}
        
        # Extract all GPS tags
        for gps_tag_id, gps_val in gps_value.items():
            gps_tag_name = GPSTAGS.get(gps_tag_id, f"GPS_Unknown_{gps_tag_id}")
            gps_data[gps_tag_name] = gps_val
            self._print(f"    {gps_tag_name:20}: {gps_val}")
        
        # Convert coordinates to decimal if possible
        coordinates = self.convert_gps_to_decimal(gps_data)
        if coordinates['latitude'] is not None and coordinates['longitude'] is not None:
            gps_data['decimal_coordinates'] = coordinates
            self._print(f"    {'Decimal Coords':20}: {coordinates['latitude']:.6f}, {coordinates['longitude']:.6f}")
            
            # Generate map links
            map_links = self.generate_map_links(coordinates['latitude'], coordinates['longitude'])
            gps_data['map_links'] = map_links
            self._print(f"    {'Google Maps':20}: {map_links['google']}")
        
        return gps_data
    
    def convert_gps_to_decimal(self, gps_info):
        """Convert GPS coordinates to decimal degrees with robust error handling"""
        result = {'latitude': None, 'longitude': None, 'altitude': None}
        
        if not gps_info:
            return result
        
        def convert_coordinate(coord_value):
            """Convert individual coordinate from DMS to decimal"""
            if coord_value is None:
                return None
            
            try:
                if isinstance(coord_value, (list, tuple)) and len(coord_value) >= 3:
                    # Handle fractions in GPS coordinates
                    degrees = float(coord_value[0]) if isinstance(coord_value[0], (int, float)) else float(coord_value[0][0]) / float(coord_value[0][1])
                    minutes = float(coord_value[1]) if isinstance(coord_value[1], (int, float)) else float(coord_value[1][0]) / float(coord_value[1][1])
                    seconds = float(coord_value[2]) if isinstance(coord_value[2], (int, float)) else float(coord_value[2][0]) / float(coord_value[2][1])
                    
                    return degrees + (minutes / 60.0) + (seconds / 3600.0)
                else:
                    return float(coord_value)
            except (ValueError, TypeError, ZeroDivisionError) as e:
                self._print(f"    GPS coordinate conversion error: {e}")
                return None
        
        # Convert latitude
        if 'GPSLatitude' in gps_info:
            lat = convert_coordinate(gps_info['GPSLatitude'])
            if lat is not None:
                # Apply direction
                if gps_info.get('GPSLatitudeRef') == 'S':
                    lat = -lat
                result['latitude'] = lat
        
        # Convert longitude
        if 'GPSLongitude' in gps_info:
            lon = convert_coordinate(gps_info['GPSLongitude'])
            if lon is not None:
                # Apply direction
                if gps_info.get('GPSLongitudeRef') == 'W':
                    lon = -lon
                result['longitude'] = lon
        
        # Convert altitude
        if 'GPSAltitude' in gps_info:
            alt = convert_coordinate(gps_info['GPSAltitude'])
            if alt is not None:
                # Apply reference (above/below sea level)
                if gps_info.get('GPSAltitudeRef') == 1:  # Below sea level
                    alt = -alt
                result['altitude'] = alt
        
        return result
    
    def generate_map_links(self, lat, lon):
        """Generate links to various mapping services"""
        return {
            'google': f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
            'openstreetmap': f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=15",
            'bing': f"https://www.bing.com/maps?q={lat},{lon}",
            'apple': f"https://maps.apple.com/?q={lat},{lon}"
        }

class ExifAnalyzer:
    """Main class for comprehensive EXIF analysis"""
    
    def __init__(self, verbose=True):
        self.settings_extractor = CameraSettingsExtractor(verbose)
        self.gps_extractor = GPSExtractor(verbose)
        self.converter = ExifValueConverter()
        self.verbose = verbose
    
    def _print(self, message):
        """Print message only if verbose mode is enabled"""
        if self.verbose:
            print(message)
    
    def analyze_image(self, image_path):
        """Perform complete EXIF analysis on an image"""
        image_path = Path(image_path)
        
        if not image_path.exists():
            self._print(f"❌ File not found: {image_path}")
            return None
        
        try:
            with Image.open(image_path) as img:
                # Basic image info
                self._print(f"📸 Image: {image_path.name}")
                self._print(f"📏 Size: {img.size}")
                self._print(f"🎨 Format: {img.format}")
                self._print(f"🔧 Mode: {img.mode}")
                
                # Try to get file size
                try:
                    file_size = image_path.stat().st_size
                    self._print(f"💾 File Size: {self.format_file_size(file_size)}")
                except:
                    pass
                
                exif_data = img.getexif()
                
                if not exif_data:
                    self._print("❌ No EXIF data found in this image")
                    return {
                        'image_info': {
                            'filename': image_path.name,
                            'size': img.size,
                            'format': img.format,
                            'mode': img.mode,
                            'file_size': getattr(image_path.stat(), 'st_size', None)
                        },
                        'has_exif': False
                    }
                
                self._print(f"✅ Found {len(exif_data)} EXIF tags")
                
                # Convert to readable format
                readable_exif = {}
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, f"Unknown_{tag_id}")
                    readable_exif[tag_name] = value
                
                # Analyze camera settings
                camera_analysis = self.analyze_camera_settings(readable_exif)
                
                # Extract GPS data
                gps_data = None
                if 'GPSInfo' in readable_exif:
                    gps_data = self.gps_extractor.extract_gps_info(readable_exif['GPSInfo'])
                
                # Show all EXIF tags if verbose
                if self.verbose:
                    self.display_all_tags(readable_exif)
                
                return {
                    'image_info': {
                        'filename': image_path.name,
                        'size': img.size,
                        'format': img.format,
                        'mode': img.mode,
                        'file_size': getattr(image_path.stat(), 'st_size', None)
                    },
                    'has_exif': True,
                    'camera_analysis': camera_analysis,
                    'gps_data': gps_data,
                    'all_exif': readable_exif
                }
                
        except Exception as e:
            self._print(f"❌ Error reading image: {str(e)}")
            return None
    
    def analyze_camera_settings(self, exif_data):
        """Analyze all camera settings"""
        self._print("\n📷 CAMERA SETTINGS ANALYSIS")
        self._print("=" * 50)
        
        results = {}
        results['aperture'] = self.settings_extractor.extract_aperture(exif_data)
        results['shutter_speed'] = self.settings_extractor.extract_shutter_speed(exif_data)
        results['iso'] = self.settings_extractor.extract_iso(exif_data)
        results['focal_length'] = self.settings_extractor.extract_focal_length(exif_data)
        results['exposure_info'] = self.settings_extractor.extract_exposure_info(exif_data)
        results['additional_info'] = self.settings_extractor.extract_additional_info(exif_data)
        
        return results
    
    def display_all_tags(self, exif_data):
        """Display all EXIF tags in organized format"""
        self._print(f"\n📋 ALL EXIF TAGS ({len(exif_data)} total)")
        self._print("=" * 50)
        
        for tag_name, value in sorted(exif_data.items()):
            if tag_name != 'GPSInfo':  # GPS is handled separately
                self.display_generic_tag(tag_name, value)
    
    def display_generic_tag(self, tag_name, value):
        """Display a generic EXIF tag"""
        if isinstance(value, bytes):
            display_value = f"<bytes: {len(value)} bytes>"
        elif isinstance(value, (list, tuple)) and len(str(value)) > 80:
            display_value = f"<{type(value).__name__}: {len(value)} items>"
        else:
            display_value = str(value)[:80] + "..." if len(str(value)) > 80 else value
        
        self._print(f"{tag_name:30}: {display_value}")
    
    def format_file_size(self, size_bytes):
        """Format file size in human-readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def generate_summary(self, analysis_results):
        """Generate a concise summary of the analysis"""
        if not analysis_results or not analysis_results.get('has_exif'):
            return "No EXIF data available"
        
        summary = []
        
        # Image info
        img_info = analysis_results['image_info']
        summary.append(f"📸 {img_info['filename']} ({img_info['format']}, {img_info['size'][0]}×{img_info['size'][1]})")
        
        # Camera settings
        camera = analysis_results['camera_analysis']
        
        # Get primary values
        aperture = None
        if camera['aperture'] and 'FNumber' in camera['aperture']:
            aperture = camera['aperture']['FNumber']
        
        shutter = None
        if camera['shutter_speed'] and 'ExposureTime' in camera['shutter_speed']:
            shutter = camera['shutter_speed']['ExposureTime']
        
        iso = None
        if camera['iso']:
            iso_keys = ['ISOSpeedRatings', 'ISO', 'PhotographicSensitivity']
            for key in iso_keys:
                if key in camera['iso']:
                    iso = camera['iso'][key]
                    break
        
        focal = None
        if camera['focal_length'] and 'FocalLength' in camera['focal_length']:
            focal = camera['focal_length']['FocalLength']
        
        # Build settings summary
        settings = []
        if aperture is not None:
            settings.append(f"f/{aperture:.1f}")
        if shutter is not None:
            settings.append(self.converter.format_shutter_speed(shutter))
        if iso is not None:
            settings.append(f"ISO{int(iso)}")
        if focal is not None:
            settings.append(f"{focal:.0f}mm")
        
        if settings:
            summary.append(f"📷 {' • '.join(settings)}")
        
        # Camera info
        if camera['additional_info']:
            make = camera['additional_info'].get('Make')
            model = camera['additional_info'].get('Model')
            if make and model:
                summary.append(f"📱 {make} {model}")
        
        # GPS info
        if analysis_results.get('gps_data') and analysis_results['gps_data'].get('decimal_coordinates'):
            coords = analysis_results['gps_data']['decimal_coordinates']
            if coords['latitude'] and coords['longitude']:
                summary.append(f"📍 {coords['latitude']:.4f}, {coords['longitude']:.4f}")
        
        return '\n'.join(summary)

def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive EXIF data extraction and analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python exif_analyzer.py photo.jpg
  python exif_analyzer.py --quiet --output analysis.json photo.jpg
  python exif_analyzer.py --summary-only *.jpg
        """
    )
    
    parser.add_argument('images', nargs='+', help='Image file(s) to analyze')
    parser.add_argument('--output', '-o', help='Save complete analysis to JSON file')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress verbose output')
    parser.add_argument('--summary-only', '-s', action='store_true', help='Show only summary information')
    parser.add_argument('--no-gps', action='store_true', help='Skip GPS data extraction')
    
    args = parser.parse_args()
    
    if args.summary_only:
        args.quiet = True
    
    print("🔍 COMPREHENSIVE EXIF DATA EXTRACTION TOOL")
    print("=" * 60)
    
    analyzer = ExifAnalyzer(verbose=not args.quiet)
    all_results = {}
    
    for image_path in args.images:
        try:
            if not args.quiet:
                print(f"\n{'='*60}")
            
            results = analyzer.analyze_image(image_path)
            
            if results:
                all_results[image_path] = results
                
                if args.summary_only:
                    print(f"\n{analyzer.generate_summary(results)}")
                elif not args.quiet:
                    print(f"\n✅ Analysis completed successfully!")
                    
                    # Quick summary
                    camera_analysis = results['camera_analysis']
                    total_settings = sum(len(settings) for settings in camera_analysis.values() if isinstance(settings, dict))
                    print(f"📊 Total EXIF tags: {len(results.get('all_exif', {}))}")
                    print(f"📷 Camera settings extracted: {total_settings}")
                    
                    if results.get('gps_data'):
                        print("📍 GPS data found")
            else:
                print(f"\n❌ Could not analyze {image_path}")
                print("Possible reasons:")
                print("  • Image has no EXIF data (processed/stripped)")
                print("  • Image format not supported") 
                print("  • File is corrupted")
                
        except Exception as e:
            print(f"❌ Error processing {image_path}: {str(e)}")
    
    # Save results if requested
    if args.output and all_results:
        try:
            with open(args.output, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)
            print(f"\n💾 Complete analysis saved to: {args.output}")
        except Exception as e:
            print(f"⚠️ Could not save JSON file: {str(e)}")
    
    if all_results:
        print(f"\n🎉 Successfully analyzed {len(all_results)} image(s)")
    else:
        print("\n❌ No images could be analyzed")

if __name__ == "__main__":
    main()