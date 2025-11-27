#!/usr/bin/env python3
import socket
import threading
import time
import json
import os
from datetime import datetime

class LightweightHoneypot:
    def __init__(self):
        self.ports = {
            8022: 'SSH',
            8080: 'HTTP', 
            8021: 'FTP',
            8023: 'Telnet',
            8443: 'HTTPS'
        }
        self.log_file = 'honeypot.log'
        self.setup_logging()
        
    def setup_logging(self):
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
    def log_event(self, event_type, client_ip, client_port, data=""):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {event_type} from {client_ip}:{client_port}"
        if data:
            log_entry += f" - {data}"
        
        print(log_entry)
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
            
        # Also log to daily file
        daily_file = f"logs/honeypot_{datetime.now().strftime('%Y%m%d')}.log"
        with open(daily_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def handle_ssh(self, client_socket, client_ip, client_port):
        self.log_event("SSH_CONNECTION", client_ip, client_port)
        try:
            client_socket.send(b"SSH-2.0-OpenSSH_8.2p1\r\n")
            client_socket.settimeout(30)
            
            while True:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    self.log_event("SSH_DATA", client_ip, client_port, data.decode('utf-8', errors='ignore')[:100])
                    
                    # Simulate SSH behavior
                    if b"SSH" in data.upper():
                        client_socket.send(b"SSH-2.0-OpenSSH_8.2p1\r\n")
                    elif b"USER" in data.upper():
                        client_socket.send(b"Password: ")
                    else:
                        client_socket.send(b"Permission denied\r\nPassword: ")
                        
                except socket.timeout:
                    break
                    
        except Exception as e:
            self.log_event("SSH_ERROR", client_ip, client_port, str(e))
        finally:
            client_socket.close()
            self.log_event("SSH_DISCONNECT", client_ip, client_port)
    
    def handle_http(self, client_socket, client_ip, client_port):
        try:
            request = client_socket.recv(4096).decode('utf-8', errors='ignore')
            lines = request.split('\n')
            if lines:
                first_line = lines[0].strip()
                self.log_event("HTTP_REQUEST", client_ip, client_port, first_line)
            
            # Send realistic response
            response = """HTTP/1.1 200 OK
Server: nginx/1.18.0
Content-Type: text/html

<html>
<head><title>Welcome</title></head>
<body>
<h1>Welcome to our server</h1>
<p>This is a test page</p>
</body>
</html>"""
            client_socket.send(response.encode())
            
        except Exception as e:
            self.log_event("HTTP_ERROR", client_ip, client_port, str(e))
        finally:
            client_socket.close()
    
    def handle_ftp(self, client_socket, client_ip, client_port):
        self.log_event("FTP_CONNECTION", client_ip, client_port)
        try:
            client_socket.send(b"220 FTP Server Ready\r\n")
            client_socket.settimeout(30)
            
            while True:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    command = data.decode('utf-8', errors='ignore').strip()
                    self.log_event("FTP_COMMAND", client_ip, client_port, command)
                    
                    if command.upper().startswith("USER"):
                        client_socket.send(b"331 User name okay, need password\r\n")
                    elif command.upper().startswith("PASS"):
                        client_socket.send(b"230 User logged in\r\n")
                    elif command.upper().startswith("QUIT"):
                        client_socket.send(b"221 Goodbye\r\n")
                        break
                    else:
                        client_socket.send(b"200 Command okay\r\n")
                        
                except socket.timeout:
                    break
                    
        except Exception as e:
            self.log_event("FTP_ERROR", client_ip, client_port, str(e))
        finally:
            client_socket.close()
            self.log_event("FTP_DISCONNECT", client_ip, client_port)
    
    def handle_telnet(self, client_socket, client_ip, client_port):
        self.log_event("TELNET_CONNECTION", client_ip, client_port)
        try:
            client_socket.send(b"Welcome\r\nlogin: ")
            client_socket.settimeout(30)
            
            state = "username"
            while True:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    self.log_event("TELNET_INPUT", client_ip, client_port, data.decode('utf-8', errors='ignore').strip())
                    
                    if state == "username":
                        client_socket.send(b"Password: ")
                        state = "password"
                    else:
                        client_socket.send(b"Login incorrect\r\nlogin: ")
                        state = "username"
                        
                except socket.timeout:
                    break
                    
        except Exception as e:
            self.log_event("TELNET_ERROR", client_ip, client_port, str(e))
        finally:
            client_socket.close()
    
    def start_service(self, port, service_name):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('0.0.0.0', port))
            server.listen(5)
            
            print(f"[+] {service_name} honeypot listening on port {port}")
            
            while True:
                client_socket, addr = server.accept()
                client_ip, client_port = addr
                
                if service_name == 'SSH':
                    handler = self.handle_ssh
                elif service_name == 'HTTP':
                    handler = self.handle_http
                elif service_name == 'FTP':
                    handler = self.handle_ftp
                elif service_name == 'Telnet':
                    handler = self.handle_telnet
                else:
                    handler = self.handle_http
                
                thread = threading.Thread(target=handler, args=(client_socket, client_ip, client_port))
                thread.daemon = True
                thread.start()
                
        except Exception as e:
            print(f"Error in {service_name} service: {e}")
    
    def start_all(self):
        print("[+] Starting lightweight honeypot...")
        print("[+] Ports: " + ", ".join([f"{port} ({service})" for port, service in self.ports.items()]))
        print("[+] Logs: honeypot.log, logs/honeypot_YYYYMMDD.log")
        print("[+] Press Ctrl+C to stop")
        
        threads = []
        for port, service in self.ports.items():
            thread = threading.Thread(target=self.start_service, args=(port, service))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            time.sleep(0.1)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[!] Stopping honeypot...")

if __name__ == "__main__":
    honeypot = LightweightHoneypot()
    honeypot.start_all()
