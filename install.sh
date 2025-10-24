#!/bin/bash

# Automated Sales Forecasting System - Mac Installer
# This script installs all dependencies and sets up the system

set -e  # Exit on error

echo "=================================================="
echo "Automated Sales Forecasting System - Installation"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This installer is designed for macOS only."
    exit 1
fi

print_success "Running on macOS"

# Check for Homebrew
echo ""
echo "Checking dependencies..."
if ! command -v brew &> /dev/null; then
    print_info "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    print_success "Homebrew installed"
else
    print_success "Homebrew found"
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    print_info "Python 3 not found. Installing Python 3..."
    brew install python@3.11
    print_success "Python 3 installed"
else
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
    print_success "Python $PYTHON_VERSION found"
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    print_info "Node.js not found. Installing Node.js..."
    brew install node
    print_success "Node.js installed"
else
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION found"
fi

# Create virtual environment for Python
echo ""
echo "Setting up Python virtual environment..."
if [ -d "venv" ]; then
    print_info "Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
print_success "Virtual environment created"

# Activate virtual environment
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel
print_success "pip upgraded"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
print_info "This may take several minutes..."
pip install -r backend/requirements.txt
print_success "Python dependencies installed"

# Install Node.js dependencies
echo ""
echo "Installing Node.js dependencies..."
cd frontend
npm install
print_success "Node.js dependencies installed"
cd ..

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p data/uploads
mkdir -p models/generated_code
mkdir -p models/saved_models
mkdir -p database
mkdir -p logs
print_success "Directories created"

# Initialize database
echo ""
echo "Initializing database..."
python backend/database.py
print_success "Database initialized"

# Check for .env file
echo ""
if [ -f ".env" ]; then
    print_success ".env file found"
else
    print_info ".env file not found. Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_info "Please edit .env file and add your ANTHROPIC_API_KEY"
    else
        echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
        print_info "Created .env file. Please add your ANTHROPIC_API_KEY"
    fi
fi

# Make run script executable
echo ""
echo "Setting up run script..."
chmod +x run.sh
print_success "Run script is now executable"

# Installation complete
echo ""
echo "=================================================="
echo "✓ Installation Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Edit the .env file and add your ANTHROPIC_API_KEY:"
echo "   nano .env"
echo ""
echo "2. Start the system:"
echo "   ./run.sh"
echo ""
echo "3. Open your browser to:"
echo "   http://localhost:3000"
echo ""
echo "For more information, see README.md"
echo ""

# Deactivate virtual environment
deactivate
