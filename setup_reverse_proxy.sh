#!/bin/bash

#
# Reverse Proxy Setup Script
# This script helps set up and run the reverse proxy server
#

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Reverse Proxy Setup & Management${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Display menu
show_menu() {
    echo -e "${GREEN}Select an option:${NC}"
    echo "1) Start reverse proxy (default config)"
    echo "2) Start reverse proxy (custom config)"
    echo "3) Start reverse proxy with SSL/TLS"
    echo "4) Test reverse proxy configuration"
    echo "5) Create new configuration"
    echo "6) View logs"
    echo "7) Stop all reverse proxy instances"
    echo "8) Exit"
    echo ""
    read -p "Enter choice [1-8]: " choice
}

# Start reverse proxy with default config
start_default() {
    echo -e "${YELLOW}Starting reverse proxy with default configuration...${NC}"
    
    if [ ! -f "reverse_proxy_config.json" ]; then
        echo -e "${RED}Configuration file not found: reverse_proxy_config.json${NC}"
        echo "Creating default configuration..."
        python3 reverse_proxy.py -b http://localhost:8001 -b http://localhost:8002 --save-config reverse_proxy_config.json
    fi
    
    python3 reverse_proxy.py -c reverse_proxy_config.json
}

# Start reverse proxy with custom config
start_custom() {
    read -p "Enter path to configuration file: " config_file
    
    if [ ! -f "$config_file" ]; then
        echo -e "${RED}Configuration file not found: $config_file${NC}"
        return
    fi
    
    echo -e "${YELLOW}Starting reverse proxy with custom configuration...${NC}"
    python3 reverse_proxy.py -c "$config_file"
}

# Start reverse proxy with SSL
start_ssl() {
    read -p "Enter host (default: 0.0.0.0): " host
    host=${host:-0.0.0.0}
    
    read -p "Enter port (default: 8443): " port
    port=${port:-8443}
    
    read -p "Enter SSL certificate path: " cert
    read -p "Enter SSL key path: " key
    
    if [ ! -f "$cert" ] || [ ! -f "$key" ]; then
        echo -e "${RED}SSL certificate or key file not found${NC}"
        return
    fi
    
    read -p "Enter backend server URLs (comma-separated): " backends
    IFS=',' read -ra BACKEND_ARRAY <<< "$backends"
    
    backend_args=""
    for backend in "${BACKEND_ARRAY[@]}"; do
        backend_args="$backend_args -b $(echo $backend | xargs)"
    done
    
    echo -e "${YELLOW}Starting reverse proxy with SSL/TLS...${NC}"
    python3 reverse_proxy.py -H "$host" -p "$port" --ssl-cert "$cert" --ssl-key "$key" $backend_args
}

# Test configuration
test_config() {
    read -p "Enter path to configuration file (default: reverse_proxy_config.json): " config_file
    config_file=${config_file:-reverse_proxy_config.json}
    
    if [ ! -f "$config_file" ]; then
        echo -e "${RED}Configuration file not found: $config_file${NC}"
        return
    fi
    
    echo -e "${YELLOW}Testing configuration...${NC}"
    python3 -c "
import json
try:
    with open('$config_file', 'r') as f:
        config = json.load(f)
    print('✓ Configuration file is valid JSON')
    print('  Host: ' + config.get('host', 'Not set'))
    print('  Port: ' + str(config.get('port', 'Not set')))
    print('  Backend Servers: ' + ', '.join(config.get('backend_servers', [])))
    print('  Load Balance: ' + config.get('load_balance', 'Not set'))
except Exception as e:
    print('✗ Configuration error: ' + str(e))
    "
}

# Create new configuration
create_config() {
    echo -e "${YELLOW}Creating new configuration...${NC}"
    
    read -p "Enter host (default: 0.0.0.0): " host
    host=${host:-0.0.0.0}
    
    read -p "Enter port (default: 8080): " port
    port=${port:-8080}
    
    read -p "Enter backend server URLs (comma-separated): " backends
    IFS=',' read -ra BACKEND_ARRAY <<< "$backends"
    
    backend_args=""
    for backend in "${BACKEND_ARRAY[@]}"; do
        backend_args="$backend_args -b $(echo $backend | xargs)"
    done
    
    read -p "Enter load balancing method (round-robin/least-conn, default: round-robin): " lb_method
    lb_method=${lb_method:-round-robin}
    
    read -p "Enter configuration file name (default: custom_proxy_config.json): " config_name
    config_name=${config_name:-custom_proxy_config.json}
    
    echo -e "${YELLOW}Saving configuration to $config_name...${NC}"
    python3 reverse_proxy.py -H "$host" -p "$port" $backend_args -l "$lb_method" --save-config "$config_name"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Configuration saved successfully!${NC}"
    else
        echo -e "${RED}Error saving configuration${NC}"
    fi
}

# View logs
view_logs() {
    if [ -f "reverse_proxy.log" ]; then
        echo -e "${YELLOW}Displaying reverse proxy logs (Ctrl+C to exit)...${NC}"
        tail -f reverse_proxy.log
    else
        echo -e "${RED}Log file not found: reverse_proxy.log${NC}"
    fi
}

# Stop all instances
stop_all() {
    echo -e "${YELLOW}Stopping all reverse proxy instances...${NC}"
    pkill -f "reverse_proxy.py"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}All reverse proxy instances stopped${NC}"
    else
        echo -e "${YELLOW}No running instances found${NC}"
    fi
}

# Main loop
while true; do
    show_menu
    
    case $choice in
        1)
            start_default
            ;;
        2)
            start_custom
            ;;
        3)
            start_ssl
            ;;
        4)
            test_config
            ;;
        5)
            create_config
            ;;
        6)
            view_logs
            ;;
        7)
            stop_all
            ;;
        8)
            echo -e "${GREEN}Exiting...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    clear
done
