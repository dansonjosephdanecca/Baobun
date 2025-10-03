#!/bin/bash

# Bao Chat Setup Script for Raspberry Pi 400
# This script sets up Bao, your friendly AI chatbot

set -e

echo "🥟 Welcome to Bao Chat Setup!"
echo "Setting up your friendly AI assistant on Raspberry Pi 400..."
echo ""

# Check if running on Raspberry Pi
if [[ ! -f /proc/device-tree/model ]] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: This script is optimized for Raspberry Pi. Some features may not work on other systems."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "📦 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv curl git

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l) -eq 1 ]]; then
    echo "❌ Error: Python 3.8 or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Install Ollama
echo "🤖 Installing Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "✅ Ollama installed successfully"
else
    echo "✅ Ollama already installed"
fi

# Start Ollama service
echo "🚀 Starting Ollama service..."
sudo systemctl enable ollama
sudo systemctl start ollama

# Wait for Ollama to start
echo "⏳ Waiting for Ollama to start..."
sleep 5

# Test Ollama connection
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Error: Could not connect to Ollama. Please check the installation."
    exit 1
fi

echo "✅ Ollama is running"

# Pull TinyLlama model (optimized for Pi 400)
echo "📥 Downloading TinyLlama model (this may take a while)..."
ollama pull tinyllama
echo "✅ TinyLlama model downloaded"

# Create Python virtual environment
echo "🐍 Setting up Python virtual environment..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data

# Set permissions
chmod +x setup.sh

# Create systemd service for Bao Chat (optional)
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/baochat.service > /dev/null <<EOF
[Unit]
Description=Bao Chat - AI Assistant
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python backend/app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
sudo systemctl daemon-reload
sudo systemctl enable baochat

echo ""
echo "🎉 Bao Chat setup complete!"
echo ""
echo "🚀 To start Bao Chat:"
echo "   Option 1 (Manual): source venv/bin/activate && python backend/app.py"
echo "   Option 2 (Service): sudo systemctl start baochat"
echo ""
echo "🌐 Access Bao Chat at: http://localhost:8000"
echo "   Or from another device: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "📋 Next steps:"
echo "   1. Open your web browser and go to the URL above"
echo "   2. Click 'Setup Model' in settings if needed"
echo "   3. Start chatting with Bao!"
echo ""
echo "💡 Tips:"
echo "   - Bao can search the web when you ask current questions"
echo "   - All data is stored locally on your Pi"
echo "   - Use 'sudo systemctl status baochat' to check service status"
echo ""
echo "🥟 Enjoy chatting with Bao!"