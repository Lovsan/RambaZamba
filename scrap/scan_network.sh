#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display banner
display_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════╗"
    echo "║         Network Security Scanner     ║"
    echo "║            Termux Edition           ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to get network info without root
get_network_info() {
    echo -e "${YELLOW}[*] Gathering network information...${NC}"
    
    # Method 1: Using ifconfig (if available)
    if command -v ifconfig &> /dev/null; then
        IP=$(ifconfig 2>/dev/null | grep -oP 'inet \K[\d.]+' | grep -v '127.0.0.1' | head -1)
    fi
    
    # Method 2: Using ip command (alternative)
    if [ -z "$IP" ]; then
        IP=$(ip route get 1 2>/dev/null | grep -oP 'src \K\S+' | head -1)
    fi
    
    # Method 3: Using netstat
    if [ -z "$IP" ]; then
        IP=$(netstat -rn 2>/dev/null | grep -oP '[\d.]+(?=.*wlan)' | head -1)
    fi
    
    # Method 4: Check WiFi connection
    if [ -z "$IP" ]; then
        dns_ip=$(getprop net.dns1 2>/dev/null)
        if [ ! -z "$dns_ip" ]; then
            IP=$dns_ip
        fi
    fi
    
    if [ ! -z "$IP" ]; then
        echo -e "${GREEN}[+] Your IP: $IP${NC}"
        # Estimate network range
        NETWORK=$(echo $IP | cut -d. -f1-3).0/24
        echo -e "${GREEN}[+] Estimated Network: $NETWORK${NC}"
    else
        echo -e "${RED}[!] Could not detect IP automatically${NC}"
        read -p "Enter your network range (e.g., 192.168.1.0/24): " NETWORK
    fi
}

# Function for basic network discovery without root
basic_network_scan() {
    echo -e "\n${YELLOW}[*] Starting basic network discovery...${NC}"
    
    # Method 1: Ping sweep without root
    echo -e "${BLUE}[*] Performing ping sweep (no root)...${NC}"
    nmap -sn $NETWORK --unprivileged -oN ping_sweep.txt
    
    # Method 2: TCP SYN scan (works without root on some devices)
    echo -e "${BLUE}[*] Performing TCP discovery...${NC}"
    nmap -PS $NETWORK --unprivileged -oN tcp_scan.txt
    
    # Combine results
    cat ping_sweep.txt tcp_scan.txt 2>/dev/null | grep -oP 'Nmap scan report for \K[\d.]+' | sort -u > live_hosts.txt
    
    if [ -f live_hosts.txt ]; then
        LIVE_COUNT=$(wc -l < live_hosts.txt 2>/dev/null || echo "0")
        echo -e "${GREEN}[+] Found $LIVE_COUNT live hosts${NC}"
    else
        echo -e "${RED}[!] No live hosts file created${NC}"
        # Create empty file to prevent errors
        touch live_hosts.txt
    fi
}

# Function for port scanning without root
port_scanning() {
    echo -e "\n${YELLOW}[*] Starting port scanning...${NC}"
    
    if [ ! -f live_hosts.txt ] || [ ! -s live_hosts.txt ]; then
        echo -e "${RED}[!] No live hosts found. Trying direct scan...${NC}"
        # Scan the network directly
        nmap -sS -T4 --top-ports 50 $NETWORK --unprivileged -oG direct_scan.txt
        grep -oP '\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b' direct_scan.txt | sort -u > live_hosts.txt
    fi
    
    if [ ! -s live_hosts.txt ]; then
        echo -e "${RED}[!] Still no live hosts detected${NC}"
        echo -e "${YELLOW}[*] Trying alternative methods...${NC}"
        
        # Try connecting to common router IPs
        common_ips=("192.168.1.1" "192.168.0.1" "10.0.0.1" "192.168.1.254" "192.168.0.254")
        for ip in "${common_ips[@]}"; do
            ping -c 1 -W 1 $ip &>/dev/null && echo $ip >> live_hosts.txt && echo -e "${GREEN}[+] Found: $ip${NC}"
        done
    fi
    
    echo -e "${BLUE}[*] Scanning common ports on live hosts...${NC}"
    
    for host in $(cat live_hosts.txt 2>/dev/null); do
        echo -e "${YELLOW}[*] Scanning $host...${NC}"
        
        # Quick TCP scan without root
        nmap -sS -T4 --top-ports 100 $host --unprivileged -oN "scan_$host.txt"
        
        # Service detection (limited without root)
        nmap -sV --version-intensity 1 $host --unprivileged -oN "services_$host.txt"
        
        # Scan common web ports
        nmap -p 80,443,8080,8443 $host --unprivileged -oN "web_$host.txt"
    done
}

