#!/bin/bash
echo "[+] Starting security tools installation (Fixed Version)..."

# Update and upgrade
pkg update -y && pkg upgrade -y

# Install essential dependencies (avoid Ruby issues)
pkg install -y python git curl wget nmap nodejs golang clang make \
               libxml2 libxslt libffi openssl termux-api

# Install xz-utils to fix the xzcat error
pkg install -y xz-utils

# Setup Python environment
pip install --upgrade pip
pip install wheel setuptools

# Install Python packages (avoid problematic native compilations)
echo "[+] Installing Python packages..."
pip install requests beautifulsoup4 scapy python-nmap flask twisted \
            netaddr pyinotify psutil pybluez

# Security tools installation
echo "[+] Installing security tools..."

# Nmap (already installed)
echo "[+] Nmap installed"

# Install Masscan
if [ ! -d "masscan" ]; then
    git clone https://github.com/robertdavidgraham/masscan
    cd masscan
    make
    cd ..
    echo "[+] Masscan installed"
else
    echo "[+] Masscan already exists"
fi

# Install Nikto
if [ ! -d "nikto" ]; then
    git clone https://github.com/sullo/nikto
    echo "[+] Nikto installed"
else
    echo "[+] Nikto already exists"
fi

# Install SQLMap
if [ ! -d "sqlmap" ]; then
    git clone https://github.com/sqlmapproject/sqlmap
    echo "[+] SQLMap installed"
else
    echo "[+] SQLMap already exists"
fi

# Install WhatWeb
if [ ! -d "WhatWeb" ]; then
    git clone https://github.com/urbanadventurer/WhatWeb
    echo "[+] WhatWeb installed"
else
    echo "[+] WhatWeb already exists"
fi

# Install Sublist3r
if [ ! -d "Sublist3r" ]; then
    git clone https://github.com/aboul3la/Sublist3r
    cd Sublist3r
    pip install -r requirements.txt
    cd ..
    echo "[+] Sublist3r installed"
else
    echo "[+] Sublist3r already exists"
fi

# Install Honeypot tools
echo "[+] Installing honeypot tools..."

# Install simplified honeypot dependencies
pip install cryptography pyopenssl

# Install Monitoring tools
echo "[+] Installing monitoring tools..."

# Install Network monitoring tools
pip install pyattacker netifaces

# Install Bluetooth tools
echo "[+] Installing Bluetooth tools..."
pkg install -y bluez bluez-utils
pip install bleak

# Create essential directories
mkdir -p sessions logs

echo "[!] Installation complete!"
echo "[!] Available tools:"
echo "  - Network Scanner: ./scan_network.sh"
echo "  - Honeypot: python advanced_honeypot.py"
echo "  - Bluetooth Tools: ./bluetooth_tools.sh"
echo "  - Vulnerability Scanner: ./vulnerability_scan.sh"
