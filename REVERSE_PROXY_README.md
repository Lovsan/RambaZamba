# Reverse Proxy - Advanced HTTP/HTTPS Reverse Proxy Server

A professional, feature-rich reverse proxy server written in Python with support for load balancing, SSL/TLS termination, health checks, and comprehensive logging.

## Features

- **HTTP/HTTPS Support**: Handle both HTTP and HTTPS traffic
- **Load Balancing**: 
  - Round-robin distribution
  - Least connections algorithm
- **SSL/TLS Termination**: Decrypt SSL traffic at the proxy
- **Health Checks**: Automatic backend server health monitoring
- **Connection Management**: Configurable max connections and timeouts
- **Detailed Logging**: File and console logging with timestamps
- **Configuration Management**: JSON-based configuration files
- **Easy Setup**: Interactive shell script for quick deployment

## Quick Start

### Basic Usage

1. **Using the setup script (recommended):**
```bash
./setup_reverse_proxy.sh
```

2. **Using Python directly:**
```bash
python3 reverse_proxy.py -b http://backend1.example.com:8001 -b http://backend2.example.com:8002
```

3. **Using a configuration file:**
```bash
python3 reverse_proxy.py -c reverse_proxy_config.json
```

## Configuration

### Command Line Options

```
-c, --config FILE          Path to configuration file
-H, --host HOST           Host address to bind to (default: 0.0.0.0)
-p, --port PORT           Port to listen on (default: 8080)
-b, --backend URL         Backend server URL (can be specified multiple times)
--ssl-cert FILE           Path to SSL certificate file
--ssl-key FILE            Path to SSL key file
-m, --max-connections N   Maximum concurrent connections (default: 100)
-t, --timeout SECONDS     Connection timeout in seconds (default: 60)
-l, --load-balance METHOD Load balancing algorithm (round-robin, least-conn)
--save-config FILE        Save configuration to file and exit
```

### Configuration File Format

Create a JSON file with the following structure:

```json
{
    "host": "0.0.0.0",
    "port": 8080,
    "backend_servers": [
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:8003"
    ],
    "ssl_cert": null,
    "ssl_key": null,
    "max_connections": 100,
    "timeout": 60,
    "load_balance": "round-robin"
}
```

## Usage Examples

### Example 1: Basic Reverse Proxy

Forward traffic from port 8080 to two backend servers:

```bash
python3 reverse_proxy.py -p 8080 \
    -b http://192.168.1.10:8001 \
    -b http://192.168.1.11:8001
```

### Example 2: HTTPS Reverse Proxy with SSL Termination

```bash
python3 reverse_proxy.py -p 443 \
    --ssl-cert /path/to/cert.pem \
    --ssl-key /path/to/key.pem \
    -b http://backend1:80 \
    -b http://backend2:80
```

### Example 3: Load Balancing with Least Connections

```bash
python3 reverse_proxy.py -p 8080 \
    -b http://server1:8001 \
    -b http://server2:8001 \
    -b http://server3:8001 \
    -l least-conn
```

### Example 4: Create and Save Configuration

```bash
python3 reverse_proxy.py -p 8080 \
    -b http://backend1:8001 \
    -b http://backend2:8001 \
    -l round-robin \
    --save-config my_proxy_config.json
```

Then use it:

```bash
python3 reverse_proxy.py -c my_proxy_config.json
```

## Interactive Setup Script

The `setup_reverse_proxy.sh` script provides an interactive menu for:

1. Starting reverse proxy with default configuration
2. Starting with custom configuration file
3. Starting with SSL/TLS support
4. Testing configuration validity
5. Creating new configurations
6. Viewing real-time logs
7. Stopping all running instances

Simply run:

```bash
./setup_reverse_proxy.sh
```

## Load Balancing Algorithms

### Round-Robin

Distributes requests evenly across all healthy backend servers in a circular pattern.

```bash
python3 reverse_proxy.py -b http://server1 -b http://server2 -l round-robin
```

### Least Connections

Routes requests to the backend server with the fewest active connections.

```bash
python3 reverse_proxy.py -b http://server1 -b http://server2 -l least-conn
```

## Health Checks

The reverse proxy automatically performs health checks on backend servers every 30 seconds. Unhealthy servers are temporarily removed from the pool until they recover.

Health check logs appear as:
```
Health check: http://backend1:8001 is healthy
Health check: http://backend2:8001 is unhealthy
```

## Logging

All activity is logged to both:
- Console output (stdout)
- Log file: `reverse_proxy.log`

Log entries include:
- Connection establishment and termination
- Backend server selection
- Health check results
- Errors and warnings
- Data transfer statistics

View logs in real-time:

```bash
tail -f reverse_proxy.log
```

## Security Considerations

1. **SSL/TLS**: Use SSL certificates for encrypted connections
2. **Firewall**: Configure firewall rules to restrict access
3. **Authentication**: Implement authentication at the backend level
4. **Rate Limiting**: Consider adding rate limiting for production use
5. **Monitoring**: Regularly monitor logs for suspicious activity

## Troubleshooting

### Port Already in Use

```
Error: [Errno 98] Address already in use
```

Solution: Change the port or stop the conflicting service.

### Backend Server Unreachable

```
Error handling client: [Errno 111] Connection refused
```

Solution: Verify backend servers are running and accessible.

### SSL Certificate Issues

```
Error loading certificate
```

Solution: Ensure SSL certificate and key files exist and are readable.

## Performance Tuning

- Increase `max_connections` for high-traffic scenarios
- Adjust `timeout` based on backend response times
- Use `least-conn` load balancing for varying request durations
- Run multiple reverse proxy instances behind a load balancer for horizontal scaling

## Integration with RambaZamba

This reverse proxy integrates seamlessly with other RambaZamba tools:

- Use with `proxy_tool_v1.0.py` for proxy testing
- Combine with `network_scan.sh` for network discovery
- Monitor with `realtime_network.py` for traffic analysis
- Deploy alongside honeybots for security research

## License

This tool is part of the RambaZamba project and is licensed under the MIT License.

## Disclaimer

This reverse proxy is intended for legitimate networking purposes, testing, and educational use. Users are responsible for ensuring compliance with applicable laws and regulations.
