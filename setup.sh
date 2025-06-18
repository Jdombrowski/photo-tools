set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project info
PROJECT_NAME="Photography Portfolio Analytics"
REQUIRED_PYTHON="3.12"

echo -e "${BLUE}📸 ${PROJECT_NAME} - Setup Script${NC}"
echo "=============================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to compare version numbers
version_ge() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# Check Python version
echo -e "${YELLOW}🐍 Checking Python version...${NC}"
if command_exists python3; then
    PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    echo "Found Python ${PYTHON_VERSION}"
    
    if version_ge "$PYTHON_VERSION" "$REQUIRED_PYTHON"; then
        echo -e "${GREEN}✅ Python version is compatible${NC}"
    else
        echo -e "${RED}❌ Python ${REQUIRED_PYTHON}+ required, found ${PYTHON_VERSION}${NC}"
        echo "Please install Python ${REQUIRED_PYTHON} or higher"
        exit 1
    fi
else
    echo -e "${RED}❌ Python3 not found${NC}"
    echo "Please install Python ${REQUIRED_PYTHON} or higher"
    exit 1
fi

# Install uv if not present
echo -e "${YELLOW}📦 Checking for uv package manager...${NC}"
if ! command_exists uv; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    if command_exists uv; then
        echo -e "${GREEN}✅ uv installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install uv${NC}"
        echo "Please install uv manually: https://github.com/astral-sh/uv"
        exit 1
    fi
else
    echo -e "${GREEN}✅ uv is already installed${NC}"
fi

# Check tkinter availability
echo -e "${YELLOW}🖼️  Checking tkinter for directory picker...${NC}"
if python3 -c "import tkinter" 2>/dev/null; then
    echo -e "${GREEN}✅ tkinter is available${NC}"
else
    echo -e "${YELLOW}⚠️  tkinter not found - installing...${NC}"
    echo "Attempting to install tkinter for Python 3..."
    brew install python-tk@3.12
fi
if [[ ! -f "pyproject.toml" ]]; then
    echo -e "${RED}❌ pyproject.toml not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Create virtual environment and install dependencies
echo -e "${YELLOW}🔧 Setting up virtual environment...${NC}"
uv venv

echo -e "${YELLOW}📚 Installing dependencies...${NC}"
uv sync

# Create logs directory
mkdir -p logs

# Generate sample data for testing
echo -e "${YELLOW}📊 Generating sample data...${NC}"
uv run python -c "
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set seed for reproducible results
np.random.seed(42)

# Generate sample data
cameras = ['Canon EOS R5', 'Sony A7IV', 'Nikon Z6II', 'Fujifilm X-T4']
lenses = ['24-70mm f/2.8', '70-200mm f/2.8', '50mm f/1.4', '16-35mm f/2.8', '85mm f/1.8']
apertures = ['f/1.4', 'f/1.8', 'f/2.8', 'f/4.0', 'f/5.6', 'f/8.0']
isos = [100, 200, 400, 800, 1600, 3200, 6400]

data = []
base_date = datetime(2023, 1, 1)

for i in range(50):
    data.append({
        'filename': f'IMG_{i+1000:04d}.jpg',
        'camera': np.random.choice(cameras),
        'lens': np.random.choice(lenses),
        'aperture': np.random.choice(apertures),
        'iso': np.random.choice(isos),
        'focal_length': f'{np.random.randint(24, 200)}mm',
        'datetime': base_date + timedelta(days=np.random.randint(0, 365)),
        'latitude': np.random.uniform(37.7, 37.8) if np.random.random() > 0.3 else None,
        'longitude': np.random.uniform(-122.5, -122.4) if np.random.random() > 0.3 else None,
        'file_size_mb': np.random.uniform(15, 45)
    })

df = pd.DataFrame(data)
df.to_csv('sample_metadata.csv', index=False)
print(f'Sample data generated: {len(df)} photos')
"

# Check if Streamlit can be imported
echo -e "${YELLOW}🧪 Testing installation...${NC}"
if uv run python -c "import streamlit, pandas, plotly; print('All dependencies imported successfully')" 2>/dev/null; then
    echo -e "${GREEN}✅ Installation test passed${NC}"
else
    echo -e "${RED}❌ Installation test failed${NC}"
    echo "Some dependencies may not be installed correctly"
    exit 1
fi

# Final success message
echo ""
echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}You can now:${NC}"
echo "  • Run the dashboard:    ${YELLOW}make run${NC}     or    ${YELLOW}uv run streamlit run streamlit_dashboard.py${NC}"
echo "  • Analyze photos:       ${YELLOW}make cli DIR=/path/to/photos${NC}"
echo "  • View all commands:    ${YELLOW}make help${NC}"
echo "  • Test with sample:     ${YELLOW}make run${NC} (then load sample_metadata.csv)"
echo ""
echo -e "${BLUE}Quick Start:${NC}"
echo "  1. Run: ${YELLOW}make run${NC}"
echo "  2. Open browser to: http://localhost:8501"
echo "  3. Select 'Upload CSV' and upload sample_metadata.csv"
echo "  4. Explore your photo analytics!"
echo ""
echo -e "${YELLOW}📁 Sample data created: sample_metadata.csv${NC}"
echo -e "${YELLOW}📋 Check 'make help' for all available commands${NC}"