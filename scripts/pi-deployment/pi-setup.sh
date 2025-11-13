#!/bin/bash
# Initial Raspberry Pi setup script for Printernizer deployment
# Run this once on the Pi to prepare for deployments

set -e

echo "=================================================="
echo "  Printernizer Raspberry Pi Setup"
echo "=================================================="

# Update system
echo -e "\n[1/6] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
if ! command -v docker &> /dev/null; then
    echo -e "\n[2/6] Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker installed"
else
    echo -e "\n[2/6] Docker already installed"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "\n[3/6] Installing Docker Compose..."
    sudo apt install -y docker-compose
    echo "✅ Docker Compose installed"
else
    echo -e "\n[3/6] Docker Compose already installed"
fi

# Create directory structure
echo -e "\n[4/6] Creating directory structure..."
mkdir -p ~/printernizer/{data/{database,thumbnails,files},logs,config}
mkdir -p ~/printernizer_backups
echo "✅ Directories created"

# Install useful tools
echo -e "\n[5/6] Installing additional tools..."
sudo apt install -y curl git htop

# Configure firewall
echo -e "\n[6/6] Configuring firewall..."
if ! command -v ufw &> /dev/null; then
    sudo apt install -y ufw
fi
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 8000/tcp comment 'Printernizer'
sudo ufw --force enable
echo "✅ Firewall configured"

# Display system info
echo -e "\n=================================================="
echo "  Setup Complete!"
echo "=================================================="
echo ""
echo "System Information:"
echo "  Model: $(cat /proc/cpuinfo | grep 'Model' | cut -d: -f2 | xargs)"
echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "  Docker: $(docker --version)"
echo "  IP Address: $(hostname -I | awk '{print $1}')"
echo ""
echo "Next Steps:"
echo "  1. Exit and re-login for Docker group to take effect"
echo "  2. From Windows: .\scripts\pi-deployment\deploy-to-pi.ps1 -PiHost $(hostname -I | awk '{print $1}')"
echo ""
echo "=================================================="
