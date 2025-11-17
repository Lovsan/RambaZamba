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

# Function to get network info
get_network_info() {
    echo -e "${YELLOW}[*] Gathering network information...${NC}"
    
    # Get IP address
    IP=$(ip addr show | grep -oP 'inet \K[\d.]+' | grep -v '127.0.0.1' | head -1)
    echo -e "${GREEN}[+] Your IP: $IP${NC}"
    
    # Get network range
    NETWORK=$(ip route | grep -oP '[\d.]+/\d+' | head -1)
    echo -e "${GREEN}[+] Network: $NETWORK${NC}"
}

# Function for basic network discovery
basic_network_scan() {
    echo -e "\n${YELLOW}[*] Starting basic network discovery...${NC}"
    
    # Ping sweep
    echo -e "${BLUE}[*] Performing ping sweep...${NC}"
    nmap -sn $NETWORK -oN ping_sweep.txt
    
    # ARP scan
    echo -e "${BLUE}[*] Performing ARP discovery...${NC}"
    nmap -PR $NETWORK -oN arp_scan.txt
    
    # Combine results
    cat ping_sweep.txt arp_scan.txt | grep -oP 'Nmap scan report for \K[\d.]+' | sort -u > live_hosts.txt
    
    LIVE_COUNT=$(wc -l < live_hosts.txt)
    echo -e "${GREEN}[+] Found $LIVE_COUNT live hosts${NC}"
}

# Function for port scanning
port_scanning() {
    echo -e "\n${YELLOW}[*] Starting port scanning...${NC}"
    
    if [ ! -f live_hosts.txt ]; then
        echo -e "${RED}[!] No live hosts found. Run basic scan first.${NC}"
        return
    fi
    
    echo -e "${BLUE}[*] Scanning common ports on live hosts...${NC}"
    
    for host in $(cat live_hosts.txt); do
        echo -e "${YELLOW}[*] Scanning $host...${NC}"
        
        # Quick TCP scan
        nmap -sS -T4 --top-ports 100 $host -oN "scan_$host.txt"
        
        # Service detection
        nmap -sV -sC $host -p- --open -oN "services_$host.txt"
        
        # OS detection (if possible)
        nmap -O $host -oN "os_$host.txt"
    done
}

# Function for detailed service scanning
service_scanning() {
    echo -e "\n${YELLOW}[*] Starting service enumeration...${NC}"
    
    for host in $(cat live_hosts.txt); do
        echo -e "${YELLOW}[*] Enumerating services on $host...${NC}"
        
        # HTTP/HTTPS services
        nmap -sV --script http-enum,http-title -p 80,443,8080,8443 $host -oN "http_$host.txt"
        
        # SMB services
        nmap -sV --script smb-enum-shares,smb-os-discovery -p 139,445 $host -oN "smb_$host.txt"
        
        # SSH services
        nmap -sV --script ssh2-enum-algos,ssh-auth-methods -p 22 $host -oN "ssh_$host.txt"
    done
}

# Main execution
main() {
    display_banner
    get_network_info
    
    echo -e "${GREEN}"
    echo "Select scan type:"
    echo "1) Basic Network Discovery"
    echo "2) Full Port Scan"
    echo "3) Comprehensive Scan (All)"
    echo "4) Custom Target"
    echo -e "${NC}"
    
    read -p "Enter choice (1-4): " choice
    
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
        *)
            echo -e "${RED}[!] Invalid choice${NC}"
            exit 1
            ;;
    esac
    
    echo -e "\n${GREEN}[+] Scan complete!${NC}"
    echo -e "${GREEN}[+] Results saved in various .txt files${NC}"
}

# Run main function
main
