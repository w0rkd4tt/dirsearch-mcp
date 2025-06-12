#!/bin/bash
# Setup script for dirsearch-mcp

echo "Setting up Dirsearch MCP..."
echo "=========================="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the test
echo ""
echo "Running current state test..."
echo "=========================="
python test_current_state.py

echo ""
echo "Setup complete!"
echo ""
echo "To use dirsearch-mcp:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the CLI: python main.py"
echo "3. Or use as a library - see examples/simple_integration.py"