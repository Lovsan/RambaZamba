#!/usr/bin/env python3
"""
Reverse Proxy System with Traffic Monitoring and Automatic Proxy Rotation

Features:
- HTTP/HTTPS reverse proxy
- Traffic monitoring (inbound/outbound)
- Automatic proxy rotation with configurable intervals
- Proxy pool management (add/remove/validate proxies)
- Traffic statistics and logging
"""

import http.server
import socketserver
import threading
import time
import json
import logging
import socket
import ssl
import urllib.parse
import urllib.request
import urllib.error
import random
import argparse
from datetime import datetime
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
import os
import sys
import signal
import queue


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ProxyEntry:
    """Represents a proxy server in the pool"""
    host: str
    port: int
    proxy_type: str = "http"  # http, https, socks4, socks5
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: bool = True
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[float] = None
    last_validated: Optional[float] = None
    response_times: List[float] = field(default_factory=list)

    def get_url(self) -> str:
        """Get proxy URL for requests"""
        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        return f"{self.proxy_type}://{auth}{self.host}:{self.port}"

    def record_success(self, response_time: float):
        """Record a successful request"""
        self.success_count += 1
        self.last_used = time.time()
        self.response_times.append(response_time)
        # Keep only last 100 response times
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]

    def record_failure(self):
        """Record a failed request"""
        self.failure_count += 1
        self.last_used = time.time()

    def get_success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total

    def get_avg_response_time(self) -> float:
        """Calculate average response time"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "host": self.host,
            "port": self.port,
            "proxy_type": self.proxy_type,
            "is_active": self.is_active,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(self.get_success_rate() * 100, 2),
            "avg_response_time": round(self.get_avg_response_time(), 3),
            "last_used": self.last_used,
            "last_validated": self.last_validated,
        }


@dataclass
class TrafficStats:
    """Traffic statistics for monitoring"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    bytes_received: int = 0
    bytes_sent: int = 0
    start_time: float = field(default_factory=time.time)
    requests_per_minute: deque = field(default_factory=lambda: deque(maxlen=60))
    
    def record_request(self, success: bool, bytes_in: int, bytes_out: int):
        """Record a request"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.bytes_received += bytes_in
        self.bytes_sent += bytes_out
        
        # Track requests per minute
        current_minute = int(time.time() / 60)
        if self.requests_per_minute and self.requests_per_minute[-1][0] == current_minute:
            self.requests_per_minute[-1] = (current_minute, self.requests_per_minute[-1][1] + 1)
        else:
            self.requests_per_minute.append((current_minute, 1))

    def get_uptime(self) -> float:
        """Get uptime in seconds"""
        return time.time() - self.start_time

    def get_requests_rate(self) -> float:
        """Get average requests per second"""
        uptime = self.get_uptime()
        if uptime <= 0:
            return 0.0
        return self.total_requests / uptime

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.successful_requests / max(1, self.total_requests) * 100, 2),
            "bytes_received": self.bytes_received,
            "bytes_sent": self.bytes_sent,
            "uptime_seconds": round(self.get_uptime(), 2),
            "requests_per_second": round(self.get_requests_rate(), 2),
        }


class ProxyPool:
    """Manages a pool of proxy servers with rotation"""
    
    def __init__(self, rotation_interval: int = 60, validation_interval: int = 300):
        self.proxies: List[ProxyEntry] = []
        self.rotation_interval = rotation_interval  # seconds between rotations
        self.validation_interval = validation_interval  # seconds between validations
        self.current_proxy_index = 0
        self.last_rotation = time.time()
        self._lock = threading.Lock()
        self._running = False
        self._rotation_thread: Optional[threading.Thread] = None
        self._validation_thread: Optional[threading.Thread] = None
        self.validation_url = "http://httpbin.org/ip"
        self.validation_timeout = 10

    def add_proxy(self, host: str, port: int, proxy_type: str = "http",
                  username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """Add a proxy to the pool
        
        Args:
            host: Proxy host address
            port: Proxy port number
            proxy_type: Type of proxy (http, https, socks4, socks5)
            username: Optional username for authentication
            password: Optional password for authentication
            
        Returns:
            True if proxy was added, False if duplicate or invalid type
        """
        # Validate proxy type
        valid_types = {"http", "https", "socks4", "socks5"}
        if proxy_type.lower() not in valid_types:
            logger.warning(f"Invalid proxy type '{proxy_type}'. Must be one of: {valid_types}")
            return False
        
        proxy_type = proxy_type.lower()
        
        with self._lock:
            # Check for duplicates
            for proxy in self.proxies:
                if proxy.host == host and proxy.port == port:
                    logger.warning(f"Proxy {host}:{port} already exists in pool")
                    return False
            
            proxy = ProxyEntry(
                host=host,
                port=port,
                proxy_type=proxy_type,
                username=username,
                password=password
            )
            self.proxies.append(proxy)
            logger.info(f"Added proxy {host}:{port} to pool")
            return True

    def remove_proxy(self, host: str, port: int) -> bool:
        """Remove a proxy from the pool"""
        with self._lock:
            for i, proxy in enumerate(self.proxies):
                if proxy.host == host and proxy.port == port:
                    self.proxies.pop(i)
                    logger.info(f"Removed proxy {host}:{port} from pool")
                    return True
            return False

    def get_current_proxy(self) -> Optional[ProxyEntry]:
        """Get the current active proxy"""
        with self._lock:
            active_proxies = [p for p in self.proxies if p.is_active]
            if not active_proxies:
                return None
            
            self.current_proxy_index = self.current_proxy_index % len(active_proxies)
            return active_proxies[self.current_proxy_index]

    def rotate(self):
        """Rotate to the next proxy"""
        with self._lock:
            active_proxies = [p for p in self.proxies if p.is_active]
            if len(active_proxies) <= 1:
                return
            
            self.current_proxy_index = (self.current_proxy_index + 1) % len(active_proxies)
            self.last_rotation = time.time()
            current = active_proxies[self.current_proxy_index]
            logger.info(f"Rotated to proxy {current.host}:{current.port}")

    def validate_proxy(self, proxy: ProxyEntry) -> bool:
        """Validate a proxy is working"""
        start_time = time.time()
        try:
            proxy_handler = urllib.request.ProxyHandler({
                'http': proxy.get_url(),
                'https': proxy.get_url()
            })
            opener = urllib.request.build_opener(proxy_handler)
            
            request = urllib.request.Request(
                self.validation_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with opener.open(request, timeout=self.validation_timeout) as response:
                if response.getcode() == 200:
                    response_time = time.time() - start_time
                    proxy.record_success(response_time)
                    proxy.last_validated = time.time()
                    proxy.is_active = True
                    return True
                    
        except Exception as e:
            logger.debug(f"Proxy validation failed for {proxy.host}:{proxy.port}: {e}")
            proxy.record_failure()
            
        # Disable proxy if too many failures
        if proxy.failure_count > 5 and proxy.get_success_rate() < 0.3:
            proxy.is_active = False
            logger.warning(f"Disabled proxy {proxy.host}:{proxy.port} due to high failure rate")
            
        return False

    def validate_all_proxies(self):
        """Validate all proxies in the pool"""
        logger.info("Validating all proxies...")
        # Create a copy of the list for iteration since validate_proxy may modify 
        # proxy.is_active status which affects iteration over active proxies
        proxies_snapshot = self.proxies[:]
        for proxy in proxies_snapshot:
            self.validate_proxy(proxy)
        
        active_count = len([p for p in self.proxies if p.is_active])
        logger.info(f"Validation complete: {active_count}/{len(self.proxies)} proxies active")

    def start_rotation(self):
        """Start automatic rotation thread"""
        self._running = True
        
        def rotation_loop():
            while self._running:
                time.sleep(self.rotation_interval)
                if self._running:
                    self.rotate()
        
        self._rotation_thread = threading.Thread(target=rotation_loop, daemon=True)
        self._rotation_thread.start()
        logger.info(f"Started proxy rotation (interval: {self.rotation_interval}s)")

    def start_validation(self):
        """Start automatic validation thread"""
        def validation_loop():
            while self._running:
                time.sleep(self.validation_interval)
                if self._running:
                    self.validate_all_proxies()
        
        self._validation_thread = threading.Thread(target=validation_loop, daemon=True)
        self._validation_thread.start()
        logger.info(f"Started proxy validation (interval: {self.validation_interval}s)")

    def stop(self):
        """Stop rotation and validation threads"""
        self._running = False
        logger.info("Stopped proxy pool threads")

    def get_stats(self) -> List[dict]:
        """Get statistics for all proxies"""
        with self._lock:
            return [p.to_dict() for p in self.proxies]

    def load_from_file(self, filepath: str) -> int:
        """Load proxies from a file (one per line: host:port or host:port:type)"""
        count = 0
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(':')
                    if len(parts) >= 2:
                        host = parts[0]
                        try:
                            port = int(parts[1])
                            proxy_type = parts[2] if len(parts) > 2 else "http"
                            if self.add_proxy(host, port, proxy_type):
                                count += 1
                        except ValueError:
                            logger.warning(f"Invalid port in line: {line}")
                            continue
        except FileNotFoundError:
            logger.error(f"Proxy file not found: {filepath}")
        except IOError as e:
            logger.error(f"Error reading proxy file: {e}")
        
        logger.info(f"Loaded {count} proxies from {filepath}")
        return count

    def save_to_file(self, filepath: str):
        """Save proxies to a file"""
        try:
            with open(filepath, 'w') as f:
                for proxy in self.proxies:
                    f.write(f"{proxy.host}:{proxy.port}:{proxy.proxy_type}\n")
            logger.info(f"Saved {len(self.proxies)} proxies to {filepath}")
        except IOError as e:
            logger.error(f"Error saving proxy file: {e}")


class ReverseProxyHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for the reverse proxy"""
    
    # Class variables set by ReverseProxy
    proxy_pool: ProxyPool = None
    stats: TrafficStats = None
    target_host: str = None
    target_port: int = None
    use_ssl: bool = False
    
    def log_message(self, format_msg: str, *args):
        """Override to use our logger"""
        logger.debug("%s - %s", self.address_string(), format_msg % args)

    def do_GET(self):
        """Handle GET requests"""
        self.proxy_request()

    def do_POST(self):
        """Handle POST requests"""
        self.proxy_request()

    def do_PUT(self):
        """Handle PUT requests"""
        self.proxy_request()

    def do_DELETE(self):
        """Handle DELETE requests"""
        self.proxy_request()

    def do_HEAD(self):
        """Handle HEAD requests"""
        self.proxy_request()

    def do_OPTIONS(self):
        """Handle OPTIONS requests"""
        self.proxy_request()

    def do_PATCH(self):
        """Handle PATCH requests"""
        self.proxy_request()

    def proxy_request(self):
        """Forward the request through the proxy"""
        start_time = time.time()
        bytes_in = 0
        bytes_out = 0
        success = False

        try:
            # Get the current proxy from the pool
            proxy = self.proxy_pool.get_current_proxy() if self.proxy_pool else None
            
            # Build target URL
            scheme = "https" if self.use_ssl else "http"
            target_url = f"{scheme}://{self.target_host}:{self.target_port}{self.path}"
            
            # Read request body if present
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            bytes_in = content_length
            
            # Prepare headers (exclude hop-by-hop headers)
            headers = {}
            hop_by_hop = {'connection', 'keep-alive', 'proxy-authenticate', 
                         'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 
                         'upgrade', 'host'}
            
            for key, value in self.headers.items():
                if key.lower() not in hop_by_hop:
                    headers[key] = value
            
            # Add host header for target
            headers['Host'] = f"{self.target_host}:{self.target_port}"
            
            # Add X-Forwarded headers
            headers['X-Forwarded-For'] = self.client_address[0]
            headers['X-Forwarded-Proto'] = scheme
            headers['X-Real-IP'] = self.client_address[0]
            
            # Create request
            request = urllib.request.Request(
                target_url,
                data=body,
                headers=headers,
                method=self.command
            )
            
            # Set up proxy handler if we have a proxy
            if proxy:
                proxy_handler = urllib.request.ProxyHandler({
                    'http': proxy.get_url(),
                    'https': proxy.get_url()
                })
                opener = urllib.request.build_opener(proxy_handler)
            else:
                opener = urllib.request.build_opener()
            
            # Make request
            try:
                with opener.open(request, timeout=30) as response:
                    response_body = response.read()
                    bytes_out = len(response_body)
                    
                    # Send response status
                    self.send_response(response.getcode())
                    
                    # Send response headers
                    for key, value in response.getheaders():
                        if key.lower() not in hop_by_hop:
                            self.send_header(key, value)
                    self.end_headers()
                    
                    # Send response body
                    self.wfile.write(response_body)
                    
                    success = True
                    
                    # Record proxy success
                    if proxy:
                        proxy.record_success(time.time() - start_time)
                        
            except urllib.error.HTTPError as e:
                # Forward HTTP errors
                self.send_response(e.code)
                for key, value in e.headers.items():
                    if key.lower() not in hop_by_hop:
                        self.send_header(key, value)
                self.end_headers()
                
                body = e.read()
                bytes_out = len(body)
                self.wfile.write(body)
                
                # Still counts as successful proxy operation
                success = True
                if proxy:
                    proxy.record_success(time.time() - start_time)
                    
        except urllib.error.URLError as e:
            self.send_error(502, f"Bad Gateway: {e.reason}")
            if proxy:
                proxy.record_failure()
                
        except socket.timeout:
            self.send_error(504, "Gateway Timeout")
            if proxy:
                proxy.record_failure()
                
        except BrokenPipeError:
            # Client disconnected
            logger.debug("Client disconnected before response completed")
            
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {str(e)}")
            logger.exception("Error proxying request")
            if proxy:
                proxy.record_failure()
        
        finally:
            # Record statistics
            if self.stats:
                self.stats.record_request(success, bytes_in, bytes_out)
            
            # Log request
            elapsed = time.time() - start_time
            proxy_info = f" via {proxy.host}:{proxy.port}" if proxy else ""
            logger.info(
                f"{self.command} {self.path} -> {self.target_host}{proxy_info} "
                f"({elapsed:.3f}s, {bytes_in}B in, {bytes_out}B out)"
            )


