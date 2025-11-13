import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import json
import threading
import time
import csv
from datetime import datetime
import socket
import geoip2.database
import os
import re
from urllib.parse import urlparse
import socks
import http.client
import ssl

class ProxyTesterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Proxy Tester Pro")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize variables
        self.proxies = []
        self.testing = False
        self.geoip_reader = None
        self.home_api_url = tk.StringVar(value="http://httpbin.org/ip")
        self.home_api_key = tk.StringVar()
        
        # Try to initialize GeoIP database
        try:
            if os.path.exists("GeoLite2-City.mmdb"):
                self.geoip_reader = geoip2.database.Reader("GeoLite2-City.mmdb")
            else:
                print("GeoIP database not found. Location data will not be available.")
        except Exception as e:
            print(f"Error loading GeoIP database: {e}")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main testing tab
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Proxy Testing")
        
        # Proxy discovery tab
        self.discovery_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.discovery_tab, text="Proxy Discovery")
        
        # Home API tab
        self.api_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.api_tab, text="Home API")
        
        self.setup_main_tab()
        self.setup_discovery_tab()
        self.setup_api_tab()
        
    def setup_main_tab(self):
        # Top controls frame
        controls_frame = ttk.LabelFrame(self.main_tab, text="Controls", padding="10")
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Input section
        input_frame = ttk.Frame(controls_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Add Proxy (ip:port:type):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.proxy_entry = ttk.Entry(input_frame, width=25)
        self.proxy_entry.grid(row=0, column=1, padx=(0, 10))
        self.proxy_entry.insert(0, "ip:port or ip:port:type")
        self.proxy_entry.bind("<FocusIn>", self.clear_placeholder)
        self.proxy_entry.bind("<Return>", self.add_proxy_from_entry)
        
        ttk.Button(input_frame, text="Add", command=self.add_proxy_from_entry).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(input_frame, text="Load from File", command=self.load_from_file).grid(row=0, column=3, padx=(0, 10))
        ttk.Button(input_frame, text="Clear All", command=self.clear_all).grid(row=0, column=4)
        
        # Test controls
        test_frame = ttk.Frame(controls_frame)
        test_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(test_frame, text="Test URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.test_url = ttk.Entry(test_frame, width=40)
        self.test_url.insert(0, "http://httpbin.org/ip")
        self.test_url.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(test_frame, text="Timeout (s):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.timeout_var = tk.StringVar(value="10")
        ttk.Entry(test_frame, textvariable=self.timeout_var, width=5).grid(row=0, column=3, padx=(0, 10))
        
        ttk.Button(test_frame, text="Start Test", command=self.start_test).grid(row=0, column=4, padx=(0, 10))
        ttk.Button(test_frame, text="Stop Test", command=self.stop_test).grid(row=0, column=5)
        ttk.Button(test_frame, text="Test Home API", command=self.test_home_api).grid(row=0, column=6, padx=(0, 10))
        
        # Filter controls
        filter_frame = ttk.Frame(controls_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.filter_entry = ttk.Entry(filter_frame, width=20)
        self.filter_entry.grid(row=0, column=1, padx=(0, 10))
        self.filter_entry.bind("<KeyRelease>", self.apply_filter)
        
        ttk.Button(filter_frame, text="Working Only", command=self.filter_working).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(filter_frame, text="Fast Only (<2s)", command=self.filter_fast).grid(row=0, column=3, padx=(0, 10))
        ttk.Button(filter_frame, text="Secure Only", command=self.filter_secure).grid(row=0, column=4, padx=(0, 10))
        ttk.Button(filter_frame, text="Clear Filter", command=self.clear_filter).grid(row=0, column=5, padx=(0, 10))
        
        # Proxy list frame
        list_frame = ttk.LabelFrame(self.main_tab, text="Proxy List", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("Proxy", "Type", "Status", "Response Time", "Security", "Country", "City", "ISP", "Last Tested")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # Define headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80)
        
        # Adjust column widths
        self.tree.column("Proxy", width=150)
        self.tree.column("Type", width=80)
        self.tree.column("Security", width=100)
        self.tree.column("Country", width=100)
        self.tree.column("City", width=100)
        self.tree.column("ISP", width=120)
        self.tree.column("Last Tested", width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind double-click to remove proxy
        self.tree.bind("<Double-1>", self.remove_selected_proxy)
        
        # Bottom buttons
        button_frame = ttk.Frame(self.main_tab)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Export Working", command=self.export_working).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Export All", command=self.export_all).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Remove Failed", command=self.remove_failed).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected_proxy).pack(side=tk.LEFT)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.main_tab, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
    def setup_discovery_tab(self):
        # Discovery controls
        discovery_frame = ttk.LabelFrame(self.discovery_tab, text="Proxy Discovery", padding="10")
        discovery_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Source selection
        source_frame = ttk.Frame(discovery_frame)
        source_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(source_frame, text="Discovery Source:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.source_var = tk.StringVar(value="free_proxy_list")
        sources = [
            ("Free Proxy List", "free_proxy_list"),
            ("SSL Proxies", "ssl_proxies"),
            ("US Proxies", "us_proxies"),
            ("UK Proxies", "uk_proxies"),
            ("SOCKS Proxies", "socks_proxies")
        ]
        
        for i, (text, value) in enumerate(sources):
            ttk.Radiobutton(source_frame, text=text, variable=self.source_var, value=value).grid(
                row=0, column=i+1, padx=(0, 10))
        
        # Type selection
        type_frame = ttk.Frame(discovery_frame)
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="Proxy Types:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.http_var = tk.BooleanVar(value=True)
        self.https_var = tk.BooleanVar(value=True)
        self.socks4_var = tk.BooleanVar(value=True)
        self.socks5_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(type_frame, text="HTTP", variable=self.http_var).grid(row=0, column=1, padx=(0, 10))
        ttk.Checkbutton(type_frame, text="HTTPS", variable=self.https_var).grid(row=0, column=2, padx=(0, 10))
        ttk.Checkbutton(type_frame, text="SOCKS4", variable=self.socks4_var).grid(row=0, column=3, padx=(0, 10))
        ttk.Checkbutton(type_frame, text="SOCKS5", variable=self.socks5_var).grid(row=0, column=4, padx=(0, 10))
        
        # Discovery buttons
        button_frame = ttk.Frame(discovery_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Discover Proxies", command=self.discover_proxies).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Test Discovered", command=self.test_discovered).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Add to Main List", command=self.add_discovered_to_main).pack(side=tk.LEFT)
        
        # Results frame
        results_frame = ttk.LabelFrame(self.discovery_tab, text="Discovered Proxies", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text area for discovered proxies
        self.discovered_text = scrolledtext.ScrolledText(results_frame, height=15, width=100)
        self.discovered_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_api_tab(self):
        # Home API configuration
        api_frame = ttk.LabelFrame(self.api_tab, text="Home API Configuration", padding="10")
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        # API URL
        url_frame = ttk.Frame(api_frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="API URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.home_api_url_entry = ttk.Entry(url_frame, textvariable=self.home_api_url, width=50)
        self.home_api_url_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(0, 10))
        
        # API Key
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(key_frame, text="API Key (optional):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.home_api_key_entry = ttk.Entry(key_frame, textvariable=self.home_api_key, width=30, show="*")
        self.home_api_key_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # API Test buttons
        test_frame = ttk.Frame(api_frame)
        test_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(test_frame, text="Test API Connection", command=self.test_api_connection).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(test_frame, text="Test All Proxies with API", command=self.test_all_with_api).pack(side=tk.LEFT)
        
        # API Results
        results_frame = ttk.LabelFrame(self.api_tab, text="API Test Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.api_results_text = scrolledtext.ScrolledText(results_frame, height=15, width=100)
        self.api_results_text.pack(fill=tk.BOTH, expand=True)
        
    def clear_placeholder(self, event):
        if self.proxy_entry.get() == "ip:port or ip:port:type":
            self.proxy_entry.delete(0, tk.END)
            
    def add_proxy_from_entry(self, event=None):
        proxy_str = self.proxy_entry.get().strip()
        if proxy_str and proxy_str != "ip:port or ip:port:type":
            self.add_proxy(proxy_str)
            self.proxy_entry.delete(0, tk.END)
            
    def add_proxy(self, proxy_str):
        # Parse proxy string (ip:port or ip:port:type)
        parts = proxy_str.split(":")
        if len(parts) < 2:
            messagebox.showerror("Error", "Invalid proxy format. Use ip:port or ip:port:type")
            return
            
        ip = parts[0]
        port = parts[1]
        proxy_type = "http"  # Default type
        
        if len(parts) >= 3:
            proxy_type = parts[2].lower()
            
        # Validate IP and port
        try:
            socket.inet_aton(ip)
            int(port)
        except (socket.error, ValueError):
            messagebox.showerror("Error", "Invalid IP address or port")
            return
            
        proxy_full = f"{ip}:{port}"
        
        # Check if proxy already exists
        for proxy in self.proxies:
            if proxy["proxy"] == proxy_full:
                messagebox.showinfo("Info", "Proxy already in list")
                return
                
        # Add to list
        proxy_data = {
            "proxy": proxy_full,
            "type": proxy_type,
            "status": "Not Tested",
            "response_time": "",
            "security": "Unknown",
            "country": "",
            "city": "",
            "isp": "",
            "last_tested": ""
        }
        
        self.proxies.append(proxy_data)
        self.update_treeview()
        self.status_var.set(f"Added proxy: {proxy_full} ({proxy_type})")
        
    def load_from_file(self):
        file_path = filedialog.askopenfilename(
            title="Select proxy file",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'proxy' in item:
                                self.add_proxy(item['proxy'])
                            elif isinstance(item, str):
                                self.add_proxy(item)
                    elif isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, str):
                                self.add_proxy(value)
            else:
                with open(file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.add_proxy(line)
                            
            self.status_var.set(f"Loaded proxies from {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
            
    def clear_all(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all proxies?"):
            self.proxies.clear()
            self.update_treeview()
            self.status_var.set("Cleared all proxies")
            
    def start_test(self):
        if not self.proxies:
            messagebox.showwarning("Warning", "No proxies to test")
            return
            
        self.testing = True
        self.status_var.set("Testing proxies...")
        
        # Start testing in a separate thread
        thread = threading.Thread(target=self.test_proxies)
        thread.daemon = True
        thread.start()
        
    def stop_test(self):
        self.testing = False
        self.status_var.set("Test stopped by user")
                
    def test_proxies(self):
        test_url = self.test_url.get()
        timeout = int(self.timeout_var.get())
        
        for i, proxy_data in enumerate(self.proxies):
            if not self.testing:
                break
                
            proxy_str = proxy_data["proxy"]
            proxy_type = proxy_data.get("type", "http")
            self.status_var.set(f"Testing {proxy_str} ({i+1}/{len(self.proxies)})")
            
            start_time = time.time()
            try:
                # Test based on proxy type
                if proxy_type in ["socks4", "socks5"]:
                    response = self.test_socks_proxy(proxy_str, proxy_type, test_url, timeout)
                else:
                    proxies = {
                        "http": f"{proxy_type}://{proxy_str}",
                        "https": f"{proxy_type}://{proxy_str}"
                    }
                    response = requests.get(test_url, proxies=proxies, timeout=timeout)
                
                if response.status_code == 200:
                    response_time = round(time.time() - start_time, 2)
                    proxy_data["status"] = "Working"
                    proxy_data["response_time"] = f"{response_time}s"
                    
                    # Security assessment
                    security = self.assess_security(response, proxy_data)
                    proxy_data["security"] = security
                    
                    # Get location info if available
                    if self.geoip_reader:
                        try:
                            ip = proxy_str.split(":")[0]
                            response_geo = self.geoip_reader.city(ip)
                            proxy_data["country"] = response_geo.country.name
                            proxy_data["city"] = response_geo.city.name
                            proxy_data["isp"] = "N/A"  # Not available in free version
                        except Exception:
                            proxy_data["country"] = "Unknown"
                            proxy_data["city"] = "Unknown"
                            proxy_data["isp"] = "Unknown"
                else:
                    proxy_data["status"] = f"Failed ({response.status_code})"
                    proxy_data["response_time"] = ""
                    proxy_data["security"] = "Failed"
            except Exception as e:
                proxy_data["status"] = "Failed"
                proxy_data["response_time"] = ""
                proxy_data["security"] = "Failed"
                
            proxy_data["last_tested"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update UI in main thread
            self.root.after(0, self.update_treeview)
            
        self.testing = False
        self.status_var.set("Test completed")
        
    def test_socks_proxy(self, proxy_str, proxy_type, test_url, timeout):
        """Test SOCKS proxy"""
        ip, port = proxy_str.split(":")
        port = int(port)
        
        # Set SOCKS proxy
        if proxy_type == "socks4":
            socks.set_default_proxy(socks.SOCKS4, ip, port)
        else:  # socks5
            socks.set_default_proxy(socks.SOCKS5, ip, port)
            
        socket.socket = socks.socksocket
        
        try:
            response = requests.get(test_url, timeout=timeout)
            return response
        finally:
            # Reset to default socket
            socks.set_default_proxy()
            
    def assess_security(self, response, proxy_data):
        """Assess proxy security based on response headers and behavior"""
        security_score = 0
        headers = response.headers
        
        # Check for security headers
        if 'X-Forwarded-For' in headers:
            security_score += 1  # Shows real IP - not secure
            
        if 'Via' in headers:
            security_score += 1  # Shows proxy usage
            
        # Check if content was modified
        if len(response.content) < 100:
            security_score -= 1  # Suspiciously small response
            
        # Check response time for anomalies
        try:
            response_time = float(proxy_data["response_time"].replace('s', ''))
            if response_time > 10:
                security_score -= 1  # Very slow - might be logging
        except:
            pass
            
        # Determine security level
        if security_score >= 2:
            return "Low"
        elif security_score >= 0:
            return "Medium"
        else:
            return "High"
            
    def update_treeview(self):
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add proxies
        for proxy_data in self.proxies:
            values = (
                proxy_data["proxy"],
                proxy_data.get("type", "http"),
                proxy_data["status"],
                proxy_data["response_time"],
                proxy_data.get("security", "Unknown"),
                proxy_data["country"],
                proxy_data["city"],
                proxy_data["isp"],
                proxy_data["last_tested"]
            )
            self.tree.insert("", tk.END, values=values)
            
    def remove_selected_proxy(self, event=None):
        selected = self.tree.selection()
        if selected:
            index = self.tree.index(selected[0])
            if 0 <= index < len(self.proxies):
                proxy = self.proxies[index]["proxy"]
                self.proxies.pop(index)
                self.update_treeview()
                self.status_var.set(f"Removed proxy: {proxy}")
                
    def remove_failed(self):
        initial_count = len(self.proxies)
        self.proxies = [p for p in self.proxies if p["status"] == "Working"]
        removed_count = initial_count - len(self.proxies)
        self.update_treeview()
        self.status_var.set(f"Removed {removed_count} failed proxies")
        
    def apply_filter(self, event=None):
        filter_text = self.filter_entry.get().lower()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for proxy_data in self.proxies:
            if (filter_text in proxy_data["proxy"].lower() or 
                filter_text in proxy_data["status"].lower() or 
                filter_text in proxy_data.get("type", "").lower() or
                filter_text in proxy_data.get("security", "").lower() or
                filter_text in proxy_data["country"].lower() or 
                filter_text in proxy_data["city"].lower()):
                values = (
                    proxy_data["proxy"],
                    proxy_data.get("type", "http"),
                    proxy_data["status"],
                    proxy_data["response_time"],
                    proxy_data.get("security", "Unknown"),
                    proxy_data["country"],
                    proxy_data["city"],
                    proxy_data["isp"],
                    proxy_data["last_tested"]
                )
                self.tree.insert("", tk.END, values=values)
                
    def filter_working(self):
        self.filter_entry.delete(0, tk.END)
        self.filter_entry.insert(0, "Working")
        self.apply_filter()
        
    def filter_fast(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for proxy_data in self.proxies:
            try:
                if proxy_data["response_time"] and float(proxy_data["response_time"].replace('s', '')) < 2:
                    values = (
                        proxy_data["proxy"],
                        proxy_data.get("type", "http"),
                        proxy_data["status"],
                        proxy_data["response_time"],
                        proxy_data.get("security", "Unknown"),
                        proxy_data["country"],
                        proxy_data["city"],
                        proxy_data["isp"],
                        proxy_data["last_tested"]
                    )
                    self.tree.insert("", tk.END, values=values)
            except ValueError:
                continue
                
    def filter_secure(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for proxy_data in self.proxies:
            if proxy_data.get("security", "") in ["High", "Medium"]:
                values = (
                    proxy_data["proxy"],
                    proxy_data.get("type", "http"),
                    proxy_data["status"],
                    proxy_data["response_time"],
                    proxy_data.get("security", "Unknown"),
                    proxy_data["country"],
                    proxy_data["city"],
                    proxy_data["isp"],
                    proxy_data["last_tested"]
                )
                self.tree.insert("", tk.END, values=values)
                
    def clear_filter(self):
        self.filter_entry.delete(0, tk.END)
        self.update_treeview()
        
    def export_working(self):
        working_proxies = [p for p in self.proxies if p["status"] == "Working"]
        self.export_proxies(working_proxies, "working_proxies")
        
    def export_all(self):
        self.export_proxies(self.proxies, "all_proxies")
        
    def export_proxies(self, proxies, filename_prefix):
        if not proxies:
            messagebox.showwarning("Warning", "No proxies to export")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Export proxies",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("CSV files", "*.csv")]
        )
        
        if not file_path:
            return
            
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'w') as f:
                    json.dump([{"proxy": p["proxy"], "type": p.get("type", "http")} for p in proxies], f, indent=2)
            elif file_path.endswith('.csv'):
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Proxy", "Type", "Status", "Response Time", "Security", "Country", "City", "ISP", "Last Tested"])
                    for p in proxies:
                        writer.writerow([
                            p["proxy"], p.get("type", "http"), p["status"], p["response_time"], 
                            p.get("security", "Unknown"), p["country"], p["city"], p["isp"], p["last_tested"]
                        ])
            else:
                with open(file_path, 'w') as f:
                    for p in proxies:
                        f.write(f"{p['proxy']}:{p.get('type', 'http')}\n")
                        
            self.status_var.set(f"Exported {len(proxies)} proxies to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {str(e)}")

    # Discovery tab methods
    def discover_proxies(self):
        self.status_var.set("Discovering proxies...")
        thread = threading.Thread(target=self._discover_proxies_thread)
        thread.daemon = True
        thread.start()
        
    def _discover_proxies_thread(self):
        try:
            source = self.source_var.get()
            discovered = []
            
            if source == "free_proxy_list":
                discovered = self.scrape_free_proxy_list()
            elif source == "ssl_proxies":
                discovered = self.scrape_ssl_proxies()
            elif source == "socks_proxies":
                discovered = self.scrape_socks_proxies()
            else:
                discovered = self.scrape_generic_proxies()
                
            # Filter by selected types
            filtered_proxies = []
            for proxy in discovered:
                proxy_type = proxy.get("type", "http")
                if ((proxy_type == "http" and self.http_var.get()) or
                    (proxy_type == "https" and self.https_var.get()) or
                    (proxy_type == "socks4" and self.socks4_var.get()) or
                    (proxy_type == "socks5" and self.socks5_var.get())):
                    filtered_proxies.append(proxy)
                    
            # Update UI
            self.root.after(0, self.update_discovered_proxies, filtered_proxies)
            self.status_var.set(f"Discovered {len(filtered_proxies)} proxies")
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Discovery failed: {str(e)}"))
            self.status_var.set("Discovery failed")
            
    def scrape_free_proxy_list(self):
        """Scrape proxies from free-proxy-list.net"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            url = "https://free-proxy-list.net/"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            proxies = []
            table = soup.find('table', {'id': 'proxylisttable'})
            if table:
                for row in table.tbody.find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) >= 7:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        is_https = cols[6].text.strip() == 'yes'
                        proxy_type = "https" if is_https else "http"
                        proxies.append({
                            "proxy": f"{ip}:{port}",
                            "type": proxy_type,
                            "country": cols[3].text.strip(),
                            "anonymity": cols[4].text.strip()
                        })
            return proxies
        except Exception as e:
            print(f"Error scraping free proxy list: {e}")
            return []
            
    def scrape_ssl_proxies(self):
        """Scrape SSL proxies"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            url = "https://www.sslproxies.org/"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            proxies = []
            table = soup.find('table', {'class': 'table table-striped table-bordered'})
            if table:
                for row in table.tbody.find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        proxies.append({
                            "proxy": f"{ip}:{port}",
                            "type": "https",
                            "country": cols[3].text.strip() if len(cols) > 3 else "Unknown"
                        })
            return proxies
        except Exception as e:
            print(f"Error scraping SSL proxies: {e}")
            return []
            
    def scrape_socks_proxies(self):
        """Scrape SOCKS proxies"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            url = "https://www.socks-proxy.net/"
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            proxies = []
            table = soup.find('table', {'id': 'proxylisttable'})
            if table:
                for row in table.tbody.find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) >= 7:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        proxy_type = cols[4].text.strip().lower()
                        if proxy_type in ['socks4', 'socks5']:
                            proxies.append({
                                "proxy": f"{ip}:{port}",
                                "type": proxy_type,
                                "country": cols[2].text.strip()
                            })
            return proxies
        except Exception as e:
            print(f"Error scraping SOCKS proxies: {e}")
            return []
            
    def scrape_generic_proxies(self):
        """Generic proxy scraper for other sources"""
        # This can be expanded with more sources
        return []
        
    def update_discovered_proxies(self, proxies):
        self.discovered_proxies = proxies
        self.discovered_text.delete(1.0, tk.END)
        
        for proxy in proxies:
            proxy_info = f"{proxy['proxy']} ({proxy.get('type', 'http')})"
            if 'country' in proxy:
                proxy_info += f" - {proxy['country']}"
            if 'anonymity' in proxy:
                proxy_info += f" - {proxy['anonymity']}"
            self.discovered_text.insert(tk.END, proxy_info + "\n")
            
    def test_discovered(self):
        if not hasattr(self, 'discovered_proxies') or not self.discovered_proxies:
            messagebox.showwarning("Warning", "No discovered proxies to test")
            return
            
        self.status_var.set("Testing discovered proxies...")
        thread = threading.Thread(target=self._test_discovered_thread)
        thread.daemon = True
        thread.start()
        
    def _test_discovered_thread(self):
        test_url = "http://httpbin.org/ip"
        timeout = int(self.timeout_var.get())
        
        working_proxies = []
        
        for i, proxy_data in enumerate(self.discovered_proxies):
            proxy_str = proxy_data["proxy"]
            proxy_type = proxy_data.get("type", "http")
            
            try:
                start_time = time.time()
                
                if proxy_type in ["socks4", "socks5"]:
                    response = self.test_socks_proxy(proxy_str, proxy_type, test_url, timeout)
                else:
                    proxies = {
                        "http": f"{proxy_type}://{proxy_str}",
                        "https": f"{proxy_type}://{proxy_str}"
                    }
                    response = requests.get(test_url, proxies=proxies, timeout=timeout)
                
                if response.status_code == 200:
                    response_time = round(time.time() - start_time, 2)
                    proxy_data["status"] = "Working"
                    proxy_data["response_time"] = f"{response_time}s"
                    working_proxies.append(proxy_data)
                    
            except Exception:
                proxy_data["status"] = "Failed"
                
        # Update UI
        self.root.after(0, self.update_discovered_results, working_proxies)
        self.status_var.set(f"Tested {len(self.discovered_proxies)} proxies, {len(working_proxies)} working")
        
    def update_discovered_results(self, working_proxies):
        self.discovered_text.delete(1.0, tk.END)
        self.discovered_text.insert(tk.END, f"=== WORKING PROXIES ({len(working_proxies)} found) ===\n\n")
        
        for proxy in working_proxies:
            proxy_info = f"{proxy['proxy']} ({proxy.get('type', 'http')}) - {proxy['response_time']}"
            if 'country' in proxy:
                proxy_info += f" - {proxy['country']}"
            self.discovered_text.insert(tk.END, proxy_info + "\n")
            
    def add_discovered_to_main(self):
        if not hasattr(self, 'discovered_proxies') or not self.discovered_proxies:
            messagebox.showwarning("Warning", "No discovered proxies to add")
            return
            
        # Add only working proxies if available
        working_proxies = [p for p in self.discovered_proxies if p.get("status") == "Working"]
        proxies_to_add = working_proxies if working_proxies else self.discovered_proxies
        
        for proxy in proxies_to_add:
            # Check if already exists
            if not any(p["proxy"] == proxy["proxy"] for p in self.proxies):
                self.proxies.append({
                    "proxy": proxy["proxy"],
                    "type": proxy.get("type", "http"),
                    "status": proxy.get("status", "Not Tested"),
                    "response_time": proxy.get("response_time", ""),
                    "security": "Unknown",
                    "country": proxy.get("country", ""),
                    "city": "",
                    "isp": "",
                    "last_tested": ""
                })
                
        self.update_treeview()
        self.status_var.set(f"Added {len(proxies_to_add)} proxies to main list")

    # Home API methods
    def test_api_connection(self):
        api_url = self.home_api_url.get()
        api_key = self.home_api_key.get()
        
        self.status_var.set("Testing API connection...")
        thread = threading.Thread(target=self._test_api_connection_thread, args=(api_url, api_key))
        thread.daemon = True
        thread.start()
        
    def _test_api_connection_thread(self, api_url, api_key):
        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
                
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = f"✓ API Connection Successful\nStatus: {response.status_code}\nResponse: {response.text[:200]}\n\n"
            else:
                result = f"✗ API Connection Failed\nStatus: {response.status_code}\nError: {response.text[:200]}\n\n"
                
        except Exception as e:
            result = f"✗ API Connection Error\nError: {str(e)}\n\n"
            
        self.root.after(0, self.update_api_results, result)
        self.status_var.set("API test completed")
        
    def test_home_api(self):
        if not self.proxies:
            messagebox.showwarning("Warning", "No proxies to test with API")
            return
            
        self.status_var.set("Testing proxies with Home API...")
        thread = threading.Thread(target=self._test_home_api_thread)
        thread.daemon = True
        thread.start()
        
    def _test_home_api_thread(self):
        api_url = self.home_api_url.get()
        api_key = self.home_api_key.get()
        timeout = int(self.timeout_var.get())
        
        results = "=== HOME API PROXY TEST RESULTS ===\n\n"
        
        for i, proxy_data in enumerate(self.proxies):
            if not self.testing:  # Use the same testing flag
                break
                
            proxy_str = proxy_data["proxy"]
            proxy_type = proxy_data.get("type", "http")
            
            try:
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                    
                start_time = time.time()
                
                if proxy_type in ["socks4", "socks5"]:
                    response = self.test_socks_proxy(proxy_str, proxy_type, api_url, timeout)
                else:
                    proxies = {
                        "http": f"{proxy_type}://{proxy_str}",
                        "https": f"{proxy_type}://{proxy_str}"
                    }
                    response = requests.get(api_url, proxies=proxies, headers=headers, timeout=timeout)
                
                if response.status_code == 200:
                    response_time = round(time.time() - start_time, 2)
                    results += f"✓ {proxy_str} ({proxy_type}): SUCCESS - {response_time}s\n"
                    results += f"   Response: {response.text[:100]}...\n\n"
                else:
                    results += f"✗ {proxy_str} ({proxy_type}): FAILED - Status {response.status_code}\n\n"
                    
            except Exception as e:
                results += f"✗ {proxy_str} ({proxy_type}): ERROR - {str(e)}\n\n"
                
        self.root.after(0, self.update_api_results, results)
        self.status_var.set("Home API testing completed")
        
    def test_all_with_api(self):
        if not self.proxies:
            messagebox.showwarning("Warning", "No proxies to test")
            return
            
        self.testing = True
        self.status_var.set("Testing all proxies with API...")
        thread = threading.Thread(target=self._test_all_with_api_thread)
        thread.daemon = True
        thread.start()
        
    def _test_all_with_api_thread(self):
        api_url = self.home_api_url.get()
        api_key = self.home_api_key.get()
        timeout = int(self.timeout_var.get())
        
        for i, proxy_data in enumerate(self.proxies):
            if not self.testing:
                break
                
            proxy_str = proxy_data["proxy"]
            proxy_type = proxy_data.get("type", "http")
            self.status_var.set(f"Testing {proxy_str} with API ({i+1}/{len(self.proxies)})")
            
            try:
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                    
                start_time = time.time()
                
                if proxy_type in ["socks4", "socks5"]:
                    response = self.test_socks_proxy(proxy_str, proxy_type, api_url, timeout)
                else:
                    proxies = {
                        "http": f"{proxy_type}://{proxy_str}",
                        "https": f"{proxy_type}://{proxy_str}"
                    }
                    response = requests.get(api_url, proxies=proxies, headers=headers, timeout=timeout)
                
                if response.status_code == 200:
                    response_time = round(time.time() - start_time, 2)
                    proxy_data["status"] = "Working (API)"
                    proxy_data["response_time"] = f"{response_time}s"
                    
                    # Enhanced security assessment for API
                    security = self.assess_api_security(response, proxy_data)
                    proxy_data["security"] = security
                else:
                    proxy_data["status"] = f"Failed (API {response.status_code})"
                    proxy_data["response_time"] = ""
                    proxy_data["security"] = "Failed"
            except Exception as e:
                proxy_data["status"] = f"Failed (API Error)"
                proxy_data["response_time"] = ""
                proxy_data["security"] = "Failed"
                
            proxy_data["last_tested"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update UI in main thread
            self.root.after(0, self.update_treeview)
            
        self.testing = False
        self.status_var.set("API testing completed")
        
    def assess_api_security(self, response, proxy_data):
        """Enhanced security assessment for API testing"""
        security_score = 0
        headers = response.headers
        
        # Check for security headers in API response
        security_headers = ['X-Content-Type-Options', 'X-Frame-Options', 'X-XSS-Protection', 
                           'Strict-Transport-Security', 'Content-Security-Policy']
        
        for header in security_headers:
            if header in headers:
                security_score += 1
                
        # Check if response was modified
        if 'Via' in headers:
            security_score -= 1  # Shows proxy was used
            
        # Check response consistency
        try:
            response_time = float(proxy_data["response_time"].replace('s', ''))
            if response_time > 15:
                security_score -= 2  # Very slow - potential security risk
            elif response_time > 5:
                security_score -= 1  # Slow - might be logging
        except:
            pass
            
        # Determine security level
        if security_score >= 3:
            return "Very High"
        elif security_score >= 1:
            return "High"
        elif security_score >= -1:
            return "Medium"
        else:
            return "Low"
            
    def update_api_results(self, results):
        self.api_results_text.delete(1.0, tk.END)
        self.api_results_text.insert(tk.END, results)

if __name__ == "__main__":
    root = tk.Tk()
    app = ProxyTesterApp(root)
    root.mainloop()