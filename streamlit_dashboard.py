import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

import os
import tkinter as tk
from tkinter import filedialog
import threading
import time
import logging
import tempfile
import shutil
import json

from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


from photo_analyzer.photo_metadata_analyzer import PhotoMetadataAnalyzer

# Page configuration
st.set_page_config(
    page_title="Photography Portfolio Analytics",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("photo_analytics.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class FileOperationHandler(FileSystemEventHandler):
    """Watchdog handler to monitor and log file operations"""

    def __init__(self):
        self.operations_log = []
        logger.info("FileOperationHandler initialized")

    def on_modified(self, event):
        if not event.is_directory:
            operation = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "modified",
                "path": event.src_path,
                "size": os.path.getsize(event.src_path) if os.path.exists(event.src_path) else 0,
            }
            self.operations_log.append(operation)
            logger.info(f"File modified: {event.src_path}")

    def on_created(self, event):
        if not event.is_directory:
            operation = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "created",
                "path": event.src_path,
                "size": os.path.getsize(event.src_path) if os.path.exists(event.src_path) else 0,
            }
            self.operations_log.append(operation)
            logger.info(f"File created: {event.src_path}")

    def on_deleted(self, event):
        if not event.is_directory:
            operation = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "deleted",
                "path": event.src_path,
                "size": 0,
            }
            self.operations_log.append(operation)
            logger.info(f"File deleted: {event.src_path}")

    def get_operations_summary(self):
        """Get summary of recent file operations"""
        return {
            "total_operations": len(self.operations_log),
            "recent_operations": self.operations_log[-10:] if self.operations_log else [],
            "operations_by_type": {
                "created": len([op for op in self.operations_log if op["event_type"] == "created"]),
                "modified": len(
                    [op for op in self.operations_log if op["event_type"] == "modified"]
                ),
                "deleted": len([op for op in self.operations_log if op["event_type"] == "deleted"]),
            },
        }


