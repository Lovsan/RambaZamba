#!/usr/bin/env python3
import asyncio
import json
import time
from datetime import datetime
from bleak import BleakScanner
import threading
import os

class RealTimeBluetoothMonitor:
    def __init__(self):
        self.discovered_devices = {}
        self.known_devices = self.load_known_devices()
        self.running = False
        
    def load_known_devices(self):
        try:
            with open("known_devices.json", "r") as f:
                return set(json.load(f))
        except:
            return set()
    
    def save_known_devices(self):
        with open("known_devices.json", "w") as f:
            json.dump(list(self.known_devices), f)
    
    def display_banner(self):
        os.system('clear')
        print("╔══════════════════════════════════════╗")
        print("║       REAL-TIME BLUETOOTH MONITOR   ║")
        print("║            Termux Edition           ║")
        print("╚══════════════════════════════════════╝")
        print()
        print("📱 Monitoring for Bluetooth devices...")
        print("🔄 Scanning every 5 seconds")
        print("💡 Press Ctrl+C to stop")
        print()
        print("{:<18} {:<25} {:<8} {:<12}".format(
            "MAC Address", "Device Name", "RSSI", "First Seen"
        ))
        print("-" * 70)
    
    def update_display(self):
        os.system('clear')
        print("╔══════════════════════════════════════╗")
        print("║       REAL-TIME BLUETOOTH MONITOR   ║")
        print("║            Termux Edition           ║")
        print("╚══════════════════════════════════════╝")
        print()
        print(f"📱 Monitoring - Found {len(self.discovered_devices)} devices")
        print("🔄 Scanning every 5 seconds")
        print("💡 Press Ctrl+C to stop")
        print()
        print("{:<18} {:<25} {:<8} {:<12}".format(
            "MAC Address", "Device Name", "RSSI", "Status"
        ))
        print("-" * 70)
        
        # Sort by most recently seen
        sorted_devices = sorted(
            self.discovered_devices.items(), 
            key=lambda x: x[1]['last_seen'], 
            reverse=True
        )
        
        for mac, info in sorted_devices[:15]:  # Show top 15
            name = info['name'][:24] if info['name'] else "Unknown"
            rssi = info['rssi'] if info['rssi'] else "N/A"
            status = "🆕 NEW!" if info['new'] else "✅ Known"
            
            print("{:<18} {:<25} {:<8} {:<12}".format(
                mac[:17], name, rssi, status
            ))
        
        print("\n💬 Log:")
        self.print_recent_logs()
    
    def print_recent_logs(self):
        try:
            with open("bluetooth_monitor.log", "r") as f:
                lines = f.readlines()[-5:]  # Last 5 lines
                for line in lines:
                    print(line.strip())
        except:
            pass
    
    def log_event(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        with open("bluetooth_monitor.log", "a") as f:
            f.write(log_entry + "\n")
        
        print(f"\r{log_entry}")
    
    async def scan_ble_devices(self):
        try:
            devices = await BleakScanner.discover(timeout=5.0, return_adv=True)
            
            current_scan_macs = set()
            new_devices_found = False
            
            for device, advertising_data in devices.values():
                mac = device.address
                name = device.name or "Unknown"
                rssi = advertising_data.rssi if advertising_data else None
                
                current_scan_macs.add(mac)
                
                if mac not in self.discovered_devices:
                    # New device
                    self.discovered_devices[mac] = {
                        'name': name,
                        'rssi': rssi,
                        'first_seen': datetime.now().strftime("%H:%M:%S"),
                        'last_seen': time.time(),
                        'new': True
                    }
                    self.log_event(f"🆕 NEW DEVICE: {name} ({mac}) RSSI: {rssi}")
                    new_devices_found = True
                    
                else:
                    # Update existing device
                    self.discovered_devices[mac]['last_seen'] = time.time()
                    self.discovered_devices[mac]['rssi'] = rssi
                    if self.discovered_devices[mac]['new']:
                        self.discovered_devices[mac]['new'] = False
            
            # Check for disappeared devices
            disappeared = set(self.discovered_devices.keys()) - current_scan_macs
            for mac in disappeared:
                if time.time() - self.discovered_devices[mac]['last_seen'] > 30:
                    name = self.discovered_devices[mac]['name']
                    self.log_event(f"📵 DEVICE LOST: {name} ({mac})")
                    # Keep in discovered devices but mark as old
            
            return new_devices_found
            
        except Exception as e:
            self.log_event(f"❌ Scan error: {str(e)}")
            return False
    
    async def continuous_scan(self):
        self.running = True
        scan_count = 0
        
        self.display_banner()
        
        while self.running:
            try:
                scan_count += 1
                new_devices = await self.scan_ble_devices()
                
                if new_devices or scan_count % 3 == 0:
                    self.update_display()
                
                await asyncio.sleep(5)
                
            except Exception as e:
                self.log_event(f"❌ Continuous scan error: {str(e)}")
                await asyncio.sleep(5)
    
    def start(self):
        try:
            asyncio.run(self.continuous_scan())
        except KeyboardInterrupt:
            self.running = False
            self.log_event("🛑 Monitoring stopped by user")
            self.save_known_devices()
            print("\n\n💾 Results saved to:")
            print("   - bluetooth_monitor.log")
            print("   - known_devices.json")
            print("\n📊 Summary:")
            print(f"   Total devices found: {len(self.discovered_devices)}")

if __name__ == "__main__":
    monitor = RealTimeBluetoothMonitor()
    monitor.start()
