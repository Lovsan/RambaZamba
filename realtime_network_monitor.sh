#!/usr/bin/env python3
import subprocess
import re
import time
import threading
from datetime import datetime
import os
import json

class RealTimeNetworkMonitor:
    def __init__(self):
        self.discovered_hosts = {}
        self.network_range = self.detect_network()
        self.running = False
        
    def detect_network(self):
        try:
            # Try to get network info from ip command
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if 'default' in line:
                    parts = line.split()
                    if len(parts) >= 7:
                        return parts[2] + "/24"  # Assume /24 subnet
        except:
            pass
        
        return "192.168.1.0/24"  # Default fallback
    
    def display_banner(self):
        os.system('clear')
        print("╔══════════════════════════════════════╗")
        print("║       REAL-TIME NETWORK MONITOR     ║")
        print("║            Termux Edition           ║")
        print("╚══════════════════════════════════════╝")
        print()
        print(f"🌐 Monitoring network: {self.network_range}")
        print("🔄 Scanning every 10 seconds")
        print("💡 Press Ctrl+C to stop")
        print()
        print("{:<16} {:<25} {:<12} {:<10}".format(
            "IP Address", "Hostname", "Status", "Ports"
        ))
        print("-" * 70)
    
    def update_display(self):
        os.system('clear')
        print("╔══════════════════════════════════════╗")
        print("║       REAL-TIME NETWORK MONITOR     ║")
        print("║            Termux Edition           ║")
        print("╚══════════════════════════════════════╝")
        print()
        print(f"🌐 Network: {self.network_range} - Found {len(self.discovered_hosts)} hosts")
        print("🔄 Scanning every 10 seconds")
        print("💡 Press Ctrl+C to stop")
        print()
        print("{:<16} {:<25} {:<12} {:<10}".format(
            "IP Address", "Hostname", "Status", "Ports"
        ))
        print("-" * 70)
        
        # Sort by IP address
        sorted_hosts = sorted(self.discovered_hosts.items())
        
        for ip, info in sorted_hosts:
            hostname = info.get('hostname', '')[:24]
            status = "🆕 NEW!" if info.get('new', False) else "✅ Online"
            ports = ", ".join(info.get('open_ports', [])[:3])  # Show first 3 ports
            if len(info.get('open_ports', [])) > 3:
                ports += f" (+{len(info.get('open_ports', [])) - 3})"
            
            print("{:<16} {:<25} {:<12} {:<10}".format(
                ip, hostname, status, ports
            ))
        
        print("\n💬 Recent Activity:")
        self.print_recent_logs()
    
    def print_recent_logs(self):
        try:
            with open("network_monitor.log", "r") as f:
                lines = f.readlines()[-5:]
                for line in lines:
                    print(line.strip())
        except:
            pass
    
    def log_event(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        with open("network_monitor.log", "a") as f:
            f.write(log_entry + "\n")
        
        print(f"\r{log_entry}")
    
    def ping_sweep(self):
        base_ip = self.network_range.split('/')[0]
        network_base = '.'.join(base_ip.split('.')[:3])
        
        active_hosts = {}
        
        def ping_host(ip):
            try:
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '1', ip],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return ip
            except:
                pass
            return None
        
        threads = []
        results = []
        
        # Ping all hosts in the network
        for i in range(1, 255):
            ip = f"{network_base}.{i}"
            thread = threading.Thread(
                target=lambda ip=ip: results.append(ping_host(ip))
            )
            threads.append(thread)
            thread.start()
            
            # Limit concurrent threads
            if len(threads) >= 50:
                for t in threads:
                    t.join()
                threads = []
        
        for t in threads:
            t.join()
        
        # Process results
        for ip in results:
            if ip:
                active_hosts[ip] = {'first_seen': time.time()}
        
        return active_hosts
    
    def port_scan_host(self, ip):
        try:
            # Quick port scan for common ports
            common_ports = [21, 22, 23, 53, 80, 443, 8080, 8443]
            open_ports = []
            
            for port in common_ports:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(1)
                        result = s.connect_ex((ip, port))
                        if result == 0:
                            open_ports.append(str(port))
                except:
                    pass
            
            return open_ports
        except Exception as e:
            return []
    
    def get_hostname(self, ip):
        try:
            result = subprocess.run(
                ['nslookup', ip],
                capture_output=True,
                text=True,
                timeout=2
            )
            lines = result.stdout.split('\n')
            for line in lines:
                if 'name =' in line:
                    return line.split('=')[1].strip()
        except:
            pass
        return ""
    
    def scan_network(self):
        current_hosts = self.ping_sweep()
        new_hosts_found = False
        
        for ip in current_hosts:
            if ip not in self.discovered_hosts:
                # New host discovered
                hostname = self.get_hostname(ip)
                open_ports = self.port_scan_host(ip)
                
                self.discovered_hosts[ip] = {
                    'hostname': hostname,
                    'open_ports': open_ports,
                    'first_seen': datetime.now().strftime("%H:%M:%S"),
                    'last_seen': time.time(),
                    'new': True
                }
                
                port_info = f"ports {', '.join(open_ports)}" if open_ports else "no open ports"
                self.log_event(f"🆕 NEW HOST: {ip} ({hostname}) - {port_info}")
                new_hosts_found = True
            else:
                # Update existing host
                self.discovered_hosts[ip]['last_seen'] = time.time()
                if self.discovered_hosts[ip]['new']:
                    self.discovered_hosts[ip]['new'] = False
        
        # Check for disappeared hosts
        current_time = time.time()
        disappeared_hosts = []
        for ip, info in self.discovered_hosts.items():
            if current_time - info['last_seen'] > 60:  # 1 minute timeout
                disappeared_hosts.append(ip)
        
        for ip in disappeared_hosts:
            hostname = self.discovered_hosts[ip].get('hostname', '')
            self.log_event(f"📵 HOST OFFLINE: {ip} ({hostname})")
            # Don't remove, just mark as old
        
        return new_hosts_found
    
    def start_monitoring(self):
        self.running = True
        scan_count = 0
        
        self.display_banner()
        
        try:
            while self.running:
                scan_count += 1
                new_hosts = self.scan_network()
                
                if new_hosts or scan_count % 2 == 0:
                    self.update_display()
                
                time.sleep(10)
                
        except KeyboardInterrupt:
            self.running = False
            self.log_event("🛑 Network monitoring stopped by user")
            print("\n\n💾 Results saved to network_monitor.log")
            print(f"📊 Total hosts discovered: {len(self.discovered_hosts)}")

# Import socket for port scanning
import socket

if __name__ == "__main__":
    monitor = RealTimeNetworkMonitor()
    monitor.start_monitoring()
