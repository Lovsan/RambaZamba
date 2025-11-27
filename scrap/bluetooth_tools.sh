#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

display_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════╗"
    echo "║          Bluetooth Tools            ║"
    echo "║            Termux Edition           ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
}

install_bluetooth_tools() {
    echo -e "${YELLOW}[*] Installing Bluetooth tools...${NC}"
    
    pkg update -y
    pkg install -y bluez bluez-utils net-tools python
    
    pip install pybluez bleak bluetooth-numbers
    
    echo -e "${GREEN}[+] Bluetooth tools installed${NC}"
}

scan_bluetooth_devices() {
    echo -e "\n${YELLOW}[*] Scanning for Bluetooth devices...${NC}"
    
    # Check if Bluetooth is available
    if ! hciconfig &> /dev/null; then
        echo -e "${RED}[!] Bluetooth not available or no permissions${NC}"
        echo -e "${YELLOW}[*] Try: termux-bluetooth${NC}"
        return
    fi
    
    echo -e "${BLUE}[*] Starting Bluetooth scan (10 seconds)...${NC}"
    timeout 10s hcitool scan | tee bluetooth_devices.txt
    
    if [ -s bluetooth_devices.txt ]; then
        echo -e "${GREEN}[+] Bluetooth devices saved to bluetooth_devices.txt${NC}"
    else
        echo -e "${RED}[!] No Bluetooth devices found${NC}"
    fi
}

scan_bluetooth_services() {
    echo -e "\n${YELLOW}[*] Scanning for Bluetooth services...${NC}"
    
    if [ ! -f bluetooth_devices.txt ] || [ ! -s bluetooth_devices.txt ]; then
        echo -e "${RED}[!] No devices found. Run scan first.${NC}"
        return
    fi
    
    # Extract MAC addresses
    grep -oE '([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})' bluetooth_devices.txt | while read mac; do
        echo -e "${BLUE}[*] Scanning services for $mac...${NC}"
        sdptool browse "$mac" > "services_$mac.txt" 2>&1
        
        if [ -s "services_$mac.txt" ]; then
            echo -e "${GREEN}[+] Services for $mac saved${NC}"
        else
            rm "services_$mac.txt" 2>&1
        fi
    done
}

bluetooth_recon() {
    echo -e "\n${YELLOW}[*] Bluetooth reconnaissance...${NC}"
    
    cat > bluetooth_recon.py << 'EOF'
#!/usr/bin/env python3
import asyncio
from bleak import BleakScanner
import json
from datetime import datetime

async def scan_ble_devices():
    print("[*] Scanning for BLE devices...")
    
    devices = await BleakScanner.discover()
    
    results = []
    for device in devices:
        device_info = {
            'name': device.name,
            'address': device.address,
            'rssi': device.rssi,
            'details': str(device.details),
            'timestamp': datetime.now().isoformat()
        }
        results.append(device_info)
        
        print(f"[+] {device.name} - {device.address} (RSSI: {device.rssi})")
    
    # Save to JSON
    with open('ble_devices.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"[+] Found {len(devices)} BLE devices")
    print("[+] Results saved to ble_devices.json")

if __name__ == "__main__":
    asyncio.run(scan_ble_devices())
EOF

    python bluetooth_recon.py
}

bluetooth_monitor() {
    echo -e "\n${YELLOW}[*] Starting Bluetooth monitor...${NC}"
    
    cat > bluetooth_monitor.sh << 'EOF'
#!/bin/bash
echo "[*] Bluetooth monitor started..."
echo "[*] Monitoring for new devices..."
echo "[*] Press Ctrl+C to stop"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Scan for devices
    hcitool scan | grep -v Scanning > new_scan.txt
    
    # Compare with previous scan
    if [ -f prev_scan.txt ]; then
        new_devices=$(comm -13 prev_scan.txt new_scan.txt)
        if [ ! -z "$new_devices" ]; then
            echo "[!] NEW DEVICES DETECTED:"
            echo "$new_devices"
            echo "$TIMESTAMP - New device: $new_devices" >> bluetooth_monitor.log
        fi
    fi
    
    mv new_scan.txt prev_scan.txt 2>/dev/null
    sleep 30
done
EOF

    chmod +x bluetooth_monitor.sh
    echo -e "${GREEN}[+] Bluetooth monitor created: bluetooth_monitor.sh${NC}"
    echo -e "${YELLOW}[*] Run: ./bluetooth_monitor.sh${NC}"
}

main() {
    display_banner
    
    echo -e "${GREEN}"
    echo "Select Bluetooth operation:"
    echo "1) Install Bluetooth Tools"
    echo "2) Scan for Devices"
    echo "3) Scan Services"
    echo "4) BLE Reconnaissance"
    echo "5) Start Monitor"
    echo "6) Full Bluetooth Audit"
    echo -e "${NC}"
    
    read -p "Enter choice (1-6): " choice
    
    case $choice in
        1)
            install_bluetooth_tools
            ;;
        2)
            scan_bluetooth_devices
            ;;
        3)
            scan_bluetooth_services
            ;;
        4)
            bluetooth_recon
            ;;
        5)
            bluetooth_monitor
            ;;
        6)
            install_bluetooth_tools
            scan_bluetooth_devices
            scan_bluetooth_services
            bluetooth_recon
            ;;
        *)
            echo -e "${RED}[!] Invalid choice${NC}"
            ;;
    esac
    
    echo -e "\n${GREEN}[+] Bluetooth operations complete!${NC}"
}

main
