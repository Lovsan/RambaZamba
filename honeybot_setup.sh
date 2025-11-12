#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

display_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════╗"
    echo "║           Honeypot System           ║"
    echo "║            Termux Edition           ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
}

setup_ssh_honeypot() {
    echo -e "\n${YELLOW}[*] Setting up SSH honeypot...${NC}"
    
    if [ -d "kippo" ]; then
        cd kippo
        # Create configuration
        cp kippo.cfg.dist kippo.cfg
        
        # Modify configuration for Termux
        sed -i 's/ssh_port = 2222/ssh_port = 2222/' kippo.cfg
        sed -i 's/hostname = svr04/hostname = termux-honeypot/' kippo.cfg
        
        echo -e "${GREEN}[+] SSH honeypot configured on port 2222${NC}"
        echo -e "${YELLOW}[*] Start with: cd kippo && twistd -y kippo.tac${NC}"
        cd ..
    else
        echo -e "${RED}[!] Kippo not found. Run install_tools.sh first.${NC}"
    fi
}

setup_simple_python_honeypot() {
    echo -e "\n${YELLOW}[*] Creating simple multi-service honeypot...${NC}"
    
    cat > simple_honeypot.py << 'EOF'
#!/usr/bin/env python3
import socket
import threading
import time
from datetime import datetime

class SimpleHoneypot:
    def __init__(self):
        self.log_file = "honeypot.log"
        self.services = {
            21: "FTP",
            22: "SSH", 
            23: "Telnet",
            80: "HTTP",
            443: "HTTPS",
            2222: "SSH-Alt",
            8080: "HTTP-Alt"
        }
        
    def log_connection(self, service, client_ip, client_port):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {service} connection from {client_ip}:{client_port}\n"
        
        with open(self.log_file, "a") as f:
            f.write(log_entry)
        print(f"[!] {service} connection from {client_ip}:{client_port}")
        
    def handle_ftp(self, client_socket, client_ip, client_port):
        self.log_connection("FTP", client_ip, client_port)
        try:
            client_socket.send(b"220 Welcome to FTP server\r\n")
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                command = data.decode().strip()
                print(f"[FTP] {client_ip}: {command}")
                
                if command.upper().startswith("USER"):
                    client_socket.send(b"331 User name okay, need password\r\n")
                elif command.upper().startswith("PASS"):
                    client_socket.send(b"230 User logged in\r\n")
                elif command.upper().startswith("QUIT"):
                    client_socket.send(b"221 Goodbye\r\n")
                    break
                else:
                    client_socket.send(b"200 Command okay\r\n")
                    
        except Exception as e:
            print(f"FTP Error: {e}")
        finally:
            client_socket.close()
            
    def handle_http(self, client_socket, client_ip, client_port):
        self.log_connection("HTTP", client_ip, client_port)
        try:
            request = client_socket.recv(1024).decode()
            print(f"[HTTP] {client_ip}: {request.splitlines()[0] if request.splitlines() else 'Empty'}")
            
            response = """HTTP/1.1 200 OK
Content-Type: text/html

<html>
<head><title>Welcome</title></head>
<body>
<h1>Welcome to our server</h1>
<p>This is a honeypot system</p>
</body>
</html>"""
            client_socket.send(response.encode())
        except Exception as e:
            print(f"HTTP Error: {e}")
        finally:
            client_socket.close()
            
    def handle_ssh(self, client_socket, client_ip, client_port):
        self.log_connection("SSH", client_ip, client_port)
        try:
            # Send SSH banner
            client_socket.send(b"SSH-2.0-OpenSSH_7.4\r\n")
            time.sleep(1)
            # Log connection details
            print(f"[SSH] Connection from {client_ip}")
        except Exception as e:
            print(f"SSH Error: {e}")
        finally:
            client_socket.close()
            
    def handle_generic(self, client_socket, service_name, client_ip, client_port):
        self.log_connection(service_name, client_ip, client_port)
        try:
            client_socket.send(b"Connection established\r\n")
            time.sleep(2)
        except:
            pass
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
                client_socket, client_addr = server.accept()
                client_ip, client_port = client_addr
                
                if service_name == "FTP":
                    thread = threading.Thread(target=self.handle_ftp, args=(client_socket, client_ip, client_port))
                elif service_name == "HTTP":
                    thread = threading.Thread(target=self.handle_http, args=(client_socket, client_ip, client_port))
                elif service_name == "SSH":
                    thread = threading.Thread(target=self.handle_ssh, args=(client_socket, client_ip, client_port))
                else:
                    thread = threading.Thread(target=self.handle_generic, args=(client_socket, service_name, client_ip, client_port))
                    
                thread.daemon = True
                thread.start()
                
        except Exception as e:
            print(f"Error starting {service_name} on port {port}: {e}")
            
    def start_all_services(self):
        print("[+] Starting all honeypot services...")
        threads = []
        
        for port, service in self.services.items():
            thread = threading.Thread(target=self.start_service, args=(port, service))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            time.sleep(0.1)
            
        print("[+] All honeypot services started!")
        print("[*] Logging to: honeypot.log")
        print("[*] Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[!] Stopping honeypot...")

if __name__ == "__main__":
    honeypot = SimpleHoneypot()
    honeypot.start_all_services()
EOF

    chmod +x simple_honeypot.py
    echo -e "${GREEN}[+] Simple honeypot created: simple_honeypot.py${NC}"
}

