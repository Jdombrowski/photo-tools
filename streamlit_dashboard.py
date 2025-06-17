import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import os
# from pathlib import Path

# Import our custom analyzer
from photo_analyzer.photo_metadata_analyzer import PhotoMetadataAnalyzer

# Page configuration
st.set_page_config(
    page_title="Photography Portfolio Analytics",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = PhotoMetadataAnalyzer()

def load_sample_data():
    """Create sample data for demonstration purposes"""
    np.random.seed(42)
    n_photos = 150
    
    cameras = ['Canon EOS R5', 'Sony A7IV', 'Nikon Z6II', 'Fujifilm X-T4']
    lenses = ['24-70mm f/2.8', '70-200mm f/2.8', '50mm f/1.4', '16-35mm f/2.8', '85mm f/1.8']
    
    sample_data = []
    for i in range(n_photos):
        # Generate realistic camera settings
        aperture_values = [1.4, 1.8, 2.8, 4.0, 5.6, 8.0, 11.0]
        iso_values = [100, 200, 400, 800, 1600, 3200, 6400]
        
        # Create datetime with some clustering around certain times
        base_date = datetime(2023, 1, 1)
        days_offset = np.random.randint(0, 365)
        hour = np.random.choice([8, 9, 10, 16, 17, 18, 19, 20], p=[0.1, 0.15, 0.1, 0.15, 0.2, 0.15, 0.1, 0.05])
        
        sample_data.append({
            'filename': f'IMG_{i+1000:04d}.jpg',
            'camera': np.random.choice(cameras),
            'lens': np.random.choice(lenses),
            'aperture': f"f/{np.random.choice(aperture_values)}",
            'iso': np.random.choice(iso_values),
            'focal_length': f"{np.random.randint(24, 200)}mm",
            'datetime': base_date.replace(day=1) + pd.Timedelta(days=days_offset, hours=hour),
            'latitude': np.random.uniform(37.7, 37.8) if np.random.random() > 0.3 else None,  # SF area
            'longitude': np.random.uniform(-122.5, -122.4) if np.random.random() > 0.3 else None,
            'file_size_mb': np.random.uniform(15, 45)
        })
    
    return pd.DataFrame(sample_data)

def create_camera_usage_chart(df):
    """Create camera usage visualization"""
    camera_counts = df['camera'].value_counts()
    
    fig = px.pie(
        values=camera_counts.values,
        names=camera_counts.index,
        title="Camera Body Usage Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_lens_usage_chart(df):
    """Create lens usage visualization"""
    lens_counts = df['lens'].value_counts()
    
    fig = px.bar(
        x=lens_counts.values,
        y=lens_counts.index,
        orientation='h',
        title="Lens Usage Frequency",
        color=lens_counts.values,
        color_continuous_scale='viridis'
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    return fig

def create_settings_analysis(df):
    """Create camera settings analysis charts"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('ISO Distribution', 'Aperture Usage', 'Focal Length Distribution', 'File Size Distribution'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # ISO Distribution
    if 'iso' in df.columns:
        iso_counts = df['iso'].value_counts().sort_index()
        fig.add_trace(
            go.Bar(x=iso_counts.index, y=iso_counts.values, name='ISO', marker_color='lightblue'),
            row=1, col=1
        )
    
    # Aperture Usage
    if 'aperture' in df.columns:
        aperture_counts = df['aperture'].value_counts()
        fig.add_trace(
            go.Bar(x=aperture_counts.index, y=aperture_counts.values, name='Aperture', marker_color='lightgreen'),
            row=1, col=2
        )
    
    # Focal Length Distribution
    if 'focal_length' in df.columns:
        focal_lengths = df['focal_length'].str.replace('mm', '').astype(float)
        fig.add_trace(
            go.Histogram(x=focal_lengths, name='Focal Length', marker_color='lightcoral', nbinsx=20),
            row=2, col=1
        )
    
    # File Size Distribution
    if 'file_size_mb' in df.columns:
        fig.add_trace(
            go.Histogram(x=df['file_size_mb'], name='File Size (MB)', marker_color='lightyellow', nbinsx=20),
            row=2, col=2
        )
    
    fig.update_layout(height=600, showlegend=False, title_text="Camera Settings Analysis")
    return fig

def create_temporal_analysis(df):
    """Create time-based analysis charts"""
    if 'datetime' not in df.columns or df['datetime'].isna().all():
        return None
    
    df['hour'] = df['datetime'].dt.hour
    df['month'] = df['datetime'].dt.month
    df['weekday'] = df['datetime'].dt.day_name()
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Photos by Hour of Day', 'Photos by Month', 'Photos by Weekday', 'Timeline'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Hour distribution
    hour_counts = df['hour'].value_counts().sort_index()
    fig.add_trace(
        go.Scatter(x=hour_counts.index, y=hour_counts.values, mode='lines+markers', 
                  name='Hourly', line=dict(color='blue')),
        row=1, col=1
    )
    
    # Month distribution
    month_counts = df['month'].value_counts().sort_index()
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    fig.add_trace(
        go.Bar(x=[month_names[i-1] for i in month_counts.index], y=month_counts.values, 
               name='Monthly', marker_color='green'),
        row=1, col=2
    )
    
    # Weekday distribution
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_counts = df['weekday'].value_counts().reindex(weekday_order, fill_value=0)
    fig.add_trace(
        go.Bar(x=weekday_counts.index, y=weekday_counts.values, 
               name='Weekday', marker_color='orange'),
        row=2, col=1
    )
    
    # Timeline
    df_sorted = df.sort_values('datetime')
    df_sorted['cumulative'] = range(1, len(df_sorted) + 1)
    fig.add_trace(
        go.Scatter(x=df_sorted['datetime'], y=df_sorted['cumulative'], 
                  mode='lines', name='Cumulative Photos', line=dict(color='red')),
        row=2, col=2
    )
    
    fig.update_layout(height=600, showlegend=False, title_text="Temporal Shooting Patterns")
    return fig

def create_location_map(df):
    """Create location-based map visualization"""
    gps_df = df.dropna(subset=['latitude', 'longitude'])
    
    if len(gps_df) == 0:
        return None
    
    fig = px.scatter_map(
        gps_df,
        lat='latitude',
        lon='longitude',
        hover_name='filename',
        hover_data=['camera', 'lens'],
        zoom=10,
        height=500,
        title=f"Photo Locations ({len(gps_df)} photos with GPS data)"
    )
    
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})
    
    return fig

# Main App Interface
def main():
    st.markdown('<h1 class="main-header">📸 Photography Portfolio Analytics</h1>', unsafe_allow_html=True)
    
    # Sidebar for data loading
    st.sidebar.header("Data Source")
    
    data_source = st.sidebar.radio(
        "Choose data source:",
        ["Load Sample Data", "Upload CSV", "Process Photo Directory"]
    )
    
    if data_source == "Load Sample Data":
        if st.sidebar.button("Generate Sample Data"):
            st.session_state.df = load_sample_data()
            st.sidebar.success("Sample data loaded!")
    
    elif data_source == "Upload CSV":
        uploaded_file = st.sidebar.file_uploader("Upload your photo metadata CSV", type=['csv'])
        if uploaded_file:
            st.session_state.df = pd.read_csv(uploaded_file)
            st.sidebar.success("CSV loaded!")
    
    elif data_source == "Process Photo Directory":
        directory_path = st.sidebar.text_input("Enter photo directory path:")
        if st.sidebar.button("Process Directory") and directory_path:
            if os.path.exists(directory_path):
                spinner = st.sidebar.spinner("Processing photos...")
                st.session_state.df = st.session_state.analyzer.process_photo_directory(directory_path)
                spinner.empty()
                st.sidebar.success(f"Processed {len(st.session_state.df)} photos!")
            else:
                st.sidebar.error("Directory not found!")
    
    # Main dashboard
    if st.session_state.df is not None:
        df = st.session_state.df
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Photos", len(df))
        
        with col2:
            unique_cameras = df['camera'].nunique() if 'camera' in df.columns else 0
            st.metric("Cameras Used", unique_cameras)
        
        with col3:
            unique_lenses = df['lens'].nunique() if 'lens' in df.columns else 0
            st.metric("Lenses Used", unique_lenses)
        
        with col4:
            gps_photos = len(df.dropna(subset=['latitude', 'longitude'])) if 'latitude' in df.columns else 0
            st.metric("GPS Tagged Photos", gps_photos)
        
        # Charts
        st.markdown("---")
        
        # Equipment usage
        col1, col2 = st.columns(2)
        
        with col1:
            camera_chart = create_camera_usage_chart(df)
            st.plotly_chart(camera_chart, use_container_width=True)
        
        with col2:
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
        
        # Data export
        st.markdown("---")
        st.subheader("Export Data")
        
        col1, col2 = st.columns(2)
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"photo_metadata_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col2:
            if st.button("Show Raw Data"):
                st.dataframe(df)
    
    else:
        st.info("👆 Select a data source from the sidebar to get started!")
        
        # Show information about EXIF data
        st.markdown("""
        ## What This Dashboard Shows
        
        This photography analytics dashboard helps you understand your shooting patterns by analyzing EXIF metadata from your photos:
        
        **📊 Equipment Usage**: See which cameras and lenses you use most frequently
        
        **⚙️ Camera Settings**: Analyze your aperture, ISO, and focal length preferences
        
        **📅 Temporal Patterns**: Discover when you shoot most (time of day, month, weekday)
        
        **📍 Location Insights**: Visualize where your GPS-tagged photos were taken
        
        **💾 Data Export**: Download your metadata for further analysis
        
        ### Getting Started
        1. Use "Load Sample Data" to see the dashboard in action
        2. Process your own photo directory to analyze your portfolio
        3. Upload a pre-processed CSV if you have metadata already extracted
        """)

if __name__ == "__main__":
    main()