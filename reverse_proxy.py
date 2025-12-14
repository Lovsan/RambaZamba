#!/usr/bin/env python3
"""
Advanced Reverse Proxy Server
A professional HTTP/HTTPS reverse proxy with load balancing, SSL/TLS support,
health checks, and detailed logging capabilities.
"""

import socket
import threading
import select
import argparse
import json
import logging
import time
from datetime import datetime
from urllib.parse import urlparse
import ssl
import os
import sys

class ReverseProxyServer:
    def __init__(self, config_file=None, host='0.0.0.0', port=8080, 
                 backend_servers=None, ssl_cert=None, ssl_key=None,
                 max_connections=100, timeout=60, load_balance='round-robin'):
        """
        Initialize the reverse proxy server.
        
        Args:
            config_file: Path to JSON configuration file
            host: Host address to bind to
            port: Port to listen on
            backend_servers: List of backend server URLs
            ssl_cert: Path to SSL certificate file
            ssl_key: Path to SSL key file
            max_connections: Maximum concurrent connections
            timeout: Connection timeout in seconds
            load_balance: Load balancing algorithm (round-robin, least-conn)
        """
        self.host = host
        self.port = port
        self.backend_servers = backend_servers or []
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.max_connections = max_connections
        self.timeout = timeout
        self.load_balance_method = load_balance
        self.running = False
        self.current_backend_index = 0
        self.backend_health = {}
        self.connection_counts = {}
        
        # Load configuration from file if provided
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
        
        # Initialize backend server health status
        for server in self.backend_servers:
            self.backend_health[server] = True
            self.connection_counts[server] = 0
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging for the proxy server."""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('reverse_proxy.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self, config_file):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.host = config.get('host', self.host)
                self.port = config.get('port', self.port)
                self.backend_servers = config.get('backend_servers', self.backend_servers)
                self.ssl_cert = config.get('ssl_cert', self.ssl_cert)
                self.ssl_key = config.get('ssl_key', self.ssl_key)
                self.max_connections = config.get('max_connections', self.max_connections)
                self.timeout = config.get('timeout', self.timeout)
                self.load_balance_method = config.get('load_balance', self.load_balance_method)
            self.logger.info(f"Configuration loaded from {config_file}")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            
    def save_config(self, config_file):
        """Save current configuration to JSON file."""
        config = {
            'host': self.host,
            'port': self.port,
            'backend_servers': self.backend_servers,
            'ssl_cert': self.ssl_cert,
            'ssl_key': self.ssl_key,
            'max_connections': self.max_connections,
            'timeout': self.timeout,
            'load_balance': self.load_balance_method
        }
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            self.logger.info(f"Configuration saved to {config_file}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            
    def get_next_backend(self):
        """
        Select the next backend server based on load balancing algorithm.
        
        Returns:
            Backend server URL or None if no healthy servers available
        """
        healthy_servers = [s for s in self.backend_servers if self.backend_health.get(s, True)]
        
        if not healthy_servers:
            self.logger.warning("No healthy backend servers available")
            return None
            
        if self.load_balance_method == 'round-robin':
            server = healthy_servers[self.current_backend_index % len(healthy_servers)]
            self.current_backend_index += 1
            return server
            
        elif self.load_balance_method == 'least-conn':
            # Select server with least active connections
            min_conn = min(self.connection_counts.get(s, 0) for s in healthy_servers)
            for server in healthy_servers:
                if self.connection_counts.get(server, 0) == min_conn:
                    return server
                    
        return healthy_servers[0]
        
    def health_check(self):
        """Perform health checks on all backend servers."""
        while self.running:
            for server in self.backend_servers:
                try:
                    parsed = urlparse(server)
                    host = parsed.hostname
                    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
                    
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    self.backend_health[server] = (result == 0)
                    status = "healthy" if result == 0 else "unhealthy"
                    self.logger.debug(f"Health check: {server} is {status}")
                    
                except Exception as e:
                    self.backend_health[server] = False
                    self.logger.warning(f"Health check failed for {server}: {e}")
                    
            time.sleep(30)  # Health check every 30 seconds
            
    def forward_data(self, source, destination, direction):
        """
        Forward data between client and backend server.
        
        Args:
            source: Source socket
            destination: Destination socket
            direction: Direction of data flow (for logging)
        """
        try:
            while self.running:
                ready = select.select([source], [], [], 1)
                if ready[0]:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.sendall(data)
                    self.logger.debug(f"{direction}: Forwarded {len(data)} bytes")
        except Exception as e:
            self.logger.debug(f"Connection closed during {direction}: {e}")
            
    def handle_client(self, client_socket, client_address):
        """
        Handle incoming client connection.
        
        Args:
            client_socket: Client socket connection
            client_address: Client address tuple
        """
        backend_server = None
        backend_socket = None
        
        try:
            # Select backend server
            backend_url = self.get_next_backend()
            if not backend_url:
                self.logger.error(f"No backend servers available for {client_address}")
                client_socket.close()
                return
                
            parsed = urlparse(backend_url)
            backend_host = parsed.hostname
            backend_port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            backend_server = backend_url
            
            self.logger.info(f"Connecting {client_address} to {backend_host}:{backend_port}")
            
            # Connect to backend server
            backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            backend_socket.settimeout(self.timeout)
            backend_socket.connect((backend_host, backend_port))
            
            # Increment connection count
            self.connection_counts[backend_server] = self.connection_counts.get(backend_server, 0) + 1
            
            # Create forwarding threads
            client_to_server = threading.Thread(
                target=self.forward_data,
                args=(client_socket, backend_socket, f"{client_address} -> {backend_host}:{backend_port}")
            )
            server_to_client = threading.Thread(
                target=self.forward_data,
                args=(backend_socket, client_socket, f"{backend_host}:{backend_port} -> {client_address}")
            )
            
            client_to_server.daemon = True
            server_to_client.daemon = True
            
            client_to_server.start()
            server_to_client.start()
            
            # Wait for threads to complete
            client_to_server.join()
            server_to_client.join()
            
        except Exception as e:
            self.logger.error(f"Error handling client {client_address}: {e}")
            
        finally:
            # Clean up
            if backend_server:
                self.connection_counts[backend_server] = max(0, self.connection_counts.get(backend_server, 1) - 1)
            
            try:
                if backend_socket:
                    backend_socket.close()
                client_socket.close()
            except:
                pass
                
            self.logger.info(f"Connection closed for {client_address}")
            
    def start(self):
        """Start the reverse proxy server."""
        try:
            # Create server socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(self.max_connections)
            
            # Wrap with SSL if certificates provided
            if self.ssl_cert and self.ssl_key:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                context.load_cert_chain(self.ssl_cert, self.ssl_key)
                server_socket = context.wrap_socket(server_socket, server_side=True)
                self.logger.info(f"SSL/TLS enabled with certificate: {self.ssl_cert}")
            
            self.running = True
            
            # Start health check thread
            health_thread = threading.Thread(target=self.health_check)
            health_thread.daemon = True
            health_thread.start()
            
            self.logger.info(f"Reverse proxy server started on {self.host}:{self.port}")
            self.logger.info(f"Backend servers: {', '.join(self.backend_servers)}")
            self.logger.info(f"Load balancing method: {self.load_balance_method}")
            
            # Accept connections
            while self.running:
                try:
                    client_socket, client_address = server_socket.accept()
                    self.logger.info(f"New connection from {client_address}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except KeyboardInterrupt:
                    self.logger.info("Received shutdown signal")
                    break
                except Exception as e:
                    self.logger.error(f"Error accepting connection: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error starting server: {e}")
            
        finally:
            self.running = False
            try:
                server_socket.close()
            except:
                pass
            self.logger.info("Reverse proxy server stopped")
            
    def stop(self):
        """Stop the reverse proxy server."""
        self.running = False


def main():
    """Main entry point for the reverse proxy server."""
    parser = argparse.ArgumentParser(description='Advanced Reverse Proxy Server')
    parser.add_argument('-c', '--config', help='Path to configuration file')
    parser.add_argument('-H', '--host', default='0.0.0.0', help='Host address to bind to (default: 0.0.0.0)')
    parser.add_argument('-p', '--port', type=int, default=8080, help='Port to listen on (default: 8080)')
    parser.add_argument('-b', '--backend', action='append', help='Backend server URL (can be specified multiple times)')
    parser.add_argument('--ssl-cert', help='Path to SSL certificate file')
    parser.add_argument('--ssl-key', help='Path to SSL key file')
    parser.add_argument('-m', '--max-connections', type=int, default=100, help='Maximum concurrent connections')
    parser.add_argument('-t', '--timeout', type=int, default=60, help='Connection timeout in seconds')
    parser.add_argument('-l', '--load-balance', choices=['round-robin', 'least-conn'], 
                        default='round-robin', help='Load balancing algorithm')
    parser.add_argument('--save-config', help='Save configuration to file and exit')
    
    args = parser.parse_args()
    
    # Create proxy server instance
    proxy = ReverseProxyServer(
        config_file=args.config,
        host=args.host,
        port=args.port,
        backend_servers=args.backend,
        ssl_cert=args.ssl_cert,
        ssl_key=args.ssl_key,
        max_connections=args.max_connections,
        timeout=args.timeout,
        load_balance=args.load_balance
    )
    
    # Save configuration if requested
    if args.save_config:
        proxy.save_config(args.save_config)
        print(f"Configuration saved to {args.save_config}")
        return
    
    # Validate configuration
    if not proxy.backend_servers:
        print("Error: No backend servers specified. Use -b or --config to specify backends.")
        parser.print_help()
        return
    
    # Start the server
    try:
        proxy.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        proxy.stop()


if __name__ == '__main__':
    main()