setup_network_monitor() {
    echo -e "\n${YELLOW}[*] Setting up network traffic monitor...${NC}"
    
    cat > network_monitor.py << 'EOF'
#!/usr/bin/env python3
import socket
import struct
import time
from datetime import datetime

def network_monitor():
    log_file = "network_traffic.log"
    
    try:
        # Create raw socket
        sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
        sniffer.bind(('0.0.0.0', 0))
        sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        
        print("[+] Network monitor started...")
        print("[*] Logging to: network_traffic.log")
        print("[*] Press Ctrl+C to stop")
        
        while True:
            packet, addr = sniffer.recvfrom(65565)
            
            # Parse IP header (first 20 bytes)
            ip_header = packet[0:20]
            iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
            
            version_ihl = iph[0]
            version = version_ihl >> 4
            ihl = version_ihl & 0xF
            iph_length = ihl * 4
            ttl = iph[5]
            protocol = iph[6]
            s_addr = socket.inet_ntoa(iph[8])
            d_addr = socket.inet_ntoa(iph[9])
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Protocol mapping
            protocols = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}
            proto_name = protocols.get(protocol, str(protocol))
            
            log_entry = f"[{timestamp}] {proto_name} {s_addr} -> {d_addr} TTL:{ttl}\n"
            
            with open(log_file, "a") as f:
                f.write(log_entry)
                
            print(f"[NET] {s_addr} -> {d_addr} [{proto_name}]")
            
    except PermissionError:
        print("[-] Root access required for raw socket monitoring")
    except KeyboardInterrupt:
        print("\n[!] Stopping network monitor...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    network_monitor()
EOF

    chmod +x network_monitor.py
    echo -e "${GREEN}[+] Network monitor created: network_monitor.py${NC}"
}

setup_connection_logger() {
    echo -e "\n${YELLOW}[*] Setting up connection logger...${NC}"
    
    cat > connection_logger.sh << 'EOF'
#!/bin/bash
# Connection logger script
LOG_FILE="connection_attempts.log"
INTERFACE=$(ip route | grep default | awk '{print $5}' | head -1)

echo "[+] Starting connection logger on interface: $INTERFACE"
echo "[*] Logging to: $LOG_FILE"
echo "[*] Press Ctrl+C to stop"

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Log TCP connections
    netstat -tn 2>/dev/null | grep ESTABLISHED | while read line; do
        echo "[$TIMESTAMP] TCP: $line" >> $LOG_FILE
    done
    
    # Log UDP connections
    netstat -un 2>/dev/null | while read line; do
        if [[ $line == udp* ]]; then
            echo "[$TIMESTAMP] UDP: $line" >> $LOG_FILE
        fi
    done
    
    sleep 5
done
EOF

    chmod +x connection_logger.sh
    echo -e "${GREEN}[+] Connection logger created: connection_logger.sh${NC}"
}

