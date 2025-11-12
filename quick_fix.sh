#!/bin/bash

echo -e "\033[1;33m"
echo "╔══════════════════════════════════════╗"
echo "║          Dependency Fixer           ║"
echo "║            Termux Edition           ║"
echo "╚══════════════════════════════════════╝"
echo -e "\033[0m"

echo "[*] Fixing dependencies..."

# Install missing packages
pkg install -y xz-utils libxml2 libxslt clang make

# Fix Ruby gem issues (if Ruby is installed)
if command -v gem &> /dev/null; then
    echo "[*] Configuring Ruby gems..."
    gem install nokogiri -- --use-system-libraries
fi

# Fix Python environment
pip install --upgrade pip setuptools wheel

# Install required Python packages
pip install requests scapy flask twisted netaddr

echo -e "\033[1;32m"
echo "[+] Dependencies fixed!"
echo "[+] Now run: ./install_tools_fixed.sh"
echo -e "\033[0m"
