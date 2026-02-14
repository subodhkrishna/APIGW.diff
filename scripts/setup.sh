#!/bin/bash
# Setup script for API Gateway Comparison Testing Framework

set -e

echo "Setting up API Gateway Comparison Testing Framework..."

# Check Python version
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy example files
if [ ! -f ".env" ]; then
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "Please edit .env with your gateway configurations"
fi

echo ""
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Configure your gateways in config/gateways.yaml"
echo "3. Set environment variables in .env"
echo "4. Run tests: python main.py test run"
echo ""
echo "For a quick start: python main.py test list"