start_monitoring_dashboard() {
    echo -e "\n${YELLOW}[*] Starting monitoring dashboard...${NC}"
    
    cat > monitoring_dashboard.py << 'EOF'
#!/usr/bin/env python3
import os
import time
from datetime import datetime

def display_dashboard():
    while True:
        os.system('clear')
        print("╔══════════════════════════════════════╗")
        print("║        MONITORING DASHBOARD         ║")
        print("║            Termux Edition           ║")
        print("╚══════════════════════════════════════╝")
        print()
        
        # Display honeypot logs
        if os.path.exists('honeypot.log'):
            print("📡 HONEYPOT ACTIVITY:")
            os.system('tail -10 honeypot.log')
            print()
        
        # Display network traffic
        if os.path.exists('network_traffic.log'):
            print("🌐 NETWORK TRAFFIC:")
            os.system('tail -8 network_traffic.log')
            print()
            
        # Display connection attempts
        if os.path.exists('connection_attempts.log'):
            print("🔗 CONNECTION ATTEMPTS:")
            os.system('tail -5 connection_attempts.log')
            print()
            
        # System information
        print("💻 SYSTEM INFO:")
        os.system('date')
        os.system('echo "IP: $(curl -s ifconfig.me)"')
        print()
        
        print("Press Ctrl+C to exit")
        time.sleep(3)

if __name__ == "__main__":
    try:
        display_dashboard()
    except KeyboardInterrupt:
        print("\n[!] Exiting dashboard...")
EOF

    chmod +x monitoring_dashboard.py
    echo -e "${GREEN}[+] Monitoring dashboard created: monitoring_dashboard.py${NC}"
}

main() {
    display_banner
    
    echo -e "${GREEN}"
    echo "Select honeypot/monitoring setup:"
    echo "1) Setup SSH Honeypot (Kippo)"
    echo "2) Setup Simple Python Honeypot"
    echo "3) Setup Network Traffic Monitor"
    echo "4) Setup Connection Logger"
    echo "5) Start Monitoring Dashboard"
    echo "6) Setup Complete System (All)"
    echo -e "${NC}"
    
    read -p "Enter choice (1-6): " choice
    
    case $choice in
        1)
            setup_ssh_honeypot
            ;;
        2)
            setup_simple_python_honeypot
            echo -e "${YELLOW}[*] Start with: python simple_honeypot.py${NC}"
            ;;
        3)
            setup_network_monitor
            echo -e "${YELLOW}[*] Start with: python network_monitor.py${NC}"
            ;;
        4)
            setup_connection_logger
            echo -e "${YELLOW}[*] Start with: ./connection_logger.sh${NC}"
            ;;
        5)
            start_monitoring_dashboard
            echo -e "${YELLOW}[*] Start with: python monitoring_dashboard.py${NC}"
            ;;
        6)
            setup_ssh_honeypot
            setup_simple_python_honeypot
            setup_network_monitor
            setup_connection_logger
            start_monitoring_dashboard
            echo -e "${GREEN}[+] Complete honeypot system setup!${NC}"
            echo -e "${YELLOW}[*] Start individual components as needed${NC}"
            ;;
        *)
            echo -e "${RED}[!] Invalid choice${NC}"
            ;;
    esac
    
    echo -e "\n${GREEN}[+] Honeypot setup complete!${NC}"
    echo -e "${YELLOW}[!] Remember: Only use on networks you own!${NC}"
}

main
