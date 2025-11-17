#!/bin/bash

echo -e "\033[1;36m"
echo "╔══════════════════════════════════════╗"
echo "║        Complete Security Setup       ║"
echo "║            Termux Edition           ║"
echo "╚══════════════════════════════════════╝"
echo -e "\033[0m"

# Make all scripts executable
chmod +x *.sh *.py 2>/dev/null

# Install dependencies
echo "[*] Installing dependencies..."
pkg update -y
pkg install -y python nmap git bluez bluez-utils net-tools

pip install requests scapy flask twisted bleak

# Create main menu
cat > security_menu.sh << 'EOF'
#!/bin/bash

while true; do
    clear
    echo -e "\033[1;36m"
    echo "╔══════════════════════════════════════╗"
    echo "║        Security Toolkit Menu        ║"
    echo "║            Termux Edition           ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "\033[0m"
    
    echo "1) Network Scanner"
    echo "2) Vulnerability Scanner" 
    echo "3) Advanced Honeypot"
    echo "4) Bluetooth Tools"
    echo "5) Start All Services"
    echo "6) Exit"
    echo
    read -p "Select option (1-6): " choice
    
    case $choice in
        1) ./scan_network.sh ;;
        2) ./vulnerability_scan.sh ;;
        3) python advanced_honeypot.py ;;
        4) ./bluetooth_tools.sh ;;
        5) 
            echo "[*] Starting all services..."
            python advanced_honeypot.py &
            ./bluetooth_monitor.sh &
            echo "[+] Services started in background"
            sleep 2
            ;;
        6) 
            echo "[!] Stopping services..."
            pkill -f advanced_honeypot
            pkill -f bluetooth_monitor
            exit 0
            ;;
        *) echo "[!] Invalid option"; sleep 1 ;;
    esac
    echo
    read -p "Press Enter to continue..."
done
EOF

chmod +x security_menu.sh

echo -e "\033[1;32m"
echo "[+] Setup complete!"
echo "[+] Run: ./security_menu.sh"
echo ""
echo "Available tools:"
echo "• ./scan_network.sh - Network scanning"
echo "• ./vulnerability_scan.sh - Vulnerability scanning" 
echo "• python advanced_honeypot.py - Advanced honeypot"
echo "• ./bluetooth_tools.sh - Bluetooth reconnaissance"
echo "• ./security_menu.sh - Main menu"
echo -e "\033[0m"
