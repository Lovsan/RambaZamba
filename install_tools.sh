#!/bin/bash
echo "[+] Starting security tools installation..."

# Update and upgrade
pkg update -y && pkg upgrade -y

# Install essential dependencies
pkg install -y python git curl wget nmap nodejs rust golang

# Install Python packages
pip install --upgrade pip
pip install requests beautifulsoup4 scapy python-nmap

# Security tools installation
echo "[+] Installing security tools..."

# Nmap (already installed)
echo "[+] Nmap installed"

# Install Masscan
git clone https://github.com/robertdavidgraham/masscan
cd masscan
make
cd ..
echo "[+] Masscan installed"

# Install Nikto
git clone https://github.com/sullo/nikto
echo "[+] Nikto installed"

# Install SQLMap
git clone https://github.com/sqlmapproject/sqlmap
echo "[+] SQLMap installed"

# Install Recon-ng
git clone https://github.com/lanmaster53/recon-ng
echo "[+] Recon-ng installed"

# Install WhatWeb
git clone https://github.com/urbanadventurer/WhatWeb
echo "[+] WhatWeb installed"

# Install Sublist3r
git clone https://github.com/aboul3la/Sublist3r
cd Sublist3r
pip install -r requirements.txt
cd ..
echo "[+] Sublist3r installed"

# Install Dirb (wordlists)
git clone https://github.com/v0re/dirb
echo "[+] Dirb wordlists installed"

# Install Metasploit (Termux version)
wget https://raw.githubusercontent.com/gushmazuko/metasploit_in_termux/master/metasploit.sh
chmod +x metasploit.sh
echo "[+] Metasploit installer downloaded"

echo "[!] Installation complete!"
echo "[!] Run: chmod +x scan_network.sh vulnerability_scan.sh"
echo "[!] Then run: ./scan_network.sh"