class ReverseProxy:
    """
    Reverse Proxy Server with traffic monitoring and proxy rotation.
    
    Features:
    - HTTP/HTTPS reverse proxy
    - Traffic monitoring (inbound/outbound)
    - Automatic proxy rotation
    - Proxy pool management
    """
    
    def __init__(
        self,
        listen_host: str = "0.0.0.0",
        listen_port: int = 8888,
        target_host: str = "localhost",
        target_port: int = 80,
        use_ssl: bool = False,
        rotation_interval: int = 60,
        validation_interval: int = 300,
    ):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.target_host = target_host
        self.target_port = target_port
        self.use_ssl = use_ssl
        
        # Initialize proxy pool
        self.proxy_pool = ProxyPool(
            rotation_interval=rotation_interval,
            validation_interval=validation_interval
        )
        
        # Initialize statistics
        self.stats = TrafficStats()
        
        # Server instance
        self.server: Optional[socketserver.TCPServer] = None
        self._running = False
        self._server_thread: Optional[threading.Thread] = None
        
        # Log file
        self.log_file = "reverse_proxy.log"
        self._setup_file_logging()

    def _setup_file_logging(self):
        """Set up file logging"""
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)

    def start(self):
        """Start the reverse proxy server"""
        # Configure handler class variables
        ReverseProxyHandler.proxy_pool = self.proxy_pool
        ReverseProxyHandler.stats = self.stats
        ReverseProxyHandler.target_host = self.target_host
        ReverseProxyHandler.target_port = self.target_port
        ReverseProxyHandler.use_ssl = self.use_ssl
        
        # Create server
        self.server = socketserver.ThreadingTCPServer(
            (self.listen_host, self.listen_port),
            ReverseProxyHandler
        )
        self.server.allow_reuse_address = True
        
        # Start proxy pool threads
        self.proxy_pool.start_rotation()
        self.proxy_pool.start_validation()
        
        # Start server in a thread
        self._running = True
        self._server_thread = threading.Thread(target=self._serve, daemon=True)
        self._server_thread.start()
        
        logger.info(
            f"Reverse proxy started on {self.listen_host}:{self.listen_port} "
            f"-> {self.target_host}:{self.target_port}"
        )

    def _serve(self):
        """Serve requests"""
        while self._running:
            try:
                self.server.handle_request()
            except Exception as e:
                if self._running:
                    logger.exception("Error handling request")

    def stop(self):
        """Stop the reverse proxy server"""
        self._running = False
        self.proxy_pool.stop()
        
        if self.server:
            self.server.shutdown()
            
        logger.info("Reverse proxy stopped")

    def get_status(self) -> dict:
        """Get current status and statistics"""
        current_proxy = self.proxy_pool.get_current_proxy()
        return {
            "running": self._running,
            "listen_address": f"{self.listen_host}:{self.listen_port}",
            "target_address": f"{self.target_host}:{self.target_port}",
            "current_proxy": current_proxy.to_dict() if current_proxy else None,
            "proxy_count": len(self.proxy_pool.proxies),
            "active_proxy_count": len([p for p in self.proxy_pool.proxies if p.is_active]),
            "traffic_stats": self.stats.to_dict(),
            "proxy_stats": self.proxy_pool.get_stats(),
        }


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║               REVERSE PROXY WITH TRAFFIC MONITOR                 ║
║                   Advanced Proxy Management                      ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_help():
    """Print help information"""
    help_text = """
Commands:
  start                - Start the reverse proxy server
  stop                 - Stop the reverse proxy server
  status               - Show current status and statistics
  add <host:port>      - Add a proxy to the pool
  remove <host:port>   - Remove a proxy from the pool
  list                 - List all proxies in the pool
  rotate               - Manually rotate to the next proxy
  validate             - Validate all proxies
  load <file>          - Load proxies from a file
  save <file>          - Save proxies to a file
  clear                - Clear traffic statistics
  help                 - Show this help message
  quit                 - Exit the application
"""
    print(help_text)


