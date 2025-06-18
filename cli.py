#!/usr/bin/env python3
"""
Quick Start Photography Metadata Analysis Script

This script provides a command-line interface for quickly analyzing
photo metadata without needing to run the full Streamlit dashboard.

Usage:
    python quick_start.py /path/to/photos
    python quick_start.py /path/to/photos --output analysis_report.html
    python quick_start.py /path/to/photos --format json
"""

import argparse
import sys
import os
from pathlib import Path
import json
from datetime import datetime
import webbrowser
import tempfile

# Import our analyzer (assumes it's in same directory)
try:
    from photo_analyzer.photo_metadata_analyzer import PhotoMetadataAnalyzer
except ImportError:
    print("Error: Make sure photo_metadata_analyzer.py is in the same directory")
    sys.exit(1)


def generate_html_report(df, insights, output_path=None):
    """Generate a standalone HTML report"""

    if output_path is None:
        output_path = tempfile.NamedTemporaryFile(suffix=".html", delete=False).name

    # Basic HTML template with embedded CSS
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Photography Portfolio Analysis Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
            h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
            .metric-card { background: #ecf0f1; padding: 20px; border-radius: 8px; text-align: center; }
            .metric-value { font-size: 2em; font-weight: bold; color: #3498db; }
            .metric-label { color: #7f8c8d; margin-top: 5px; }
            .insight-box { background: #e8f6f3; padding: 15px; border-left: 4px solid #1abc9c; margin: 15px 0; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #3498db; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            .charts-note { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📸 Photography Portfolio Analysis</h1>
            <p style="text-align: center; color: #7f8c8d;">Generated on {timestamp}</p>
            
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{total_photos}</div>
                    <div class="metric-label">Total Photos</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{unique_cameras}</div>
                    <div class="metric-label">Cameras Used</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{unique_lenses}</div>
                    <div class="metric-label">Lenses Used</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{gps_photos}</div>
                    <div class="metric-label">GPS Tagged</div>
                </div>
            </div>
            
            <h2>Equipment Usage</h2>
            <div class="insight-box">
                <strong>Most Used Camera:</strong> {most_used_camera}<br>
                <strong>Most Used Lens:</strong> {most_used_lens}<br>
                <strong>Average ISO:</strong> {avg_iso}
            </div>
            
            <h3>Camera Distribution</h3>
            <table>
                <tr><th>Camera</th><th>Photos</th><th>Percentage</th></tr>
                {camera_rows}
            </table>
            
            <h3>Lens Distribution</h3>
            <table>
                <tr><th>Lens</th><th>Photos</th><th>Percentage</th></tr>  
                {lens_rows}
            </table>
            
            <h2>Technical Settings</h2>
            <div class="insight-box">
                <strong>ISO Range:</strong> {iso_range}<br>
                <strong>Most Common ISO:</strong> {common_iso}<br>
                <strong>Date Range:</strong> {date_range}
            </div>
            
            <h2>Shooting Patterns</h2>
            {shooting_patterns}
            
            <div class="charts-note">
                <strong>💡 Pro Tip:</strong> For interactive charts and advanced analytics, 
                run the full Streamlit dashboard with: <code>streamlit run streamlit_dashboard.py</code>
            </div>
            
            <h2>Raw Data Summary</h2>
            <p>First 10 photos from your collection:</p>
            <table>
                <tr>
                    <th>Filename</th><th>Camera</th><th>Lens</th><th>ISO</th><th>Aperture</th><th>Date</th>
                </tr>
                {sample_data_rows}
            </table>
            
            <footer style="margin-top: 40px; text-align: center; color: #7f8c8d; border-top: 1px solid #ecf0f1; padding-top: 20px;">
                <p>Generated by Photography Metadata Analyzer</p>
            </footer>
        </div>
    </body>
    </html>
    """

    # Calculate metrics
    total_photos = len(df)
    unique_cameras = df["camera"].nunique() if "camera" in df.columns else 0
    unique_lenses = df["lens"].nunique() if "lens" in df.columns else 0
    gps_photos = len(df.dropna(subset=["latitude", "longitude"])) if "latitude" in df.columns else 0

    # Most used equipment
    most_used_camera = (
        df["camera"].mode().iloc[0] if "camera" in df.columns and not df["camera"].empty else "N/A"
    )
    most_used_lens = (
        df["lens"].mode().iloc[0] if "lens" in df.columns and not df["lens"].empty else "N/A"
    )
    avg_iso = f"{df['iso'].mean():.0f}" if "iso" in df.columns else "N/A"

    # ISO statistics
    iso_range = f"{df['iso'].min():.0f} - {df['iso'].max():.0f}" if "iso" in df.columns else "N/A"
    common_iso = df["iso"].mode().iloc[0] if "iso" in df.columns and not df["iso"].empty else "N/A"

    # Date range
    if "datetime" in df.columns and not df["datetime"].isna().all():
        date_range = f"{df['datetime'].min().strftime('%Y-%m-%d')} to {df['datetime'].max().strftime('%Y-%m-%d')}"
    else:
        date_range = "N/A"

    # Generate table rows
    def generate_table_rows(series, total):
        rows = []
        for item, count in series.value_counts().head(10).items():
            percentage = (count / total) * 100
            rows.append(f"<tr><td>{item}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>")
        return "\n".join(rows)

    camera_rows = (
        generate_table_rows(df["camera"], total_photos)
        if "camera" in df.columns
        else '<tr><td colspan="3">No camera data</td></tr>'
    )
    lens_rows = (
        generate_table_rows(df["lens"], total_photos)
        if "lens" in df.columns
        else '<tr><td colspan="3">No lens data</td></tr>'
    )

    # Shooting patterns
    shooting_patterns = ""
    if "datetime" in df.columns and not df["datetime"].isna().all():
        df_temp = df.copy()
        df_temp["hour"] = df_temp["datetime"].dt.hour
        peak_hour = df_temp["hour"].mode().iloc[0]
        shooting_patterns = f"""
        <div class="insight-box">
            <strong>Peak Shooting Hour:</strong> {peak_hour}:00<br>
            <strong>Most Active Month:</strong> {df_temp['datetime'].dt.month_name().mode().iloc[0] if not df_temp['datetime'].dt.month_name().empty else 'N/A'}
        </div>
        """
    else:
        shooting_patterns = (
            '<div class="insight-box">No datetime data available for pattern analysis</div>'
        )

    # Sample data rows
    sample_data = df.head(10)
    sample_rows = []
    for _, row in sample_data.iterrows():
        date_str = row.get("datetime", "N/A")
        if pd.notna(date_str) and hasattr(date_str, "strftime"):
            date_str = date_str.strftime("%Y-%m-%d")

        sample_rows.append(
            f"""
        <tr>
            <td>{row.get('filename', 'N/A')}</td>
            <td>{row.get('camera', 'N/A')}</td>
            <td>{row.get('lens', 'N/A')}</td>
            <td>{row.get('iso', 'N/A')}</td>
            <td>{row.get('aperture', 'N/A')}</td>
            <td>{date_str}</td>
        </tr>
        """
        )

    # Fill in the template
    html_content = html_template.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_photos=total_photos,
        unique_cameras=unique_cameras,
        unique_lenses=unique_lenses,
        gps_photos=gps_photos,
        most_used_camera=most_used_camera,
        most_used_lens=most_used_lens,
        avg_iso=avg_iso,
        iso_range=iso_range,
        common_iso=common_iso,
        date_range=date_range,
        camera_rows=camera_rows,
        lens_rows=lens_rows,
        shooting_patterns=shooting_patterns,
        sample_data_rows="\n".join(sample_rows),
    )

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path


def print_summary_report(df, insights):
    """Print a text summary to console"""
    print("\n" + "=" * 60)
    print("📸 PHOTOGRAPHY PORTFOLIO ANALYSIS SUMMARY")
    print("=" * 60)

    # Basic stats
    print(f"\n📊 OVERVIEW:")
    print(f"   Total Photos: {len(df)}")
    print(
        f"   Date Range: {df['datetime'].min().strftime('%Y-%m-%d') if 'datetime' in df.columns and not df['datetime'].isna().all() else 'N/A'} to {df['datetime'].max().strftime('%Y-%m-%d') if 'datetime' in df.columns and not df['datetime'].isna().all() else 'N/A'}"
    )
    print(
        f"   GPS Tagged: {len(df.dropna(subset=['latitude', 'longitude']))} ({(len(df.dropna(subset=['latitude', 'longitude'])) / len(df) * 100):.1f}%)"
        if "latitude" in df.columns
        else "GPS Tagged: 0"
    )

    # Equipment
    print(f"\n📷 EQUIPMENT:")
    if "camera" in df.columns:
        print(f"   Cameras Used: {df['camera'].nunique()}")
        for camera, count in df["camera"].value_counts().head(3).items():
            print(f"     • {camera}: {count} photos ({count/len(df)*100:.1f}%)")

    if "lens" in df.columns:
        print(f"   Lenses Used: {df['lens'].nunique()}")
        for lens, count in df["lens"].value_counts().head(3).items():
            print(f"     • {lens}: {count} photos ({count/len(df)*100:.1f}%)")

    # Settings
    print(f"\n⚙️  CAMERA SETTINGS:")
    if "iso" in df.columns:
        print(f"   ISO Range: {df['iso'].min():.0f} - {df['iso'].max():.0f}")
        print(f"   Average ISO: {df['iso'].mean():.0f}")
        print(f"   Most Common ISO: {df['iso'].mode().iloc[0] if not df['iso'].empty else 'N/A'}")

    if "aperture" in df.columns:
        aperture_counts = df["aperture"].value_counts().head(3)
        print(
            f"   Top Apertures: {', '.join([f'{ap} ({count})' for ap, count in aperture_counts.items()])}"
        )

    # Patterns
    if "datetime" in df.columns and not df["datetime"].isna().all():
        print(f"\n📅 SHOOTING PATTERNS:")
        df_temp = df.copy()
        df_temp["hour"] = df_temp["datetime"].dt.hour
        df_temp["month"] = df_temp["datetime"].dt.month
        print(f"   Peak Hour: {df_temp['hour'].mode().iloc[0]}:00")
        print(
            f"   Most Active Month: {df_temp['datetime'].dt.month_name().mode().iloc[0] if not df_temp['datetime'].dt.month_name().empty else 'N/A'}"
        )

        # Photos per year
        yearly_counts = df_temp["datetime"].dt.year.value_counts().sort_index()
        print(f"   Photos by Year:")
        for year, count in yearly_counts.items():
            print(f"     • {year}: {count} photos")

    print("\n" + "=" * 60)
    print("✨ Analysis complete! Use --output filename.html for detailed report")
    print("🚀 For interactive charts, run: streamlit run streamlit_dashboard.py")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Quick photography metadata analysis")
    parser.add_argument("directory", help="Directory containing photos to analyze")
    parser.add_argument("--output", "-o", help="Output file path (HTML report)")
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "csv", "html"],
        default="console",
        help="Output format (default: console summary)",
    )
    parser.add_argument(
        "--recursive", "-r", action="store_true", help="Recursively search subdirectories"
    )
    parser.add_argument(
        "--open", action="store_true", help="Automatically open HTML report in browser"
    )

    args = parser.parse_args()

    # Validate directory
    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        sys.exit(1)

    # Initialize analyzer
    print(f"🔍 Analyzing photos in: {args.directory}")
    print(f"📁 Recursive search: {'Yes' if args.recursive else 'No'}")

    analyzer = PhotoMetadataAnalyzer()

    try:
        # Process photos
        print("⏳ Processing photos...")
        df = analyzer.process_photo_directory(args.directory, recursive=args.recursive)

        if len(df) == 0:
            print("⚠️  No photos with EXIF data found in the specified directory")
            print("   Make sure the directory contains JPEG/TIFF files with metadata")
            sys.exit(1)

        print(f"✅ Found {len(df)} photos with metadata")

        # Generate insights
        insights = analyzer.generate_insights(df)

        # Output based on format
        if args.format == "console":
            print_summary_report(df, insights)

        elif args.format == "json":
            output_file = (
                args.output or f"photo_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

            # Prepare JSON-serializable data
            export_data = {
                "summary": {
                    "total_photos": len(df),
                    "analysis_date": datetime.now().isoformat(),
                    "directory": args.directory,
                },
                "insights": insights,
                "sample_data": df.head(10).to_dict("records"),
            }

            with open(output_file, "w") as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"📄 JSON report saved to: {output_file}")

        elif args.format == "csv":
            output_file = (
                args.output or f"photo_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            df.to_csv(output_file, index=False)
            print(f"📊 CSV data saved to: {output_file}")

        elif args.format == "html" or args.output:
            output_file = (
                args.output or f"photo_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
            html_path = generate_html_report(df, insights, output_file)
            print(f"📋 HTML report saved to: {html_path}")

            if args.open:
                webbrowser.open(f"file://{os.path.abspath(html_path)}")
                print("🌐 Report opened in your default browser")

    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Add pandas import for the generate_html_report function
    import pandas as pd

    main()
