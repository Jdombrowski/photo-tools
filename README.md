# File: README.md

# Location: ./README.md

# Purpose: Complete project documentation with consolidated UV setup

# 📸 Photography Portfolio Analytics

A comprehensive tool for analyzing photography portfolios through EXIF metadata extraction and interactive visualization. Built with Python, Streamlit, and modern data analysis libraries.

## ✨ Features

- **📁 Native Directory Browser**: Point-and-click photo directory selection
- **🎭 Staging System**: Preview and safely commit file operations
- **📊 Interactive Dashboard**: Rich visualizations of your photography patterns
- **⚙️ Command Line Interface**: Batch processing and automation support
- **🔍 File Monitoring**: Real-time tracking of file operations with comprehensive logging
- **💾 Multiple Export Formats**: CSV, JSON, and HTML reports

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **UV Package Manager** (automatically installed during setup)

### One-Command Setup

```bash
# Clone the repository
git clone <repository-url>
cd photography-portfolio-analytics

# Run the setup script (installs UV, creates venv, installs dependencies)
chmod +x setup.sh
./setup.sh

# Start the dashboard
make run
```

### Manual Setup (Alternative)

```bash
# Install UV if not present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
uv sync

# Run the dashboard
uv run streamlit run streamlit_dashboard.py
```

## 📋 Available Commands

The project uses a consolidated Makefile with UV integration. Run `make help` to see all available commands:

```bash
# Core functionality
make setup          # Complete setup for new users
make run             # Start Streamlit dashboard  
make cli DIR=/path   # Run CLI analyzer on directory
make test            # Run basic functionality test

# Environment management
make deps            # Install/update dependencies
make lock            # Lock dependency versions
make update-deps     # Update all dependencies

# Utilities
make sample-data     # Generate test data
make clean           # Clean all build artifacts
make info            # Show project information
make build           # Build package
```

## 🎯 Usage

### 1. Interactive Dashboard

```bash
make run
# Opens browser to http://localhost:8501
```

**Dashboard Features:**

- **Directory Browser**: Native file picker for selecting photo folders
- **Staging Area**: Preview files before download with commit/rollback options
- **Real-time Monitoring**: Track file operations as they happen
- **Interactive Charts**: Equipment usage, settings analysis, temporal patterns
- **Export Options**: Multiple formats with staging preview

### 2. Command Line Interface

```bash
# Analyze a directory and generate HTML report
make cli DIR="/path/to/photos" ARGS="--output report.html --open"

# Generate JSON export
uv run python cli.py /path/to/photos --format json --output analysis.json

# Quick console summary
uv run python cli.py /path/to/photos
```

### 3. Python API

```python
from photo_analyzer.photo_metadata_analyzer import PhotoMetadataAnalyzer

# Initialize analyzer
analyzer = PhotoMetadataAnalyzer()

# Process directory
df = analyzer.process_photo_directory("/path/to/photos", recursive=True)

# Generate insights
insights = analyzer.generate_insights(df)

# Export data
df.to_csv("photo_metadata.csv", index=False)
```

## 📊 What Gets Analyzed

The tool extracts and analyzes:

- **📷 Equipment**: Camera bodies, lenses, and usage statistics
- **⚙️ Camera Settings**: ISO, aperture, shutter speed, focal length
- **📅 Temporal Patterns**: Shooting times, dates, seasonal trends
- **📍 Location Data**: GPS coordinates for geotagged photos
- **📁 File Information**: Sizes, formats, modification dates
- **🎨 Shooting Habits**: Most common settings and patterns

## 🔧 Project Structure

```
photography-portfolio-analytics/
├── photo_analyzer/
│   └── photo_metadata_analyzer.py    # Core analysis engine
├── streamlit_dashboard.py             # Interactive web dashboard
├── cli.py                            # Command line interface
├── logging_config.py                 # Centralized logging setup
├── setup.sh                         # One-command setup script
├── Makefile                          # Consolidated build system
├── pyproject.toml                    # Project configuration
├── uv.lock                           # Locked dependencies
└── logs/                             # Application logs
    ├── photo_analytics_YYYYMMDD.log
    ├── file_operations_YYYYMMDD.log
    └── staging_operations_YYYYMMDD.log
```

## 🛡️ Safety Features

### Staging System

- **Preview Before Commit**: Inspect CSV/JSON content before download
- **Temporary Storage**: All operations staged in isolated temporary directory
- **Operation Tracking**: Unique IDs for all file operations
- **Rollback Support**: Cancel operations before committing

