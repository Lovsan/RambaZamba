#!/data/data/com.termux/files/usr/bin/env python3
import os
import sys
import requests
import json
import threading
import time
import csv
from datetime import datetime
import socket
import re
import urllib3
from urllib.parse import urlparse
import concurrent.futures
from bs4 import BeautifulSoup
import socks
import argparse

# Disable SSL warnings for better output
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TermuxProxyTester:
    def __init__(self):
        self.proxies = []
        self.testing = False
        self.colors = self.setup_colors()
        
    def setup_colors(self):
        """Setup terminal colors"""
        colors = {}
        colors['RED'] = '\033[91m'
        colors['GREEN'] = '\033[92m'
        colors['YELLOW'] = '\033[93m'
        colors['BLUE'] = '\033[94m'
        colors['MAGENTA'] = '\033[95m'
        colors['CYAN'] = '\033[96m'
        colors['WHITE'] = '\033[97m'
        colors['RESET'] = '\033[0m'
        colors['BOLD'] = '\033[1m'
        return colors

    def print_banner(self):
        """Print application banner"""
        banner = f"""
{self.colors['CYAN']}{self.colors['BOLD']}
╔══════════════════════════════════════════════╗
║           TERMUX PROXY TESTER PRO           ║
║              Advanced Edition               ║
╚══════════════════════════════════════════════╝
{self.colors['RESET']}
"""
        print(banner)

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')

    def print_menu(self):
        """Print main menu"""
        self.clear_screen()
        self.print_banner()
        
        menu = f"""
{self.colors['BOLD']}Main Menu:{self.colors['RESET']}

{self.colors['GREEN']}[1]{self.colors['RESET']} Add Proxy Manually
{self.colors['GREEN']}[2]{self.colors['RESET']} Load Proxies from File
{self.colors['GREEN']}[3]{self.colors['RESET']} Test All Proxies
{self.colors['GREEN']}[4]{self.colors['RESET']} Discover Proxies Online
{self.colors['GREEN']}[5]{self.colors['RESET']} Test with Home API
{self.colors['GREEN']}[6]{self.colors['RESET']} View Proxy List
{self.colors['GREEN']}[7]{self.colors['RESET']} Filter & Manage Proxies
{self.colors['GREEN']}[8]{self.colors['RESET']} Export Proxies
{self.colors['GREEN']}[9]{self.colors['RESET']} Settings
{self.colors['RED']}[0]{self.colors['RESET']} Exit

{self.colors['YELLOW']}Proxies Loaded: {len(self.proxies)}{self.colors['RESET']}
"""
        print(menu)

    def get_user_choice(self):
        """Get user menu choice"""
        try:
            choice = input(f"\n{self.colors['CYAN']}Select option [0-9]: {self.colors['RESET']}")
            return choice.strip()
        except KeyboardInterrupt:
            return '0'

    def add_proxy_manual(self):
        """Add proxy manually"""
        self.clear_screen()
        print(f"{self.colors['BOLD']}Add Proxy Manually{self.colors['RESET']}\n")
        
        while True:
            proxy_input = input(f"{self.colors['YELLOW']}Enter proxy (ip:port:type) or 'back': {self.colors['RESET']}")
            if proxy_input.lower() == 'back':
                return
                
            if not self.validate_proxy_format(proxy_input):
                print(f"{self.colors['RED']}Invalid format! Use: ip:port or ip:port:type{self.colors['RESET']}")
                continue
                
            self.add_proxy(proxy_input)
            print(f"{self.colors['GREEN']}Proxy added successfully!{self.colors['RESET']}")
            
            another = input(f"{self.colors['YELLOW']}Add another? (y/n): {self.colors['RESET']}")
            if another.lower() != 'y':
                break

    def validate_proxy_format(self, proxy_str):
        """Validate proxy format"""
        parts = proxy_str.split(':')
        if len(parts) < 2:
            return False
            
        ip, port = parts[0], parts[1]
        
        try:
            socket.inet_aton(ip)
            int(port)
            return True
        except (socket.error, ValueError):
            return False

    def add_proxy(self, proxy_str):
        """Add proxy to list"""
        parts = proxy_str.split(':')
        ip = parts[0]
        port = parts[1]
        proxy_type = parts[2] if len(parts) > 2 else "http"
        
        proxy_data = {
            "proxy": f"{ip}:{port}",
            "type": proxy_type,
            "status": "Not Tested",
            "response_time": "",
            "security": "Unknown",
            "country": "Unknown",
            "city": "Unknown",
            "isp": "Unknown",
            "last_tested": ""
        }
        
        # Check for duplicates
        if not any(p["proxy"] == proxy_data["proxy"] for p in self.proxies):
            self.proxies.append(proxy_data)

    def load_from_file(self):
        """Load proxies from file"""
        self.clear_screen()
        print(f"{self.colors['BOLD']}Load Proxies from File{self.colors['RESET']}\n")
        
        print(f"{self.colors['YELLOW']}Supported formats:{self.colors['RESET']}")
        print("• Text files (.txt) - one proxy per line")
        print("• JSON files (.json) - array of proxies")
        print("• CSV files (.csv) - with proxy column")
        print()
        
        file_path = input(f"{self.colors['CYAN']}Enter file path: {self.colors['RESET']}")
        
        if not os.path.exists(file_path):
            print(f"{self.colors['RED']}File not found!{self.colors['RESET']}")
            input(f"{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")
            return
            
        try:
            count_before = len(self.proxies)
            
            if file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'proxy' in item:
                                self.add_proxy(item['proxy'])
                            elif isinstance(item, str):
                                self.add_proxy(item)
            else:
                with open(file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.add_proxy(line)
            
            count_after = len(self.proxies)
            added = count_after - count_before
            
            print(f"{self.colors['GREEN']}Successfully added {added} proxies!{self.colors['RESET']}")
            
        except Exception as e:
            print(f"{self.colors['RED']}Error loading file: {str(e)}{self.colors['RESET']}")
            
        input(f"{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")

    def test_all_proxies(self):
        """Test all proxies"""
        if not self.proxies:
            print(f"{self.colors['RED']}No proxies to test!{self.colors['RESET']}")
            input(f"{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")
            return
            
        self.clear_screen()
        print(f"{self.colors['BOLD']}Testing All Proxies{self.colors['RESET']}\n")
        
        test_url = input(f"{self.colors['CYAN']}Test URL [http://httpbin.org/ip]: {self.colors['RESET']}") or "http://httpbin.org/ip"
        timeout = input(f"{self.colors['CYAN']}Timeout in seconds [10]: {self.colors['RESET']}") or "10"
        
        try:
            timeout = int(timeout)
        except ValueError:
            timeout = 10
            
        print(f"\n{self.colors['YELLOW']}Testing {len(self.proxies)} proxies...{self.colors['RESET']}")
        print(f"{self.colors['YELLOW']}This may take a while...{self.colors['RESET']}\n")
        
        # Use thread pool for faster testing
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for proxy_data in self.proxies:
                future = executor.submit(self.test_single_proxy, proxy_data, test_url, timeout)
                futures.append(future)
                
            # Wait for all to complete and show progress
            completed = 0
            total = len(futures)
            
            for future in concurrent.futures.as_completed(futures):
                completed += 1
                self.show_progress(completed, total)
                
        print(f"\n\n{self.colors['GREEN']}Testing completed!{self.colors['RESET']}")
        
        # Show summary
        working = len([p for p in self.proxies if p["status"] == "Working"])
        print(f"{self.colors['GREEN']}Working proxies: {working}/{len(self.proxies)}{self.colors['RESET']}")
        
        input(f"{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")

    def test_single_proxy(self, proxy_data, test_url, timeout):
        """Test a single proxy"""
        proxy_str = proxy_data["proxy"]
        proxy_type = proxy_data.get("type", "http")
        
        start_time = time.time()
        try:
            if proxy_type in ["socks4", "socks5"]:
                response = self.test_socks_proxy(proxy_str, proxy_type, test_url, timeout)
            else:
                proxies = {
                    "http": f"{proxy_type}://{proxy_str}",
                    "https": f"{proxy_type}://{proxy_str}"
                }
                response = requests.get(test_url, proxies=proxies, timeout=timeout, verify=False)
            
            if response.status_code == 200:
                response_time = round(time.time() - start_time, 2)
                proxy_data["status"] = "Working"
                proxy_data["response_time"] = f"{response_time}s"
                proxy_data["security"] = self.assess_security(response, proxy_data)
            else:
                proxy_data["status"] = f"Failed ({response.status_code})"
                proxy_data["response_time"] = ""
                proxy_data["security"] = "Failed"
                
        except Exception as e:
            proxy_data["status"] = "Failed"
            proxy_data["response_time"] = ""
            proxy_data["security"] = "Failed"
            
        proxy_data["last_tested"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
            response = requests.get(test_url, timeout=timeout, verify=False)
            return response
        finally:
            # Reset to default socket
            socks.set_default_proxy()

    def assess_security(self, response, proxy_data):
        """Assess proxy security"""
        security_score = 0
        headers = response.headers
        
        if 'X-Forwarded-For' in headers:
            security_score += 1
            
        if 'Via' in headers:
            security_score += 1
            
        try:
            response_time = float(proxy_data["response_time"].replace('s', ''))
            if response_time > 10:
                security_score -= 1
        except:
            pass
            
        if security_score >= 2:
            return "Low"
        elif security_score >= 0:
            return "Medium"
        else:
            return "High"

    def show_progress(self, current, total):
        """Show progress bar"""
        bar_length = 30
        percent = float(current) / total
        arrow = '=' * int(round(percent * bar_length) - 1) + '>'
        spaces = ' ' * (bar_length - len(arrow))
        
        sys.stdout.write(f'\r{self.colors['CYAN']}[{arrow + spaces}] {int(round(percent * 100))}% ({current}/{total}){self.colors['RESET']}')
        sys.stdout.flush()

    def discover_proxies(self):
        """Discover proxies online"""
        self.clear_screen()
        print(f"{self.colors['BOLD']}Discover Proxies Online{self.colors['RESET']}\n")
        
        print(f"{self.colors['YELLOW']}Available Sources:{self.colors['RESET']}")
        print(f"{self.colors['GREEN']}[1]{self.colors['RESET']} Free Proxy List")
        print(f"{self.colors['GREEN']}[2]{self.colors['RESET']} SSL Proxies")
        print(f"{self.colors['GREEN']}[3]{self.colors['RESET']} SOCKS Proxies")
        print(f"{self.colors['GREEN']}[4]{self.colors['RESET']} US Proxies")
        print(f"{self.colors['GREEN']}[5]{self.colors['RESET']} UK Proxies")
        print(f"{self.colors['RED']}[0]{self.colors['RESET']} Back")
        
        choice = input(f"\n{self.colors['CYAN']}Select source: {self.colors['RESET']}")
        
        sources = {
            '1': 'free_proxy_list',
            '2': 'ssl_proxies',
            '3': 'socks_proxies',
            '4': 'us_proxies',
            '5': 'uk_proxies'
        }
        
        if choice == '0':
            return
            
        if choice in sources:
            print(f"\n{self.colors['YELLOW']}Discovering proxies...{self.colors['RESET']}")
            discovered = self.scrape_proxies(sources[choice])
            
            if discovered:
                print(f"{self.colors['GREEN']}Found {len(discovered)} proxies!{self.colors['RESET']}")
                
                # Show first few proxies
                print(f"\n{self.colors['YELLOW']}First 10 proxies:{self.colors['RESET']}")
                for i, proxy in enumerate(discovered[:10]):
                    print(f"  {i+1}. {proxy['proxy']} ({proxy.get('type', 'http')})")
                    
                add_all = input(f"\n{self.colors['CYAN']}Add all to list? (y/n): {self.colors['RESET']}")
                if add_all.lower() == 'y':
                    count_before = len(self.proxies)
                    for proxy in discovered:
                        if not any(p["proxy"] == proxy["proxy"] for p in self.proxies):
                            self.proxies.append(proxy)
                    added = len(self.proxies) - count_before
                    print(f"{self.colors['GREEN']}Added {added} new proxies!{self.colors['RESET']}")
            else:
                print(f"{self.colors['RED']}No proxies found!{self.colors['RESET']}")
                
        input(f"\n{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")

    def scrape_proxies(self, source):
        """Scrape proxies from various sources"""
        try:
            if source == 'free_proxy_list':
                return self.scrape_free_proxy_list()
            elif source == 'ssl_proxies':
                return self.scrape_ssl_proxies()
            elif source == 'socks_proxies':
                return self.scrape_socks_proxies()
            else:
                return self.scrape_generic_proxies(source)
        except Exception as e:
            print(f"{self.colors['RED']}Error scraping: {str(e)}{self.colors['RESET']}")
            return []

    def scrape_free_proxy_list(self):
        """Scrape from free-proxy-list.net"""
        try:
            url = "https://free-proxy-list.net/"
            response = requests.get(url, timeout=10, verify=False)
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
                            "status": "Not Tested",
                            "response_time": "",
                            "security": "Unknown",
                            "country": cols[3].text.strip(),
                            "city": "Unknown",
                            "isp": "Unknown",
                            "last_tested": ""
                        })
            return proxies
        except Exception as e:
            print(f"{self.colors['RED']}Error scraping free proxy list: {e}{self.colors['RESET']}")
            return []

    def scrape_ssl_proxies(self):
        """Scrape SSL proxies"""
        try:
            url = "https://www.sslproxies.org/"
            response = requests.get(url, timeout=10, verify=False)
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
                            "status": "Not Tested",
                            "response_time": "",
                            "security": "Unknown",
                            "country": cols[3].text.strip() if len(cols) > 3 else "Unknown",
                            "city": "Unknown",
                            "isp": "Unknown",
                            "last_tested": ""
                        })
            return proxies
        except Exception as e:
            print(f"{self.colors['RED']}Error scraping SSL proxies: {e}{self.colors['RESET']}")
            return []

    def scrape_socks_proxies(self):
        """Scrape SOCKS proxies"""
        try:
            url = "https://www.socks-proxy.net/"
            response = requests.get(url, timeout=10, verify=False)
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
                                "status": "Not Tested",
                                "response_time": "",
                                "security": "Unknown",
                                "country": cols[2].text.strip(),
                                "city": "Unknown",
                                "isp": "Unknown",
                                "last_tested": ""
                            })
            return proxies
        except Exception as e:
            print(f"{self.colors['RED']}Error scraping SOCKS proxies: {e}{self.colors['RESET']}")
            return []

    def scrape_generic_proxies(self, source):
        """Generic proxy scraper"""
        # Add more sources as needed
        return []

    def test_home_api(self):
        """Test proxies with home API"""
        self.clear_screen()
        print(f"{self.colors['BOLD']}Test with Home API{self.colors['RESET']}\n")
        
        api_url = input(f"{self.colors['CYAN']}API URL: {self.colors['RESET']}")
        if not api_url:
            print(f"{self.colors['RED']}API URL is required!{self.colors['RESET']}")
            input(f"{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")
            return
            
        api_key = input(f"{self.colors['CYAN']}API Key (optional): {self.colors['RESET']}")
        timeout = input(f"{self.colors['CYAN']}Timeout [10]: {self.colors['RESET']}") or "10"
        
        try:
            timeout = int(timeout)
        except ValueError:
            timeout = 10
            
        working_proxies = []
        
        print(f"\n{self.colors['YELLOW']}Testing {len(self.proxies)} proxies with API...{self.colors['RESET']}")
        
        for i, proxy_data in enumerate(self.proxies, 1):
            self.show_progress(i, len(self.proxies))
            
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
                    response = requests.get(api_url, proxies=proxies, headers=headers, timeout=timeout, verify=False)
                
                if response.status_code == 200:
                    response_time = round(time.time() - start_time, 2)
                    working_proxies.append(proxy_data)
                    proxy_data["status"] = "Working (API)"
                    proxy_data["response_time"] = f"{response_time}s"
                    
            except Exception:
                pass
                
        print(f"\n\n{self.colors['GREEN']}API testing completed!{self.colors['RESET']}")
        print(f"{self.colors['GREEN']}Working with API: {len(working_proxies)}/{len(self.proxies)}{self.colors['RESET']}")
        
        input(f"{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")

    def view_proxy_list(self):
        """View proxy list"""
        self.clear_screen()
        print(f"{self.colors['BOLD']}Proxy List ({len(self.proxies)} proxies){self.colors['RESET']}\n")
        
        if not self.proxies:
            print(f"{self.colors['YELLOW']}No proxies in list.{self.colors['RESET']}")
            input(f"{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")
            return
            
        # Show summary
        working = len([p for p in self.proxies if "Working" in p["status"]])
        print(f"{self.colors['GREEN']}Working: {working}{self.colors['RESET']} | {self.colors['RED']}Failed: {len(self.proxies) - working}{self.colors['RESET']}\n")
        
        # Print table header
        print(f"{self.colors['BOLD']}{'#':<3} {'Proxy':<20} {'Type':<8} {'Status':<12} {'Time':<8} {'Security':<10}{self.colors['RESET']}")
        print(f"{self.colors['CYAN']}{'='*65}{self.colors['RESET']}")
        
        # Print proxies
        for i, proxy in enumerate(self.proxies[:50]):  # Show first 50
            status_color = self.colors['GREEN'] if "Working" in proxy["status"] else self.colors['RED']
            security_color = self.colors['GREEN'] if proxy["security"] in ["High", "Very High"] else self.colors['YELLOW'] if proxy["security"] == "Medium" else self.colors['RED']
            
            print(f"{i+1:<3} {proxy['proxy']:<20} {proxy.get('type', 'http'):<8} {status_color}{proxy['status'][:11]:<12}{self.colors['RESET']} {proxy['response_time']:<8} {security_color}{proxy.get('security', 'Unknown')[:9]:<10}{self.colors['RESET']}")
            
        if len(self.proxies) > 50:
            print(f"\n{self.colors['YELLOW']}... and {len(self.proxies) - 50} more proxies{self.colors['RESET']}")
            
        input(f"\n{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")

    def filter_manage_proxies(self):
        """Filter and manage proxies"""
        self.clear_screen()
        print(f"{self.colors['BOLD']}Filter & Manage Proxies{self.colors['RESET']}\n")
        
        print(f"{self.colors['GREEN']}[1]{self.colors['RESET']} Show Working Only")
        print(f"{self.colors['GREEN']}[2]{self.colors['RESET']} Show Fast Only (<2s)")
        print(f"{self.colors['GREEN']}[3]{self.colors['RESET']} Show Secure Only")
        print(f"{self.colors['GREEN']}[4]{self.colors['RESET']} Remove Failed Proxies")
        print(f"{self.colors['GREEN']}[5]{self.colors['RESET']} Remove All Proxies")
        print(f"{self.colors['RED']}[0]{self.colors['RESET']} Back")
        
        choice = input(f"\n{self.colors['CYAN']}Select option: {self.colors['RESET']}")
        
        if choice == '1':
            working = [p for p in self.proxies if "Working" in p["status"]]
            print(f"\n{self.colors['GREEN']}Found {len(working)} working proxies{self.colors['RESET']}")
            
        elif choice == '2':
            fast = []
            for p in self.proxies:
                try:
                    if p["response_time"] and float(p["response_time"].replace('s', '')) < 2:
                        fast.append(p)
                except:
                    pass
            print(f"\n{self.colors['GREEN']}Found {len(fast)} fast proxies{self.colors['RESET']}")
            
        elif choice == '3':
            secure = [p for p in self.proxies if p.get("security") in ["High", "Very High", "Medium"]]
            print(f"\n{self.colors['GREEN']}Found {len(secure)} secure proxies{self.colors['RESET']}")
            
        elif choice == '4':
            before = len(self.proxies)
            self.proxies = [p for p in self.proxies if "Working" in p["status"]]
            removed = before - len(self.proxies)
            print(f"\n{self.colors['GREEN']}Removed {removed} failed proxies{self.colors['RESET']}")
            
        elif choice == '5':
            confirm = input(f"{self.colors['RED']}Are you sure? (y/n): {self.colors['RESET']}")
            if confirm.lower() == 'y':
                self.proxies.clear()
                print(f"{self.colors['GREEN']}All proxies removed{self.colors['RESET']}")
                
        input(f"\n{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")

    def export_proxies(self):
        """Export proxies to file"""
        self.clear_screen()
        print(f"{self.colors['BOLD']}Export Proxies{self.colors['RESET']}\n")
        
        if not self.proxies:
            print(f"{self.colors['YELLOW']}No proxies to export.{self.colors['RESET']}")
            input(f"{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")
            return
            
        print(f"{self.colors['GREEN']}[1]{self.colors['RESET']} Export Working Proxies")
        print(f"{self.colors['GREEN']}[2]{self.colors['RESET']} Export All Proxies")
        print(f"{self.colors['RED']}[0]{self.colors['RESET']} Back")
        
        choice = input(f"\n{self.colors['CYAN']}Select option: {self.colors['RESET']}")
        
        if choice == '0':
            return
            
        if choice in ['1', '2']:
            proxies_to_export = self.proxies if choice == '2' else [p for p in self.proxies if "Working" in p["status"]]
            
            print(f"\n{self.colors['YELLOW']}Export Formats:{self.colors['RESET']}")
            print(f"{self.colors['GREEN']}[1]{self.colors['RESET']} Text file (.txt)")
            print(f"{self.colors['GREEN']}[2]{self.colors['RESET']} JSON file (.json)")
            print(f"{self.colors['GREEN']}[3]{self.colors['RESET']} CSV file (.csv)")
            
            format_choice = input(f"\n{self.colors['CYAN']}Select format: {self.colors['RESET']}")
            
            filename = input(f"{self.colors['CYAN']}Filename: {self.colors['RESET']}")
            if not filename:
                filename = f"proxies_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
            try:
                if format_choice == '1':
                    filename = filename if filename.endswith('.txt') else filename + '.txt'
                    with open(filename, 'w') as f:
                        for proxy in proxies_to_export:
                            f.write(f"{proxy['proxy']}:{proxy.get('type', 'http')}\n")
                            
                elif format_choice == '2':
                    filename = filename if filename.endswith('.json') else filename + '.json'
                    with open(filename, 'w') as f:
                        json.dump([{"proxy": p["proxy"], "type": p.get("type", "http")} for p in proxies_to_export], f, indent=2)
                        
                elif format_choice == '3':
                    filename = filename if filename.endswith('.csv') else filename + '.csv'
                    with open(filename, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(["Proxy", "Type", "Status", "Response Time", "Security", "Country", "City", "ISP", "Last Tested"])
                        for p in proxies_to_export:
                            writer.writerow([
                                p["proxy"], p.get("type", "http"), p["status"], p["response_time"], 
                                p.get("security", "Unknown"), p["country"], p["city"], p["isp"], p["last_tested"]
                            ])
                            
                print(f"{self.colors['GREEN']}Successfully exported {len(proxies_to_export)} proxies to {filename}{self.colors['RESET']}")
                
            except Exception as e:
                print(f"{self.colors['RED']}Error exporting: {str(e)}{self.colors['RESET']}")
                
        input(f"\n{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")

    def run(self):
        """Main application loop"""
        while True:
            self.print_menu()
            choice = self.get_user_choice()
            
            if choice == '0':
                print(f"\n{self.colors['GREEN']}Thank you for using Termux Proxy Tester!{self.colors['RESET']}")
                break
            elif choice == '1':
                self.add_proxy_manual()
            elif choice == '2':
                self.load_from_file()
            elif choice == '3':
                self.test_all_proxies()
            elif choice == '4':
                self.discover_proxies()
            elif choice == '5':
                self.test_home_api()
            elif choice == '6':
                self.view_proxy_list()
            elif choice == '7':
                self.filter_manage_proxies()
            elif choice == '8':
                self.export_proxies()
            elif choice == '9':
                self.show_settings()
            else:
                print(f"{self.colors['RED']}Invalid choice!{self.colors['RESET']}")
                input(f"{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")

    def show_settings(self):
        """Show settings menu"""
        self.clear_screen()
        print(f"{self.colors['BOLD']}Settings{self.colors['RESET']}\n")
        print(f"{self.colors['YELLOW']}Settings feature coming soon!{self.colors['RESET']}")
        input(f"{self.colors['YELLOW']}Press Enter to continue...{self.colors['RESET']}")

def main():
    """Main function"""
    # Check if running in Termux
    if not os.path.exists('/data/data/com.termux/files/usr/bin/'):
        print("This script is designed for Termux on Android.")
        print("Some features may not work properly in other environments.")
        continue_anyway = input("Continue anyway? (y/n): ")
        if continue_anyway.lower() != 'y':
            return
    
    # Create app instance and run
    app = TermuxProxyTester()
    app.run()

if __name__ == "__main__":
    main()
