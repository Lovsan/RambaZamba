#!/bin/bash

echo -e "\033[1;36m"
echo "╔══════════════════════════════════════╗"
echo "║     Termux Toolkit Installation     ║"
echo "║            Complete Setup           ║"
echo "╚══════════════════════════════════════╝"
echo -e "\033[0m"

echo "[*] Starting installation..."

# Update packages
echo "[*] Updating packages..."
pkg update -y && pkg upgrade -y

# Install dependencies
echo "[*] Installing dependencies..."
pkg install -y python nmap git bluez bluez-utils sqlite openssh

# Install Python packages
echo "[*] Installing Python packages..."
pip install --upgrade pip
pip install paramiko pillow pyautogui scapy requests flask

# Create directory structure
echo "[*] Creating directory structure..."
mkdir -p logs backups database config

# Make scripts executable
echo "[*] Setting up scripts..."
chmod +x *.py

# Initialize database
echo "[*] Initializing database..."
python system_manager.py --init-only

echo -e "\033[1;32m"
echo "[+] Installation complete!"
echo ""
echo "🎯 Available Tools:"
echo "   🛠️  System Manager: python system_manager.py"
echo "   📱 Bluetooth Monitor: python realtime_bluetooth.py"
echo "   🌐 Network Scanner: python realtime_network.py"
echo "   🎣 Honeypot: python active_honeypot.py"
echo "   📊 Dashboard: python dashboard.py"
echo ""
echo "🚀 Quick Start:"
echo "   1. Run: python system_manager.py"
echo "   2. Add your systems using the menu"
echo "   3. Start monitoring and managing!"
echo -e "\033[0m"
