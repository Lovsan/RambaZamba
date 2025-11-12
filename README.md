# RAMBAZAMBA - the the ultimate networking tools.
# Termux Security & Management Toolkit

A comprehensive security and remote management toolkit designed for Termux on Android devices. This toolkit provides network scanning, vulnerability assessment, honeypot capabilities, Bluetooth monitoring, and remote system management.

## 🚀 Features

### Security Tools
- **Network Scanning**: Real-time network discovery and port scanning
- **Vulnerability Assessment**: Automated vulnerability scanning
- **Honeypot Systems**: Multi-service honeypots with real-time monitoring
- **Bluetooth Reconnaissance**: Bluetooth device discovery and monitoring
- **Traffic Analysis**: Network traffic monitoring and analysis

### Remote Management
- **Multi-System Management**: Manage multiple remote systems
- **Command Execution**: Run commands across multiple systems
- **Status Monitoring**: Real-time system status tracking
- **Screenshot Capture**: Remote screenshot functionality (where supported)
- **Database Backend**: SQLite database for storing system information
- **Quick Commands**: Predefined command templates for common tasks

## 📦 Installation

### Prerequisites
- Termux app installed from F-Droid or Play Store
- Basic Termux setup completed

### Quick Setup
```bash
# Clone the repository
git clone https://github.com/lovsan/RambaZamba.git
cd RambaZamba

# Run the installation script
chmod +x install_all.sh
./install_all.sh
```

### Manual installation
```bash
# Update packages
pkg update && pkg upgrade

# Install dependencies
pkg install python nmap git bluez bluez-utils sqlite

# Install Python packages
pip install paramiko pillow pyautogui
```