### File Monitoring

- **Real-time Tracking**: Watchdog monitors all file system changes
- **Comprehensive Logging**: Separate logs for different operation types
- **Operation History**: Complete audit trail of all file operations
- **Error Handling**: Graceful handling of file system errors

## 📈 Supported Formats

- **Input**: JPEG, TIFF (with EXIF data)
- **Output**: CSV, JSON, HTML reports
- **Charts**: Interactive Plotly visualizations
- **Maps**: GPS data visualization with OpenStreetMap

## 🔍 Logging and Monitoring

The application provides comprehensive logging:

- **Main Operations**: `logs/photo_analytics_YYYYMMDD.log`
- **File Operations**: `logs/file_operations_YYYYMMDD.log`  
- **Staging Activities**: `logs/staging_operations_YYYYMMDD.log`

View log summary:

```bash
make info  # Shows current project status and recent activity
```

## 🧹 Maintenance

```bash
# Clean temporary files (keep virtual environment)
make clean-cache

# Complete cleanup (removes virtual environment)
make clean

# Update all dependencies
make update-deps
```

## 🐛 Troubleshooting

### Common Issues

**1. UV not found**

```bash
# Install UV manually
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

**2. Virtual environment conflicts**

```bash
# Clean and recreate
make clean
make setup
```

**3. Permission errors with directory browser**

```bash
# Ensure tkinter is installed (usually included with Python)
sudo apt-get install python3-tk  # Ubuntu/Debian
```

**4. No EXIF data found**

- Ensure photos are JPEG/TIFF format
- Check that files haven't been stripped of metadata
- Verify file permissions

### Debug Mode

```bash
# Run with verbose logging
uv run python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from photo_analyzer.photo_metadata_analyzer import PhotoMetadataAnalyzer
analyzer = PhotoMetadataAnalyzer()
df = analyzer.process_photo_directory('/path/to/photos')
"
```

## 📚 Dependencies

Core dependencies (managed by UV):

- **streamlit**: Interactive web dashboard
- **pandas**: Data manipulation and analysis  
- **plotly**: Interactive visualizations
- **pillow**: Image processing and EXIF extraction
- **numpy**: Numerical computations
- **watchdog**: File system monitoring

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes and test**: `make test`
4. **Commit changes**: `git commit -m 'Add amazing feature'`
5. **Push to branch**: `git push origin feature/amazing-feature`
6. **Open Pull Request**

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Pillow/PIL** for EXIF data extraction
- **Streamlit** for the amazing web framework
- **Plotly** for interactive visualizations
- **UV** for fast and reliable Python package management
- **Watchdog** for file system monitoring

---

**Happy analyzing! 📸✨**

For questions or issues, please check the logs in the `logs/` directory or open an issue on GitHub.

# Install UV if not present

curl -LsSf <https://astral.sh/uv/install.sh> | sh

# Create virtual environment and install dependencies

uv venv
uv sync

# Run the dashboard

uv run streamlit run streamlit_dashboard.py

```

## 📋 Available Commands

The project uses a consolidated Makefile with UV integration. Run `make help` to see all available commands:

```bash
# Development workflow
make setup          # Complete setup for new users
make run             # Start Streamlit dashboard  
make cli DIR=/path   # Run CLI analyzer on directory
make test            # Run tests

# Code quality
make format          # Format code with black
make lint            # Lint code with flake8
make typecheck       # Type check with mypy
make check           # Run all quality checks

# Dependencies
make deps            # Install/update dependencies
make lock            # Lock dependency versions
make dev-deps        # Install development dependencies

# Utilities
make sample-data     # Generate test data
make clean           # Clean all build artifacts
make info            # Show project information
```

## 🎯 Usage

### 1. Interactive Dashboard

```bash
make run
# Opens browser to http://localhost:8501
```

**Dashboard Features:**

- **Directory Browser**: Native file picker for selecting photo folders
- **Staging Area**: Preview files before download with commit/rollback options
- **Real-time Monitoring**: Track file operations as they happen
- **Interactive Charts**: Equipment usage, settings analysis, temporal patterns
- **Export Options**: Multiple formats with staging preview

### 2. Command Line Interface

```bash
# Analyze a directory and generate HTML report
make cli DIR="/path/to/photos" ARGS="--output report.html --open"

# Generate JSON export
uv run python cli.py /path/to/photos --format json --output analysis.json

# Quick console summary
uv run python cli.py /path/to/photos
```

### 3. Python API

