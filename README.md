# RambaZamba - Advanced Networking Tools Collection

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/Lovsan/RambaZamba.svg)](https://github.com/Lovsan/RambaZamba/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/Lovsan/RambaZamba.svg)](https://github.com/Lovsan/RambaZamba/issues)

A comprehensive suite of networking tools designed for security testing, network analysis, and proxy management. Built with Python and Bash scripts for maximum flexibility and performance.

## 🌟 Key Features

### 🔧 Core Proxy Management
- **Multi-Protocol Support**: HTTP, HTTPS, SOCKS4, SOCKS5 proxies
- **Batch Testing**: Test hundreds of proxies simultaneously with configurable timeouts
- **Smart Filtering**: Filter by status, speed, type, country, and custom criteria
- **GeoIP Integration**: Automatic location detection with city-level accuracy
- **Export Capabilities**: Save working proxies in TXT, JSON, CSV formats

### 🌐 Advanced Network Tools
- **Proxy Discovery**: Automated proxy harvesting from multiple sources
- **Nmap Integration**: Port scanning and service detection
- **Network Analysis**: DNS lookup, WHOIS, traceroute, and ping tools
- **Speed Testing**: Download/upload speed measurement through proxies
- **SSL/TLS Analysis**: Certificate and encryption strength testing

### 🛡️ Security Assessment
- **Vulnerability Scanner**: Automated security vulnerability detection
- **Custom Headers**: Advanced HTTP header manipulation and testing
- **Security Scoring**: Proxy security rating based on multiple factors
- **Brute Force Detection**: Identify and test for common attack vectors

### ⛓️ Advanced Features
- **Proxy Chain Builder**: Create multi-hop proxy chains for enhanced anonymity
- **Reverse Proxy System**: HTTP/HTTPS reverse proxy with traffic monitoring
- **Automatic Proxy Rotation**: Configurable intervals for proxy switching
- **Traffic Monitoring**: Real-time tracking of inbound/outbound traffic
- **System Integration**: Windows system proxy management with one-click setup
- **Real-time Monitoring**: Live system resource and network monitoring
- **Interactive Globe**: 3D visualization of proxy locations worldwide
- **Theme Support**: Multiple UI themes (Dark, Terminal, Blood, Ultraviolet, Light)

### 💻 System Integration
- **Windows Proxy Management**: Direct registry integration for system proxy control
- **Emergency Repair**: Fix corrupted proxy settings with one click
- **Backup/Restore**: Save and restore system proxy configurations
- **Thread Management**: Configurable thread pools for optimal performance

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Windows 10/11 (primary platform) or Linux/macOS (limited features)
- Administrator privileges (for system proxy management)

### Installation

1. **Clone or Download the Project**
   ```bash
   git clone https://github.com/Lovsan/RambaZamba.git
   cd RambaZamba
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Or use the provided installation script:
   ```bash
   ./install_tools.sh
   ```

3. **Run the Setup**
   ```bash
   ./quick_setup.sh
   ```

## 📖 Usage

### Proxy Tools
Run the main proxy tool:
```bash
python proxy_tool_v1.0.py
```

### Honeybot Deployment
Deploy a lightweight honeybot:
```bash
python lightweight_honeybot.py
```

### Network Scanning
Perform a network scan:
```bash
./network_scan.sh
```

### Real-time Monitoring
Monitor network in real-time:
```bash
python realtime_network.py
```

### Reverse Proxy
Run the reverse proxy with traffic monitoring:
```bash
python reverse_proxy.py --target-host example.com --target-port 80
```

Or run in daemon mode with a proxy file:
```bash
python reverse_proxy.py --target-host api.example.com --target-port 443 --ssl --proxy-file proxies.txt --daemon
```

Interactive commands in the reverse proxy:
- `start` - Start the reverse proxy server
- `stop` - Stop the reverse proxy server  
- `status` - Show current status and traffic statistics
- `add <host:port>` - Add a proxy to the pool
- `remove <host:port>` - Remove a proxy from the pool
- `list` - List all proxies in the pool
- `rotate` - Manually rotate to the next proxy
- `validate` - Validate all proxies
- `load <file>` - Load proxies from a file
- `save <file>` - Save proxies to a file

## 📸 Screenshots

### Main Dashboard
![Main Dashboard Screenshot](screenshots/main_dashboard.png)
*The main interface showing proxy management and network tools.*

### Proxy Testing Interface
![Proxy Testing Screenshot](screenshots/proxy_testing.png)
*Real-time proxy testing with filtering and export options.*

### Network Scanning Results
![Network Scan Screenshot](screenshots/network_scan.png)
*Detailed network scan results with vulnerability assessment.*

### Honeybot Configuration
![Honeybot Config Screenshot](screenshots/honeybot_config.png)
*Honeybot setup and monitoring interface.*

### Real-time Bluetooth Monitoring
![Bluetooth Monitoring Screenshot](screenshots/bluetooth_monitor.png)
*Live Bluetooth device scanning and analysis.*

### System Resource Dashboard
![System Dashboard Screenshot](screenshots/system_dashboard.png)
*Comprehensive system and network resource monitoring.*

## 🛠️ Tools Included

| Tool | Description | Language |
|------|-------------|----------|
| `proxy_tool_v1.0.py` | Advanced proxy management and testing | Python |
| `reverse_proxy.py` | Reverse proxy with traffic monitoring and auto-rotation | Python |
| `honeybot_setup.sh` | Honeybot deployment script | Bash |
| `network_scan.sh` | Network scanning utilities | Bash |
| `vulnerability_scan.sh` | Security vulnerability scanner | Bash |
| `bluetooth_tools.sh` | Bluetooth device management | Bash |
| `realtime_network.py` | Real-time network monitoring | Python |
| `system_manager.py` | System integration manager | Python |
| `master_dashboard.py` | Main dashboard interface | Python |

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Format code
black .
```

### Benchmarking and Testing

The project includes comprehensive benchmarking tools:

```bash
# HTML5 parser fuzzing
cd benchmarks
python3 fuzz.py --sample 5  # Generate sample fuzzed HTML
python3 fuzz.py --help      # See all options
```

See [benchmarks/README.md](benchmarks/README.md) for detailed documentation.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This toolkit is intended for educational and testing purposes only. Users are responsible for complying with applicable laws and regulations when using these tools. The authors assume no liability for misuse.

## 🙏 Acknowledgments

- Thanks to the open-source community for inspiration and contributions
- Special thanks to contributors and testers

---

**Note**: Screenshots are placeholders. Replace with actual screenshots of your application in action.