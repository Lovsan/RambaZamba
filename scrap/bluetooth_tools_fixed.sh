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

check_bluetooth() {
    echo -e "${YELLOW}[*] Checking Bluetooth capabilities...${NC}"
    
    # Check if Bluetooth is available in Termux
    if ! termux-bluetooth-info &> /dev/null; then
        echo -e "${RED}[!] Bluetooth not available in Termux${NC}"
        echo -e "${YELLOW}[*] Note: Bluetooth access in Termux may be limited${NC}"
        return 1
    fi
    
    echo -e "${GREEN}[+] Bluetooth is available${NC}"
    return 0
}

scan_bluetooth_devices() {
    echo -e "\n${YELLOW}[*] Scanning for Bluetooth devices...${NC}"
    
    # Use termux-bluetooth if available
    if command -v termux-bluetooth-scan &> /dev/null; then
        echo -e "${BLUE}[*] Starting Bluetooth scan (15 seconds)...${NC}"
        timeout 15s termux-bluetooth-scan > bluetooth_devices.txt 2>&1 &
        scan_pid=$!
        
        # Show progress
        for i in {1..15}; do
            echo -n "."
            sleep 1
        done
        echo
        
        wait $scan_pid
        echo -e "${GREEN}[+] Bluetooth scan completed${NC}"
    else
        echo -e "${YELLOW}[*] Using alternative Bluetooth scanning method...${NC}"
        python3 -c "
import asyncio
from bleak import BleakScanner
import json
from datetime import datetime

async def scan():
    print('[*] Scanning for BLE devices (10 seconds)...')
    devices = await BleakScanner.discover(timeout=10)
    results = []
    for device in devices:
        info = {
            'name': device.name or 'Unknown',
            'address': device.address,
            'rssi': device.rssi,
            'timestamp': datetime.now().isoformat()
        }
        results.append(info)
        print(f'[+] {device.name} - {device.address} (RSSI: {device.rssi})')
    
    with open('ble_devices.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f'[+] Found {len(devices)} BLE devices')

asyncio.run(scan())
" > ble_scan.txt 2>&1
        echo -e "${GREEN}[+] BLE scan completed${NC}"
    fi
}

bluetooth_recon() {
    echo -e "\n${YELLOW}[*] Performing Bluetooth reconnaissance...${NC}"
    
    cat > simple_ble_scan.py << 'EOF'
#!/usr/bin/env python3
import asyncio
from bleak import BleakScanner
import json
from datetime import datetime

async def main():
    print("[*] Scanning for Bluetooth devices...")
    print("[*] This will take 10 seconds...")
    
    devices = await BleakScanner.discover(timeout=10.0, return_adv=True)
    
    found_devices = []
    for device, adv in devices.values():
        device_info = {
            "name": device.name or "Unknown",
            "address": device.address,
            "rssi": adv.rssi,
            "timestamp": datetime.now().isoformat()
        }
        found_devices.append(device_info)
        
        print(f"[DEVICE] {device.name} - {device.address} (RSSI: {adv.rssi})")
    
    # Save results
    with open("bluetooth_scan.json", "w") as f:
        json.dump(found_devices, f, indent=2)
    
    print(f"\n[+] Found {len(found_devices)} Bluetooth devices")
    print("[+] Results saved to bluetooth_scan.json")

if __name__ == "__main__":
    asyncio.run(main())
EOF

    python3 simple_ble_scan.py
}

bluetooth_monitor() {
    echo -e "\n${YELLOW}[*] Setting up Bluetooth device monitor...${NC}"
    
    cat > bluetooth_watcher.py << 'EOF'
#!/usr/bin/env python3
import time
import json
from datetime import datetime

def monitor_bluetooth():
    known_devices = set()
    
    try:
        with open("known_devices.json", "r") as f:
            known_devices = set(json.load(f))
    except:
        pass
    
    print("[*] Bluetooth device watcher started...")
    print("[*] Monitoring for new devices...")
    print("[*] Press Ctrl+C to stop")
    
    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"[{current_time}] Scanning...")
            
            # In a real implementation, you would scan for devices here
            # For demo purposes, we'll simulate device detection
            
            time.sleep(30)  # Scan every 30 seconds
            
    except KeyboardInterrupt:
        print("\n[!] Stopping Bluetooth watcher...")
        # Save known devices
        with open("known_devices.json", "w") as f:
            json.dump(list(known_devices), f)

if __name__ == "__main__":
    monitor_bluetooth()
EOF

    echo -e "${GREEN}[+] Bluetooth monitor created${NC}"
    echo -e "${YELLOW}[*] Run: python3 bluetooth_watcher.py${NC}"
}

install_bluetooth_deps() {
    echo -e "${YELLOW}[*] Installing Bluetooth dependencies...${NC}"
    
    pkg install -y python rust
    pip install bleak
    
    echo -e "${GREEN}[+] Bluetooth dependencies installed${NC}"
}

main() {
    display_banner
    
    echo -e "${GREEN}"
    echo "Select Bluetooth operation:"
    echo "1) Install Dependencies"
    echo "2) Scan for Devices"
    echo "3) BLE Reconnaissance"
    echo "4) Start Device Monitor"
    echo "5) Full Bluetooth Audit"
    echo -e "${NC}"
    
    read -p "Enter choice (1-5): " choice
    
    case $choice in
        1)
            install_bluetooth_deps
            ;;
        2)
            scan_bluetooth_devices
            ;;
        3)
            bluetooth_recon
            ;;
        4)
            bluetooth_monitor
            ;;
        5)
            install_bluetooth_deps
            scan_bluetooth_devices
            bluetooth_recon
            bluetooth_monitor
            ;;
        *)
            echo -e "${RED}[!] Invalid choice${NC}"
            ;;
    esac
    
    echo -e "\n${GREEN}[+] Bluetooth operations complete!${NC}"
}

main