class StagingManager:
    """Manages staging area for file operations with preview capabilities"""

    def __init__(self):
        self.staging_dir = tempfile.mkdtemp(prefix="photo_analytics_staging_")
        self.staged_operations = []
        logger.info(f"StagingManager initialized with staging directory: {self.staging_dir}")

    def stage_csv_creation(self, df, filename_base):
        """Stage a CSV file creation operation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        staged_filename = f"{filename_base}_{timestamp}.csv"
        staged_path = os.path.join(self.staging_dir, staged_filename)

        # Create staged file
        df.to_csv(staged_path, index=False)

        operation = {
            "operation_id": f"csv_{timestamp}",
            "type": "create_csv",
            "staged_path": staged_path,
            "filename": staged_filename,
            "rows": len(df),
            "columns": list(df.columns),
            "size_mb": os.path.getsize(staged_path) / (1024 * 1024),
            "timestamp": datetime.now().isoformat(),
            "status": "staged",
        }

        self.staged_operations.append(operation)
        logger.info(f"CSV creation staged: {staged_filename} ({operation['size_mb']:.2f} MB)")
        return operation

    def stage_json_creation(self, data, filename_base):
        """Stage a JSON file creation operation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        staged_filename = f"{filename_base}_{timestamp}.json"
        staged_path = os.path.join(self.staging_dir, staged_filename)

        # Create staged file
        with open(staged_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        operation = {
            "operation_id": f"json_{timestamp}",
            "type": "create_json",
            "staged_path": staged_path,
            "filename": staged_filename,
            "size_mb": os.path.getsize(staged_path) / (1024 * 1024),
            "timestamp": datetime.now().isoformat(),
            "status": "staged",
        }

        self.staged_operations.append(operation)
        logger.info(f"JSON creation staged: {staged_filename} ({operation['size_mb']:.2f} MB)")
        return operation

    def preview_operation(self, operation_id):
        """Get preview information for a staged operation"""
        operation = next(
            (op for op in self.staged_operations if op["operation_id"] == operation_id), None
        )
        if not operation:
            return None

        preview = {
            "operation": operation,
            "file_exists": os.path.exists(operation["staged_path"]),
            "preview_content": None,
        }

        if operation["type"] == "create_csv":
            # Preview first few rows of CSV
            try:
                df_preview = pd.read_csv(operation["staged_path"]).head(5)
                preview["preview_content"] = df_preview.to_dict("records")
            except Exception as e:
                preview["preview_content"] = f"Error reading CSV: {str(e)}"

        elif operation["type"] == "create_json":
            # Preview JSON structure
            try:
                with open(operation["staged_path"], "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        preview["preview_content"] = {
                            k: str(v)[:100] + "..." if len(str(v)) > 100 else v
                            for k, v in list(data.items())[:5]
                        }
                    else:
                        preview["preview_content"] = (
                            str(data)[:500] + "..." if len(str(data)) > 500 else data
                        )
            except Exception as e:
                preview["preview_content"] = f"Error reading JSON: {str(e)}"

        return preview

    def commit_operation(self, operation_id, target_dir=None):
        """Commit a staged operation to the target directory"""
        operation = next(
            (op for op in self.staged_operations if op["operation_id"] == operation_id), None
        )
        if not operation:
            return False, "Operation not found"

        try:
            if target_dir:
                target_path = os.path.join(target_dir, operation["filename"])
                shutil.copy2(operation["staged_path"], target_path)
                operation["committed_path"] = target_path

            operation["status"] = "committed"
            operation["commit_timestamp"] = datetime.now().isoformat()

            logger.info(
                f"Operation committed: {operation['operation_id']} -> {operation.get('committed_path', 'download only')}"
            )
            return True, "Operation committed successfully"

        except Exception as e:
            logger.error(f"Error committing operation {operation_id}: {str(e)}")
            return False, f"Error: {str(e)}"

    def get_staged_operations(self):
        """Get list of all staged operations"""
        return self.staged_operations

    def cleanup(self):
        """Clean up staging directory"""
        try:
            shutil.rmtree(self.staging_dir)
            logger.info(f"Staging directory cleaned up: {self.staging_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up staging directory: {str(e)}")

    def get_staging_summary(self):
        """Get summary of staging area"""
        return {
            "staging_dir": self.staging_dir,
            "total_operations": len(self.staged_operations),
            "pending_operations": len(
                [op for op in self.staged_operations if op["status"] == "staged"]
            ),
            "committed_operations": len(
                [op for op in self.staged_operations if op["status"] == "committed"]
            ),
            "total_staged_size_mb": sum(op.get("size_mb", 0) for op in self.staged_operations),
        }


st.markdown(
    """
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .insight-box {
        background-color: #e1f5fe;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #01579b;
        margin: 1rem 0;
    }
    .directory-picker {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 2px dashed #dee2e6;
        margin: 1rem 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "df" not in st.session_state:
    st.session_state.df = None
if "analyzer" not in st.session_state:
    st.session_state.analyzer = PhotoMetadataAnalyzer()
if "selected_directory" not in st.session_state:
    st.session_state.selected_directory = ""
if "processing_status" not in st.session_state:
    st.session_state.processing_status = ""
if "file_handler" not in st.session_state:
    st.session_state.file_handler = FileOperationHandler()
if "staging_manager" not in st.session_state:
    st.session_state.staging_manager = StagingManager()
if "observer" not in st.session_state:
    st.session_state.observer = None

# Log application start
logger.info("Streamlit Photo Analytics Dashboard started")


def start_file_monitoring(directory):
    """Start monitoring file operations in the specified directory"""
    try:
        if st.session_state.observer:
            st.session_state.observer.stop()
            st.session_state.observer.join()

        st.session_state.observer = Observer()
        st.session_state.observer.schedule(st.session_state.file_handler, directory, recursive=True)
        st.session_state.observer.start()
        logger.info(f"File monitoring started for directory: {directory}")
        return True
    except Exception as e:
        logger.error(f"Error starting file monitoring: {str(e)}")
        return False


def stop_file_monitoring():
    """Stop file monitoring"""
    try:
        if st.session_state.observer:
            st.session_state.observer.stop()
            st.session_state.observer.join()
            st.session_state.observer = None
            logger.info("File monitoring stopped")
    except Exception as e:
        logger.error(f"Error stopping file monitoring: {str(e)}")


def browse_directory():
    """Open a native directory picker dialog"""
    try:
        logger.info("Opening directory picker dialog")
        # Hide the main tkinter window
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        # Open directory picker
        directory = filedialog.askdirectory(
            title="Select Photo Directory", initialdir=os.path.expanduser("~")
        )

        root.destroy()

        if directory:
            st.session_state.selected_directory = directory
            logger.info(f"Directory selected: {directory}")
            # Start monitoring the selected directory
            start_file_monitoring(directory)
            return directory
        else:
            logger.info("Directory selection cancelled")
        return None
    except Exception as e:
        logger.error(f"Error opening directory picker: {str(e)}")
        st.error(f"Error opening directory picker: {str(e)}")
        return None


def process_directory_async(directory_path, recursive=True):
    """Process directory in a separate thread to avoid blocking UI"""
    try:
        logger.info(
            f"Starting photo processing for directory: {directory_path} (recursive: {recursive})"
        )
        st.session_state.processing_status = "Processing photos..."

        df = st.session_state.analyzer.process_photo_directory(directory_path, recursive=recursive)
        st.session_state.df = df

        logger.info(f"Photo processing completed. Found {len(df)} photos with metadata")
        st.session_state.processing_status = f"✅ Successfully processed {len(df)} photos!"

        # Auto-stage CSV creation
        if len(df) > 0:
            staging_op = st.session_state.staging_manager.stage_csv_creation(df, "photo_metadata")
            logger.info(f"CSV automatically staged: {staging_op['operation_id']}")

        return df
    except Exception as e:
        error_msg = f"Error processing directory: {str(e)}"
        logger.error(error_msg)
        st.session_state.processing_status = f"❌ {error_msg}"
        return None


def load_sample_data():
    """Create sample data for demonstration purposes"""
    np.random.seed(42)
    n_photos = 150

    cameras = ["Canon EOS R5", "Sony A7IV", "Nikon Z6II", "Fujifilm X-T4"]
    lenses = ["24-70mm f/2.8", "70-200mm f/2.8", "50mm f/1.4", "16-35mm f/2.8", "85mm f/1.8"]

    sample_data = []
    for i in range(n_photos):
        # Generate realistic camera settings
        aperture_values = [1.4, 1.8, 2.8, 4.0, 5.6, 8.0, 11.0]
        iso_values = [100, 200, 400, 800, 1600, 3200, 6400]

        # Create datetime with some clustering around certain times
        base_date = datetime(2023, 1, 1)
        days_offset = np.random.randint(0, 365)
        hour = np.random.choice(
            [8, 9, 10, 16, 17, 18, 19, 20], p=[0.1, 0.15, 0.1, 0.15, 0.2, 0.15, 0.1, 0.05]
        )

        sample_data.append(
            {
                "filename": f"IMG_{i+1000:04d}.jpg",
                "camera": np.random.choice(cameras),
                "lens": np.random.choice(lenses),
                "aperture": f"f/{np.random.choice(aperture_values)}",
                "iso": np.random.choice(iso_values),
                "focal_length": f"{np.random.randint(24, 200)}mm",
                "datetime": base_date.replace(day=1) + pd.Timedelta(days=days_offset, hours=hour),
                "latitude": (
                    np.random.uniform(37.7, 37.8) if np.random.random() > 0.3 else None
                ),  # SF area
                "longitude": (
                    np.random.uniform(-122.5, -122.4) if np.random.random() > 0.3 else None
                ),
                "file_size_mb": np.random.uniform(15, 45),
            }
        )

    return pd.DataFrame(sample_data)


def create_camera_usage_chart(df):
    """Create camera usage visualization"""
    camera_counts = df["camera"].value_counts()

    fig = px.pie(
        values=camera_counts.values,
        names=camera_counts.index,
        title="Camera Body Usage Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


def create_lens_usage_chart(df):
    """Create lens usage visualization"""
    lens_counts = df["lens"].value_counts()

    fig = px.bar(
        x=lens_counts.values,
        y=lens_counts.index,
        orientation="h",
        title="Lens Usage Frequency",
        color=lens_counts.values,
        color_continuous_scale="viridis",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


def create_settings_analysis(df):
    """Create camera settings analysis charts"""
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "ISO Distribution",
            "Aperture Usage",
            "Focal Length Distribution",
            "File Size Distribution",
        ),
        specs=[
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": False}],
        ],
    )

    # ISO Distribution
    if "iso" in df.columns:
        iso_counts = df["iso"].value_counts().sort_index()
        fig.add_trace(
            go.Bar(x=iso_counts.index, y=iso_counts.values, name="ISO", marker_color="lightblue"),
            row=1,
            col=1,
        )

    # Aperture Usage
    if "aperture" in df.columns:
        aperture_counts = df["aperture"].value_counts()
        fig.add_trace(
            go.Bar(
                x=aperture_counts.index,
                y=aperture_counts.values,
                name="Aperture",
                marker_color="lightgreen",
            ),
            row=1,
            col=2,
        )

    # Focal Length Distribution
    if "focal_length" in df.columns:
        focal_lengths = df["focal_length"].str.replace("mm", "").astype(float)
        fig.add_trace(
            go.Histogram(
                x=focal_lengths, name="Focal Length", marker_color="lightcoral", nbinsx=20
            ),
            row=2,
            col=1,
        )

    # File Size Distribution
    if "file_size_mb" in df.columns:
        fig.add_trace(
            go.Histogram(
                x=df["file_size_mb"], name="File Size (MB)", marker_color="lightyellow", nbinsx=20
            ),
            row=2,
            col=2,
        )

    fig.update_layout(height=600, showlegend=False, title_text="Camera Settings Analysis")
    return fig


def create_temporal_analysis(df):
    """Create time-based analysis charts"""
    if "datetime" not in df.columns or df["datetime"].isna().all():
        return None

    df["hour"] = df["datetime"].dt.hour
    df["month"] = df["datetime"].dt.month
    df["weekday"] = df["datetime"].dt.day_name()

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Photos by Hour of Day",
            "Photos by Month",
            "Photos by Weekday",
            "Timeline",
        ),
        specs=[
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": False}],
        ],
    )

    # Hour distribution
    hour_counts = df["hour"].value_counts().sort_index()
    fig.add_trace(
        go.Scatter(
            x=hour_counts.index,
            y=hour_counts.values,
            mode="lines+markers",
            name="Hourly",
            line=dict(color="blue"),
        ),
        row=1,
        col=1,
    )

    # Month distribution
    month_counts = df["month"].value_counts().sort_index()
    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    fig.add_trace(
        go.Bar(
            x=[month_names[i - 1] for i in month_counts.index],
            y=month_counts.values,
            name="Monthly",
            marker_color="green",
        ),
        row=1,
        col=2,
    )

    # Weekday distribution
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_counts = df["weekday"].value_counts().reindex(weekday_order, fill_value=0)
    fig.add_trace(
        go.Bar(
            x=weekday_counts.index, y=weekday_counts.values, name="Weekday", marker_color="orange"
        ),
        row=2,
        col=1,
    )

    # Timeline
    df_sorted = df.sort_values("datetime")
    df_sorted["cumulative"] = range(1, len(df_sorted) + 1)
    fig.add_trace(
        go.Scatter(
            x=df_sorted["datetime"],
            y=df_sorted["cumulative"],
            mode="lines",
            name="Cumulative Photos",
            line=dict(color="red"),
        ),
        row=2,
        col=2,
    )

    fig.update_layout(height=600, showlegend=False, title_text="Temporal Shooting Patterns")
    return fig


def create_location_map(df):
    """Create location-based map visualization"""
    gps_df = df.dropna(subset=["latitude", "longitude"])

    if len(gps_df) == 0:
        return None

    fig = px.scatter_mapbox(
        gps_df,
        lat="latitude",
        lon="longitude",
        hover_name="filename",
        hover_data=["camera", "lens"],
        zoom=10,
        height=500,
        title=f"Photo Locations ({len(gps_df)} photos with GPS data)",
    )

    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0})

    return fig


# Main App Interface
def main():
    st.markdown(
        '<h1 class="main-header">📸 Photography Portfolio Analytics</h1>', unsafe_allow_html=True
    )

    # Sidebar for data loading
    st.sidebar.header("📁 Data Source")

    data_source = st.sidebar.radio(
        "Choose data source:", ["🗂️ Browse Photo Directory", "📊 Load Sample Data", "📤 Upload CSV"]
    )

    # Directory Browser Section
    if data_source == "🗂️ Browse Photo Directory":
        st.sidebar.markdown("### Directory Selection")

        # Directory picker button
        if st.sidebar.button("📂 Browse for Photo Directory", key="browse_btn"):
            selected_dir = browse_directory()
            if selected_dir:
                st.sidebar.success(f"Selected: {selected_dir}")

        # Show selected directory
        if st.session_state.selected_directory:
            st.sidebar.markdown(f"**Selected Directory:**")
            st.sidebar.code(st.session_state.selected_directory)

            # Processing options
            recursive = st.sidebar.checkbox("Include subdirectories", value=True)

            # Process button
            if st.sidebar.button("🔄 Process Photos", key="process_btn"):
                if os.path.exists(st.session_state.selected_directory):
                    st.sidebar.spinner("Processing photos...")
                    try:
                        df = st.session_state.analyzer.process_photo_directory(
                            st.session_state.selected_directory, recursive=recursive
                        )
                        st.session_state.df = df

                        if len(df) > 0:
                            st.sidebar.success(f"✅ Processed {len(df)} photos!")

                            # Auto-generate CSV
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            csv_filename = f"photo_metadata_{timestamp}.csv"
                            csv_data = df.to_csv(index=False)

                            st.sidebar.download_button(
                                label="💾 Download Processed CSV",
                                data=csv_data,
                                file_name=csv_filename,
                                mime="text/csv",
                                key="download_processed_csv",
                            )
                        else:
                            st.sidebar.warning("⚠️ No photos with EXIF data found")
                    except Exception as e:
                        st.sidebar.error(f"❌ Error: {str(e)}")
                        logger.error(f"Error processing directory: {str(e)}")
                else:
                    st.sidebar.error("❌ Directory not found!")
        else:
            st.sidebar.info("👆 Click 'Browse for Photo Directory' to select a folder")

    # Sample Data Section
    elif data_source == "📊 Load Sample Data":
        st.sidebar.markdown("### Sample Data")
        st.sidebar.info("Load demo data to explore the dashboard features")

        if st.sidebar.button("🎲 Generate Sample Data"):
            st.session_state.df = load_sample_data()
            st.sidebar.success("✅ Sample data loaded!")

    # CSV Upload Section
    elif data_source == "📤 Upload CSV":
        st.sidebar.markdown("### CSV Upload")
        uploaded_file = st.sidebar.file_uploader(
            "Upload your photo metadata CSV",
            type=["csv"],
            help="Upload a CSV file with photo metadata columns",
        )

        if uploaded_file:
            try:
                st.session_state.df = pd.read_csv(uploaded_file)
                st.sidebar.success(f"✅ CSV loaded! ({len(st.session_state.df)} rows)")
            except Exception as e:
                st.sidebar.error(f"❌ Error loading CSV: {str(e)}")

    # Main dashboard content
    if st.session_state.df is not None:
        df = st.session_state.df

        # Show processing summary if from directory
        if data_source == "🗂️ Browse Photo Directory" and st.session_state.selected_directory:
            st.markdown(
                f"""
            <div class="success-message">
                <strong>📁 Processing Complete!</strong><br>
                Directory: <code>{st.session_state.selected_directory}</code><br>
                Photos processed: <strong>{len(df)}</strong><br>
                Ready for analysis! 🎉
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Photos", len(df))

        with col2:
            unique_cameras = df["camera"].nunique() if "camera" in df.columns else 0
            st.metric("Cameras Used", unique_cameras)

        with col3:
            unique_lenses = df["lens"].nunique() if "lens" in df.columns else 0
            st.metric("Lenses Used", unique_lenses)

        with col4:
            gps_photos = (
                len(df.dropna(subset=["latitude", "longitude"])) if "latitude" in df.columns else 0
            )
            st.metric("GPS Tagged Photos", gps_photos)

        # Quick insights
        if len(df) > 0:
            st.markdown("### 🔍 Quick Insights")

            insights_col1, insights_col2 = st.columns(2)

            with insights_col1:
                if "camera" in df.columns and not df["camera"].empty:
                    most_used_camera = df["camera"].mode().iloc[0]
                    camera_count = df["camera"].value_counts().iloc[0]
                    camera_pct = camera_count / len(df) * 100
                    st.info(
                        f"🎥 Most used camera: **{most_used_camera}** ({camera_count} photos, {camera_pct:.1f}%)"
                    )

            with insights_col2:
                if "iso" in df.columns and not df["iso"].empty:
                    avg_iso = df["iso"].mean()
                    max_iso = df["iso"].max()
                    st.info(f"📊 ISO usage: Average **{avg_iso:.0f}**, Max **{max_iso:.0f}**")

        # Charts
        st.markdown("---")

        # Equipment usage
        col1, col2 = st.columns(2)

        with col1:
            if "camera" in df.columns:
                camera_chart = create_camera_usage_chart(df)
                st.plotly_chart(camera_chart, use_container_width=True)

        with col2:
            if "lens" in df.columns:
                lens_chart = create_lens_usage_chart(df)
                st.plotly_chart(lens_chart, use_container_width=True)

        # Camera settings analysis
        settings_chart = create_settings_analysis(df)
        st.plotly_chart(settings_chart, use_container_width=True)

        # Temporal analysis
        temporal_chart = create_temporal_analysis(df)
        if temporal_chart:
            st.plotly_chart(temporal_chart, use_container_width=True)

        # Location map
        location_map = create_location_map(df)
        if location_map:
            st.plotly_chart(location_map, use_container_width=True)

        # Data export section
        st.markdown("---")
        st.subheader("💾 Export & Download with Staging")

        # Show staging summary
        staging_summary = st.session_state.staging_manager.get_staging_summary()
        operations_summary = st.session_state.file_handler.get_operations_summary()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Staged Operations", staging_summary["pending_operations"])

        with col2:
            st.metric("File Operations", operations_summary["total_operations"])

        with col3:
            st.metric("Staging Size (MB)", f"{staging_summary['total_staged_size_mb']:.2f}")

        # Staging operations section
        st.markdown("### 🎭 Staging Area")

        tab1, tab2, tab3 = st.tabs(["📄 Create New", "👁️ Preview Staged", "📊 File Operations Log"])

        with tab1:
            st.markdown("#### Stage New File Operations")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📊 Stage CSV Export", key="stage_csv"):
                    staging_op = st.session_state.staging_manager.stage_csv_creation(
                        df, "photo_metadata"
                    )
                    st.success(f"✅ CSV staged: {staging_op['filename']}")
                    logger.info(f"User manually staged CSV: {staging_op['operation_id']}")

            with col2:
                if st.button("📋 Stage JSON Export", key="stage_json"):
                    # Create comprehensive JSON export
                    insights = st.session_state.analyzer.generate_insights(df)
                    json_data = {
                        "metadata": {
                            "export_timestamp": datetime.now().isoformat(),
                            "total_photos": len(df),
                            "source_directory": st.session_state.selected_directory,
                        },
                        "insights": insights,
                        "photo_data": df.to_dict("records"),
                    }
                    staging_op = st.session_state.staging_manager.stage_json_creation(
                        json_data, "photo_analysis"
                    )
                    st.success(f"✅ JSON staged: {staging_op['filename']}")
                    logger.info(f"User manually staged JSON: {staging_op['operation_id']}")

        with tab2:
            st.markdown("#### Preview and Commit Staged Operations")

            staged_ops = st.session_state.staging_manager.get_staged_operations()
            pending_ops = [op for op in staged_ops if op["status"] == "staged"]

            if pending_ops:
                for operation in pending_ops:
                    with st.expander(f"📁 {operation['filename']} ({operation['size_mb']:.2f} MB)"):
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.write(f"**Type:** {operation['type']}")
                            st.write(f"**Created:** {operation['timestamp']}")
                            st.write(f"**Size:** {operation['size_mb']:.2f} MB")

                            # Show preview
                            if st.button(f"🔍 Preview", key=f"preview_{operation['operation_id']}"):
                                preview = st.session_state.staging_manager.preview_operation(
                                    operation["operation_id"]
                                )
                                if preview and preview["preview_content"]:
                                    st.json(preview["preview_content"])

                        with col2:
                            # Download staged file
                            if os.path.exists(operation["staged_path"]):
                                with open(operation["staged_path"], "rb") as f:
                                    file_data = f.read()

                                st.download_button(
                                    label="💾 Download",
                                    data=file_data,
                                    file_name=operation["filename"],
                                    mime=(
                                        "text/csv"
                                        if operation["type"] == "create_csv"
                                        else "application/json"
                                    ),
                                    key=f"download_{operation['operation_id']}",
                                )

                                # Mark as committed after download
                                if st.button(
                                    "✅ Mark Committed", key=f"commit_{operation['operation_id']}"
                                ):
                                    success, message = (
                                        st.session_state.staging_manager.commit_operation(
                                            operation["operation_id"]
                                        )
                                    )
                                    if success:
                                        st.success(message)
                                        st.rerun()
                                    else:
                                        st.error(message)
            else:
                st.info(
                    "No pending staged operations. Use 'Create New' tab to stage file operations."
                )

        with tab3:
            st.markdown("#### File Operations Monitor")

            ops_summary = st.session_state.file_handler.get_operations_summary()

            if ops_summary["total_operations"] > 0:
                st.write(f"**Total Operations:** {ops_summary['total_operations']}")
                st.write(f"**Created:** {ops_summary['operations_by_type']['created']}")
                st.write(f"**Modified:** {ops_summary['operations_by_type']['modified']}")
                st.write(f"**Deleted:** {ops_summary['operations_by_type']['deleted']}")

                st.markdown("##### Recent Operations:")
                for op in ops_summary["recent_operations"]:
                    st.text(
                        f"{op['timestamp']} - {op['event_type'].upper()}: {os.path.basename(op['path'])}"
                    )
            else:
                st.info("No file operations detected yet.")

        # Legacy download section (for backward compatibility)
        st.markdown("### 📥 Quick Downloads")
        col1, col2, col3 = st.columns(3)

        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📊 Quick CSV Download",
                data=csv,
                file_name=f"photo_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

        with col2:
            # JSON export
            json_data = df.to_json(orient="records", date_format="iso")
            st.download_button(
                label="📋 Quick JSON Download",
                data=json_data,
                file_name=f"photo_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
            )

        with col3:
            if st.button("👁️ Show Raw Data"):
                st.dataframe(df, use_container_width=True)

    else:
        # Welcome screen
        st.markdown(
            """
        ## 🚀 Welcome to Photography Analytics!
        
        This dashboard helps you analyze your photography portfolio by extracting and visualizing EXIF metadata from your photos.
        
        ### 📋 What You Can Do:
        
        **📁 Browse Photo Directory**: Select any folder containing your photos
        - Automatically extracts EXIF metadata from JPEG/TIFF files
        - Processes camera settings, GPS coordinates, timestamps
        - Generates downloadable CSV for further analysis
        
        **📊 Interactive Analysis**: Explore your photography patterns
        - Equipment usage statistics (cameras & lenses)
        - Camera settings distribution (ISO, aperture, focal length)
        - Temporal shooting patterns (time of day, monthly trends)
        - Geographic distribution of GPS-tagged photos
        
        **💾 Export Options**: Download your data
        - CSV format for spreadsheet analysis
        - JSON format for programmatic use
        - Raw data tables for detailed inspection
        
        ### 🎯 Getting Started:
        
        1. **Browse for a directory** containing your photos using the sidebar
        2. **Process the photos** to extract metadata
        3. **Explore the visualizations** to understand your patterns
        4. **Download the results** for further analysis
        
        ---
        
        *Supported formats: JPEG, TIFF with EXIF data*
        """
        )

        # Show example of what the analysis looks like
        st.markdown("### 🎨 Preview: What Your Analysis Will Look Like")

        if st.button("🎲 See Demo with Sample Data"):
            st.session_state.df = load_sample_data()
            st.rerun()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error in main application: {str(e)}")
    finally:
        # Cleanup on exit
        stop_file_monitoring()
        if "staging_manager" in st.session_state:
            st.session_state.staging_manager.cleanup()
        logger.info("Application cleanup completed")