def format_bytes(num_bytes: int) -> str:
    """Format bytes to human readable string"""
    size = float(num_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def interactive_mode(proxy: ReverseProxy):
    """Run in interactive mode"""
    print_banner()
    print_help()
    
    running = True
    
    def signal_handler(sig, frame):
        nonlocal running
        print("\n\nReceived interrupt signal. Shutting down...")
        proxy.stop()
        running = False
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    while running:
        try:
            command = input("\n[reverse-proxy]> ").strip().lower()
            parts = command.split()
            
            if not parts:
                continue
            
            cmd = parts[0]
            args = parts[1:]
            
            if cmd == "start":
                if not proxy._running:
                    proxy.start()
                    print("✅ Reverse proxy started")
                else:
                    print("⚠️  Proxy is already running")
                    
            elif cmd == "stop":
                if proxy._running:
                    proxy.stop()
                    print("✅ Reverse proxy stopped")
                else:
                    print("⚠️  Proxy is not running")
                    
            elif cmd == "status":
                status = proxy.get_status()
                print("\n📊 Status:")
                print(f"  Running: {'Yes' if status['running'] else 'No'}")
                print(f"  Listen: {status['listen_address']}")
                print(f"  Target: {status['target_address']}")
                print(f"  Proxies: {status['active_proxy_count']}/{status['proxy_count']} active")
                
                if status['current_proxy']:
                    cp = status['current_proxy']
                    print(f"  Current Proxy: {cp['host']}:{cp['port']}")
                    print(f"    Success Rate: {cp['success_rate']}%")
                    print(f"    Avg Response: {cp['avg_response_time']}s")
                
                ts = status['traffic_stats']
                print(f"\n📈 Traffic Statistics:")
                print(f"  Total Requests: {ts['total_requests']}")
                print(f"  Successful: {ts['successful_requests']} ({ts['success_rate']}%)")
                print(f"  Failed: {ts['failed_requests']}")
                print(f"  Data In: {format_bytes(ts['bytes_received'])}")
                print(f"  Data Out: {format_bytes(ts['bytes_sent'])}")
                print(f"  Rate: {ts['requests_per_second']} req/s")
                print(f"  Uptime: {ts['uptime_seconds']:.0f}s")
                
            elif cmd == "add":
                if not args:
                    print("❌ Usage: add <host:port[:type]>")
                    continue
                    
                parts = args[0].split(':')
                if len(parts) < 2:
                    print("❌ Invalid format. Use host:port[:type]")
                    continue
                    
                try:
                    host = parts[0]
                    port = int(parts[1])
                    proxy_type = parts[2] if len(parts) > 2 else "http"
                    
                    if proxy.proxy_pool.add_proxy(host, port, proxy_type):
                        print(f"✅ Added proxy {host}:{port}")
                    else:
                        print(f"⚠️  Proxy already exists")
                except ValueError:
                    print("❌ Invalid port number")
                    
            elif cmd == "remove":
                if not args:
                    print("❌ Usage: remove <host:port>")
                    continue
                    
                parts = args[0].split(':')
                if len(parts) < 2:
                    print("❌ Invalid format. Use host:port")
                    continue
                    
                try:
                    host = parts[0]
                    port = int(parts[1])
                    
                    if proxy.proxy_pool.remove_proxy(host, port):
                        print(f"✅ Removed proxy {host}:{port}")
                    else:
                        print(f"⚠️  Proxy not found")
                except ValueError:
                    print("❌ Invalid port number")
                    
            elif cmd == "list":
                proxies = proxy.proxy_pool.get_stats()
                if not proxies:
                    print("📭 No proxies in pool")
                else:
                    print(f"\n📋 Proxy Pool ({len(proxies)} proxies):")
                    print("-" * 70)
                    print(f"{'Host:Port':<25} {'Type':<8} {'Status':<10} {'Success':<10} {'Avg Time'}")
                    print("-" * 70)
                    
                    for p in proxies:
                        status = "Active" if p['is_active'] else "Inactive"
                        print(f"{p['host']}:{p['port']:<15} {p['proxy_type']:<8} {status:<10} {p['success_rate']}%{'':<5} {p['avg_response_time']:.3f}s")
                        
            elif cmd == "rotate":
                proxy.proxy_pool.rotate()
                current = proxy.proxy_pool.get_current_proxy()
                if current:
                    print(f"✅ Rotated to {current.host}:{current.port}")
                else:
                    print("⚠️  No active proxies available")
                    
            elif cmd == "validate":
                print("🔍 Validating proxies...")
                proxy.proxy_pool.validate_all_proxies()
                print("✅ Validation complete")
                
            elif cmd == "load":
                if not args:
                    print("❌ Usage: load <filename>")
                    continue
                    
                count = proxy.proxy_pool.load_from_file(args[0])
                print(f"✅ Loaded {count} proxies")
                
            elif cmd == "save":
                if not args:
                    print("❌ Usage: save <filename>")
                    continue
                    
                proxy.proxy_pool.save_to_file(args[0])
                print(f"✅ Saved proxies to {args[0]}")
                
            elif cmd == "clear":
                proxy.stats = TrafficStats()
                ReverseProxyHandler.stats = proxy.stats
                print("✅ Statistics cleared")
                
            elif cmd == "help":
                print_help()
                
            elif cmd in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                proxy.stop()
                running = False
                break
                
            else:
                print(f"❌ Unknown command: {cmd}")
                print("Type 'help' for available commands")
                
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\n")
            continue


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Reverse Proxy with Traffic Monitoring and Proxy Rotation"
    )
    parser.add_argument(
        "--listen-host",
        default="0.0.0.0",
        help="Host to listen on (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--listen-port",
        type=int,
        default=8888,
        help="Port to listen on (default: 8888)"
    )
    parser.add_argument(
        "--target-host",
        default="localhost",
        help="Target host to forward requests to (default: localhost)"
    )
    parser.add_argument(
        "--target-port",
        type=int,
        default=80,
        help="Target port to forward requests to (default: 80)"
    )
    parser.add_argument(
        "--ssl",
        action="store_true",
        help="Use SSL for target connection"
    )
    parser.add_argument(
        "--rotation-interval",
        type=int,
        default=60,
        help="Proxy rotation interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--validation-interval",
        type=int,
        default=300,
        help="Proxy validation interval in seconds (default: 300)"
    )
    parser.add_argument(
        "--proxy-file",
        help="File to load proxies from on startup"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run in daemon mode (no interactive prompt)"
    )
    
    args = parser.parse_args()
    
    # Create reverse proxy instance
    proxy = ReverseProxy(
        listen_host=args.listen_host,
        listen_port=args.listen_port,
        target_host=args.target_host,
        target_port=args.target_port,
        use_ssl=args.ssl,
        rotation_interval=args.rotation_interval,
        validation_interval=args.validation_interval,
    )
    
    # Load proxies from file if specified
    if args.proxy_file:
        proxy.proxy_pool.load_from_file(args.proxy_file)
    
    if args.daemon:
        # Run in daemon mode
        proxy.start()
        print(f"Reverse proxy running in daemon mode on {args.listen_host}:{args.listen_port}")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            proxy.stop()
    else:
        # Run in interactive mode
        interactive_mode(proxy)


if __name__ == "__main__":
    main()
