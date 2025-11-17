#!/usr/bin/env python3
import os
import time
import threading
from datetime import datetime

class MasterDashboard:
    def __init__(self):
        self.running = False
        
    def display_dashboard(self):
        while self.running:
            os.system('clear')
            print("╔══════════════════════════════════════╗")
            print("║         MASTER SECURITY DASHBOARD   ║")
            print("║            Termux Edition           ║")
            print("╚══════════════════════════════════════╝")
            print()
            print(f"🕒 Last Update: {datetime.now().strftime('%H:%M:%S')}")
            print()
            
            # Bluetooth Status
            self.show_bluetooth_status()
            print()
            
            # Network Status
            self.show_network_status()
            print()
            
            # Honeypot Status
            self.show_honeypot_status()
            print()
            
            print("💡 Controls: [B]luetooth [N]etwork [H]oneypot [Q]uit")
            
            time.sleep(3)
    
    def show_bluetooth_status(self):
        print("📱 BLUETOOTH MONITOR")
        print("─" * 40)
        
        try:
            if os.path.exists("bluetooth_monitor.log"):
                with open("bluetooth_monitor.log", "r") as f:
                    lines = f.readlines()
                    recent_lines = lines[-3:] if len(lines) >= 3 else lines
                    for line in recent_lines:
                        print(f"   {line.strip()}")
            else:
                print("   💤 Not monitoring")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    def show_network_status(self):
        print("🌐 NETWORK MONITOR")
        print("─" * 40)
        
        try:
            if os.path.exists("network_monitor.log"):
                with open("network_monitor.log", "r") as f:
                    lines = f.readlines()
                    recent_lines = lines[-3:] if len(lines) >= 3 else lines
                    for line in recent_lines:
                        print(f"   {line.strip()}")
            else:
                print("   💤 Not monitoring")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    def show_honeypot_status(self):
        print("🎣 HONEYPOT MONITOR")
        print("─" * 40)
        
        try:
            if os.path.exists("honeypot_monitor.log"):
                with open("honeypot_monitor.log", "r") as f:
                    lines = f.readlines()
                    recent_lines = lines[-3:] if len(lines) >= 3 else lines
                    for line in recent_lines:
                        print(f"   {line.strip()}")
            else:
                print("   💤 Not active")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    def start(self):
        self.running = True
        print("🚀 Starting Master Dashboard...")
        time.sleep(2)
        
        try:
            self.display_dashboard()
        except KeyboardInterrupt:
            self.running = False
            print("\n🛑 Dashboard stopped")

if __name__ == "__main__":
    dashboard = MasterDashboard()
    dashboard.start()