# Function for service enumeration without root
service_scanning() {
    echo -e "\n${YELLOW}[*] Starting service enumeration...${NC}"
    
    for host in $(cat live_hosts.txt 2>/dev/null); do
        echo -e "${YELLOW}[*] Enumerating services on $host...${NC}"
        
        # HTTP/HTTPS services
        nmap --script http-enum,http-title -p 80,443,8080,8443 $host --unprivileged -oN "http_$host.txt"
        
        # SSH services
        nmap -p 22 $host --script ssh2-enum-algos --unprivileged -oN "ssh_$host.txt"
    done
}

# Function to use alternative scanning methods
alternative_scanning() {
    echo -e "\n${YELLOW}[*] Using alternative scanning methods...${NC}"
    
    # Using netcat for port scanning
    echo -e "${BLUE}[*] Netcat port sweep...${NC}"
    for i in {1..254}; do
        ip="${NETWORK%.*}.$i"
        timeout 0.5 nc -zv $ip 80 2>&1 | grep succeeded && echo "$ip" >> nc_live_hosts.txt
    done &
    
    # Using ping only method
    echo -e "${BLUE}[*] Intensive ping sweep...${NC}"
    fping -asg $NETWORK 2>/dev/null | tee fping_live_hosts.txt
    
    # Merge all results
    cat live_hosts.txt nc_live_hosts.txt fping_live_hosts.txt 2>/dev/null | sort -u > all_live_hosts.txt
    mv all_live_hosts.txt live_hosts.txt 2>/dev/null
}

main() {
    display_banner
    get_network_info
    
    echo -e "${GREEN}"
    echo "Select scan type:"
    echo "1) Basic Network Discovery"
    echo "2) Full Port Scan"
    echo "3) Comprehensive Scan (All)"
    echo "4) Custom Target"
    echo "5) Alternative Methods"
    echo -e "${NC}"
    
    read -p "Enter choice (1-5): " choice
    
    case $choice in
        1)
            basic_network_scan
            ;;
        2)
            basic_network_scan
            port_scanning
            ;;
        3)
            basic_network_scan
            port_scanning
            service_scanning
            ;;
        4)
            read -p "Enter target IP or range: " custom_target
            NETWORK=$custom_target
            basic_network_scan
            port_scanning
            service_scanning
            ;;
        5)
            alternative_scanning
            ;;
        *)
            echo -e "${RED}[!] Invalid choice${NC}"
            exit 1
            ;;
    esac
    
    echo -e "\n${GREEN}[+] Scan complete!${NC}"
    echo -e "${GREEN}[+] Results saved in various .txt files${NC}"
    
    # Show summary
    if [ -f live_hosts.txt ] && [ -s live_hosts.txt ]; then
        echo -e "\n${YELLOW}[*] Scan Summary:${NC}"
        cat live_hosts.txt | while read host; do
            if [ -f "scan_$host.txt" ]; then
                ports=$(grep -oP '\d+/open' "scan_$host.txt" | wc -l)
                echo -e "${GREEN}[+] $host - $ports open ports${NC}"
            fi
        done
    fi
}

# Check if nmap is installed
if ! command -v nmap &> /dev/null; then
    echo -e "${RED}[!] Nmap is not installed. Installing...${NC}"
    pkg install nmap -y
fi

# Run main function
main