```python
from photo_analyzer.photo_metadata_analyzer import PhotoMetadataAnalyzer

# Initialize analyzer
analyzer = PhotoMetadataAnalyzer()

# Process directory
df = analyzer.process_photo_directory("/path/to/photos", recursive=True)

# Generate insights
insights = analyzer.generate_insights(df)

# Export data
df.to_csv("photo_metadata.csv", index=False)
```

## 📊 What Gets Analyzed

The tool extracts and analyzes:

- **📷 Equipment**: Camera bodies, lenses, and usage statistics
- **⚙️ Camera Settings**: ISO, aperture, shutter speed, focal length
- **📅 Temporal Patterns**: Shooting times, dates, seasonal trends
- **📍 Location Data**: GPS coordinates for geotagged photos
- **📁 File Information**: Sizes, formats, modification dates
- **🎨 Shooting Habits**: Most common settings and patterns

## 🔧 Project Structure

```
photography-portfolio-analytics/
├── photo_analyzer/
│   └── photo_metadata_analyzer.py    # Core analysis engine
├── streamlit_dashboard.py             # Interactive web dashboard
├── cli.py                            # Command line interface
├── logging_config.py                 # Centralized logging setup
├── setup.sh                         # One-command setup script
├── Makefile                          # Consolidated build system
├── pyproject.toml                    # Project configuration
├── uv.lock                           # Locked dependencies
└── logs/                             # Application logs
    ├── photo_analytics_YYYYMMDD.log
    ├── file_operations_YYYYMMDD.log
    └── staging_operations_YYYYMMDD.log
```

## 🛡️ Safety Features

### Staging System

- **Preview Before Commit**: Inspect CSV/JSON content before download
- **Temporary Storage**: All operations staged in isolated temporary directory
- **Operation Tracking**: Unique IDs for all file operations
- **Rollback Support**: Cancel operations before committing

### File Monitoring

- **Real-time Tracking**: Watchdog monitors all file system changes
- **Comprehensive Logging**: Separate logs for different operation types
- **Operation History**: Complete audit trail of all file operations
- **Error Handling**: Graceful handling of file system errors

## 📈 Supported Formats

- **Input**: JPEG, TIFF (with EXIF data)
- **Output**: CSV, JSON, HTML reports
- **Charts**: Interactive Plotly visualizations
- **Maps**: GPS data visualization with OpenStreetMap

## 🔍 Logging and Monitoring

The application provides comprehensive logging:

- **Main Operations**: `logs/photo_analytics_YYYYMMDD.log`
- **File Operations**: `logs/file_operations_YYYYMMDD.log`  
- **Staging Activities**: `logs/staging_operations_YYYYMMDD.log`

View log summary:

```bash
make info  # Shows current project status and recent activity
```

## 🧹 Maintenance

```bash
# Clean temporary files (keep virtual environment)
make clean-cache

# Complete cleanup (removes virtual environment)
make clean

# Update all dependencies
make update-deps

# Export requirements.txt for compatibility
make export-requirements
```

## 🐛 Troubleshooting

### Common Issues

**1. UV not found**

```bash
# Install UV manually
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or restart terminal
```

**2. Virtual environment conflicts**

```bash
# Clean and recreate
make clean
make setup
```

**3. Permission errors with directory browser**

```bash
# Ensure tkinter is installed (usually included with Python)
sudo apt-get install python3-tk  # Ubuntu/Debian

# Brew
brew install python-tk
```

**4. No EXIF data found**

- Ensure photos are JPEG/TIFF format
- Check that files haven't been stripped of metadata
- Verify file permissions

### Debug Mode

```bash
# Run with verbose logging
uv run python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from photo_analyzer.photo_metadata_analyzer import PhotoMetadataAnalyzer
analyzer = PhotoMetadataAnalyzer()
df = analyzer.process_photo_directory('/path/to/photos')
"
```

## 📚 Dependencies

Core dependencies (managed by UV):

- **streamlit**: Interactive web dashboard
- **pandas**: Data manipulation and analysis  
- **plotly**: Interactive visualizations
- **pillow**: Image processing and EXIF extraction
- **numpy**: Numerical computations
- **watchdog**: File system monitoring

Development dependencies:

- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Code linting
- **mypy**: Type checking

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Pillow/PIL** for EXIF data extraction
- **Streamlit** for the amazing web framework
- **Plotly** for interactive visualizations
- **UV** for fast and reliable Python package management
- **Watchdog** for file system monitoring
