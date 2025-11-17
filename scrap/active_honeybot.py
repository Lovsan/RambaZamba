#!/usr/bin/env python3
import socket
import threading
import time
from datetime import datetime
import os
import json

class ActiveHoneypotMonitor:
    def __init__(self):
        self.connections = {}
        self.stats = {
            'total_connections': 0,
            'unique_ips': set(),
            'services': {},
            'start_time': datetime.now()
        }
        self.running = False
        
    def display_banner(self):
        os.system('clear')
        print("╔══════════════════════════════════════╗")
        print("║         ACTIVE HONEYPOT MONITOR     ║")
        print("║            Termux Edition           ║")
        print("╚══════════════════════════════════════╝")
        print()
        print("🎣 Honeypot services running on:")
        print("   • SSH: 8022 | HTTP: 8080 | FTP: 8021 | Telnet: 8023")
        print()
        print("📊 Statistics:")
        self.update_stats_display()
        print()
        print("🔍 Recent Connections:")
        print("-" * 70)
    
    def update_display(self):
        os.system('clear')
        print("╔══════════════════════════════════════╗")
        print("║         ACTIVE HONEYPOT MONITOR     ║")
        print("║            Termux Edition           ║")
        print("╚══════════════════════════════════════╝")
        print()
        print("🎣 Honeypot services running on:")
        print("   • SSH: 8022 | HTTP: 8080 | FTP: 8021 | Telnet: 8023")
        print()
        print("📊 Statistics:")
        self.update_stats_display()
        print()
        print("🔍 Recent Connections:")
        print("-" * 70)
        
        # Show recent connections
        recent_connections = sorted(
            self.connections.items(),
            key=lambda x: x[1]['timestamp'],
            reverse=True
        )[:10]
        
        for conn_id, info in recent_connections:
            ip = info['ip']
            service = info['service']
            timestamp = info['timestamp'].strftime("%H:%M:%S")
            status = "ACTIVE" if info.get('active', False) else "CLOSED"
            
            print(f"[{timestamp}] {service:>6} {ip:>15} - {status}")
        
        print("\n💬 Activity Log:")
        self.print_recent_logs()
    
    def update_stats_display(self):
        runtime = datetime.now() - self.stats['start_time']
        hours, remainder = divmod(runtime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        print(f"   • Runtime: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
        print(f"   • Total Connections: {self.stats['total_connections']}")
        print(f"   • Unique IPs: {len(self.stats['unique_ips'])}")
        print(f"   • Services:")
        for service, count in self.stats['services'].items():
            print(f"     - {service}: {count}")
    
    def print_recent_logs(self):
        try:
            with open("honeypot_monitor.log", "r") as f:
                lines = f.readlines()[-5:]
                for line in lines:
                    print(line.strip())
        except:
            pass
    
    def log_event(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        with open("honeypot_monitor.log", "a") as f:
            f.write(log_entry + "\n")
        
        print(f"\r{log_entry}")
    
    def handle_connection(self, service_name, port, client_socket, client_ip):
        conn_id = f"{client_ip}:{port}"
        
        self.connections[conn_id] = {
            'ip': client_ip,
            'service': service_name,
            'timestamp': datetime.now(),
            'active': True
        }
        
        self.stats['total_connections'] += 1
        self.stats['unique_ips'].add(client_ip)
        self.stats['services'][service_name] = self.stats['services'].get(service_name, 0) + 1
        
        self.log_event(f"🎯 {service_name} connection from {client_ip}")
        
        try:
            if service_name == "SSH":
                client_socket.send(b"SSH-2.0-OpenSSH_8.2p1\r\n")
                # Simulate SSH interaction
                time.sleep(2)
                
            elif service_name == "HTTP":
                request = client_socket.recv(1024).decode('utf-8', errors='ignore')
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Welcome</h1></body></html>"
                client_socket.send(response.encode())
                
            elif service_name == "FTP":
                client_socket.send(b"220 FTP Server Ready\r\n")
                time.sleep(1)
                
            elif service_name == "Telnet":
                client_socket.send(b"Welcome\r\nlogin: ")
                time.sleep(1)
                
        except Exception as e:
            pass
        finally:
            client_socket.close()
            self.connections[conn_id]['active'] = False
            self.log_event(f"💤 {service_name} connection closed from {client_ip}")
    
    def start_service(self, service_name, port):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('0.0.0.0', port))
            server.listen(10)
            
            self.log_event(f"✅ {service_name} honeypot started on port {port}")
            
            while self.running:
                try:
                    client_socket, addr = server.accept()
                    client_ip = addr[0]
                    
                    thread = threading.Thread(
                        target=self.handle_connection,
                        args=(service_name, port, client_socket, client_ip)
                    )
                    thread.daemon = True
                    thread.start()
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            self.log_event(f"❌ Failed to start {service_name} on port {port}: {e}")
    
    def start_monitoring(self):
        self.running = True
        
        # Start honeypot services
        services = [
            ("SSH", 8022),
            ("HTTP", 8080),
            ("FTP", 8021),
            ("Telnet", 8023)
        ]
        
        # Start each service in a separate thread
        for service_name, port in services:
            thread = threading.Thread(
                target=self.start_service,
                args=(service_name, port)
            )
            thread.daemon = True
            thread.start()
            time.sleep(0.5)
        
        # Start display updater
        self.display_banner()
        
        try:
            while self.running:
                self.update_display()
                time.sleep(2)
                
        except KeyboardInterrupt:
            self.running = False
            self.log_event("🛑 Honeypot monitoring stopped")
            print("\n\n💾 Logs saved to honeypot_monitor.log")
            print("📊 Final Statistics:")
            self.update_stats_display()

if __name__ == "__main__":
    monitor = ActiveHoneypotMonitor()
    monitor.start_monitoring()
