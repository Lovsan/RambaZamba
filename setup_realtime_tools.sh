#!/bin/bash

echo -e "\033[1;36m"
echo "╔══════════════════════════════════════╗"
echo "║      REAL-TIME MONITORING SETUP     ║"
echo "║            Termux Edition           ║"
echo "╚══════════════════════════════════════╝"
echo -e "\033[0m"

echo "[*] Installing dependencies..."
pkg update -y
pkg install -y python nmap git bluez bluez-utils

echo "[*] Installing Python packages..."
pip install --upgrade pip
pip install bleak scapy requests

echo "[*] Making scripts executable..."
chmod +x *.py

echo -e "\033[1;32m"
echo "[+] Setup complete!"
echo ""
echo "🎯 Available Real-Time Monitors:"
echo "   📱 Bluetooth: python realtime_bluetooth.py"
echo "   🌐 Network:   python realtime_network.py" 
echo "   🎣 Honeypot:  python active_honeypot.py"
echo "   📊 Dashboard: python master_dashboard.py"
echo ""
echo "🚀 Usage:"
echo "   Run any monitor and it will show live results!"
echo "   Press Ctrl+C to stop any monitor"
echo -e "\033[0m"
