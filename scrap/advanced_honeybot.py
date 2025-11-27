#!/usr/bin/env python3
import socket
import threading
import time
import logging
from datetime import datetime
import json
import hashlib
import os

class AdvancedHoneypot:
    def __init__(self):
        self.config = {
            'log_file': 'honeypot.log',
            'json_log': 'honeypot.json',
            'session_log': 'sessions/',
            'ports': {
                8022: 'SSH',
                8080: 'HTTP',
                8021: 'FTP',
                8023: 'Telnet',
                8443: 'HTTPS',
                9080: 'HTTP-Alt'
            }
        }
        
        # Create sessions directory
        os.makedirs(self.config['session_log'], exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config['log_file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger()
        
    def get_client_fingerprint(self, client_ip, client_port):
        """Create a fingerprint for the client"""
        unique_string = f"{client_ip}:{client_port}:{datetime.now().timestamp()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:8]
    
    def log_event(self, event_type, client_ip, client_port, data=None, session_id=None):
        """Log events in both text and JSON format"""
        timestamp = datetime.now().isoformat()
        
        # Text log
        log_entry = f"[{timestamp}] {event_type} from {client_ip}:{client_port}"
        if data:
            log_entry += f" - {data}"
        self.logger.info(log_entry)
        
        # JSON log
        json_entry = {
            'timestamp': timestamp,
            'event_type': event_type,
            'client_ip': client_ip,
            'client_port': client_port,
            'session_id': session_id,
            'data': data
        }
        
        with open(self.config['json_log'], 'a') as f:
            f.write(json.dumps(json_entry) + '\n')
            
        # Session logging
        if session_id:
            session_file = os.path.join(self.config['session_log'], f"{session_id}.log")
            with open(session_file, 'a') as f:
                f.write(f"[{timestamp}] {data}\n")
    
    def handle_ssh(self, client_socket, client_ip, client_port):
        """SSH honeypot handler"""
        session_id = self.get_client_fingerprint(client_ip, client_port)
        self.log_event("SSH_CONNECTION", client_ip, client_port, "New SSH connection", session_id)
        
        try:
            # Send SSH banner
            client_socket.send(b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.3\r\n")
            
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                # Log the received data
                try:
                    decoded_data = data.decode('utf-8', errors='ignore')
                    self.log_event("SSH_INPUT", client_ip, client_port, decoded_data.strip(), session_id)
                    
                    # Simulate SSH negotiation
                    if "SSH" in decoded_data.upper():
                        client_socket.send(b"SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.3\r\n")
                    elif "USER" in decoded_data.upper():
                        client_socket.send(b"Password: ")
                    elif len(data) > 0:  # Assume password attempt
                        self.log_event("SSH_PASSWORD_ATTEMPT", client_ip, client_port, "Password attempted", session_id)
                        client_socket.send(b"Permission denied, please try again.\r\nPassword: ")
                        
                except Exception as e:
                    self.log_event("SSH_ERROR", client_ip, client_port, str(e), session_id)
                    
        except Exception as e:
            self.log_event("SSH_ERROR", client_ip, client_port, str(e), session_id)
        finally:
            client_socket.close()
            self.log_event("SSH_DISCONNECT", client_ip, client_port, "Connection closed", session_id)
    
    def handle_http(self, client_socket, client_ip, client_port):
        """HTTP honeypot handler"""
        session_id = self.get_client_fingerprint(client_ip, client_port)
        
        try:
            request = client_socket.recv(4096).decode('utf-8', errors='ignore')
            self.log_event("HTTP_REQUEST", client_ip, client_port, request.split('\n')[0] if request else "Empty", session_id)
            
            # Parse request details
            headers = {}
            if request:
                lines = request.split('\n')
                for line in lines[1:]:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        headers[key.strip()] = value.strip()
            
            # Log user agent and other headers
            user_agent = headers.get('User-Agent', 'Unknown')
            self.log_event("HTTP_USER_AGENT", client_ip, client_port, user_agent, session_id)
            
            # Create realistic response
            response = """HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Server: nginx/1.18.0
Connection: close

<!DOCTYPE html>
<html>
<head>
    <title>Welcome to nginx!</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to nginx!</h1>
        <p>If you see this page, the nginx web server is successfully installed and working.</p>
        <p>Thank you for using nginx.</p>
        <hr>
        <p><em>This is a honeypot system. Your activity is being logged.</em></p>
    </div>
</body>
</html>"""
            
            client_socket.send(response.encode())
            
        except Exception as e:
            self.log_event("HTTP_ERROR", client_ip, client_port, str(e), session_id)
        finally:
            client_socket.close()
    
    def handle_ftp(self, client_socket, client_ip, client_port):
        """FTP honeypot handler"""
        session_id = self.get_client_fingerprint(client_ip, client_port)
        self.log_event("FTP_CONNECTION", client_ip, client_port, "New FTP connection", session_id)
        
        try:
            client_socket.send(b"220 Welcome to FTP server\r\n")
            
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                command = data.decode('utf-8', errors='ignore').strip()
                self.log_event("FTP_COMMAND", client_ip, client_port, command, session_id)
                
                if command.upper().startswith("USER"):
                    client_socket.send(b"331 User name okay, need password\r\n")
                elif command.upper().startswith("PASS"):
                    client_socket.send(b"230 User logged in successfully\r\n")
                elif command.upper().startswith("SYST"):
                    client_socket.send(b"215 UNIX Type: L8\r\n")
                elif command.upper().startswith("PWD"):
                    client_socket.send(b'257 "/" is current directory\r\n')
                elif command.upper().startswith("QUIT"):
                    client_socket.send(b"221 Goodbye\r\n")
                    break
                else:
                    client_socket.send(b"200 Command okay\r\n")
                    
        except Exception as e:
            self.log_event("FTP_ERROR", client_ip, client_port, str(e), session_id)
        finally:
            client_socket.close()
            self.log_event("FTP_DISCONNECT", client_ip, client_port, "Connection closed", session_id)
    
    def handle_telnet(self, client_socket, client_ip, client_port):
        """Telnet honeypot handler"""
        session_id = self.get_client_fingerprint(client_ip, client_port)
        self.log_event("TELNET_CONNECTION", client_ip, client_port, "New Telnet connection", session_id)
        
        try:
            client_socket.send(b"Welcome to Ubuntu 18.04 LTS\r\n\r\nlogin: ")
            
            username_received = False
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                command = data.decode('utf-8', errors='ignore').strip()
                self.log_event("TELNET_INPUT", client_ip, client_port, command, session_id)
                
                if not username_received:
                    client_socket.send(b"Password: ")
                    username_received = True
                else:
                    client_socket.send(b"\r\nLogin incorrect\r\n\r\nlogin: ")
                    username_received = False
                    
        except Exception as e:
            self.log_event("TELNET_ERROR", client_ip, client_port, str(e), session_id)
        finally:
            client_socket.close()
    
    def start_service(self, port, service_name):
        """Start a honeypot service on specified port"""
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('0.0.0.0', port))
            server.listen(10)
            
            self.logger.info(f"[+] {service_name} honeypot listening on port {port}")
            
            while True:
                client_socket, client_addr = server.accept()
                client_ip, client_port = client_addr
                
                # Choose handler based on service
                if service_name == 'SSH':
                    handler = self.handle_ssh
                elif service_name == 'HTTP':
                    handler = self.handle_http
                elif service_name == 'FTP':
                    handler = self.handle_ftp
                elif service_name == 'Telnet':
                    handler = self.handle_telnet
                else:
                    handler = self.handle_http  # Default
                
                # Start thread for each connection
                thread = threading.Thread(
                    target=handler,
                    args=(client_socket, client_ip, client_port)
                )
                thread.daemon = True
                thread.start()
                
        except Exception as e:
            self.logger.error(f"Error starting {service_name} on port {port}: {e}")
    
    def start_all_services(self):
        """Start all honeypot services"""
        self.logger.info("[+] Starting all honeypot services...")
        
        threads = []
        for port, service in self.config['ports'].items():
            thread = threading.Thread(
                target=self.start_service,
                args=(port, service)
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)
            time.sleep(0.2)
        
        self.logger.info("[+] All honeypot services started!")
        self.logger.info("[*] Services running on ports: " + ", ".join([str(p) for p in self.config['ports'].keys()]))
        self.logger.info("[*] Logs: honeypot.log, honeypot.json, sessions/")
        self.logger.info("[*] Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("[!] Stopping honeypot...")

if __name__ == "__main__":
    honeypot = AdvancedHoneypot()
    honeypot.start_all_services()
