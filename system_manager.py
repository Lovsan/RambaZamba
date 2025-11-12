#!/usr/bin/env python3
import sqlite3
import json
import os
import paramiko
from datetime import datetime
import threading
import time
import subprocess
from pathlib import Path

class SystemManager:
    def __init__(self, db_path="systems.db"):
        self.db_path = db_path
        self.init_database()
        self.quick_commands = self.load_quick_commands()
        
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Systems table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                hostname TEXT NOT NULL,
                port INTEGER DEFAULT 22,
                username TEXT,
                auth_type TEXT DEFAULT 'password',
                password TEXT,
                key_file TEXT,
                os_type TEXT,
                description TEXT,
                tags TEXT,
                last_seen DATETIME,
                status TEXT DEFAULT 'unknown',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Commands table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                command TEXT NOT NULL,
                category TEXT,
                description TEXT,
                is_dangerous INTEGER DEFAULT 0
            )
        ''')
        
        # Command results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER,
                command_id INTEGER,
                output TEXT,
                exit_code INTEGER,
                execution_time REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (system_id) REFERENCES systems (id),
                FOREIGN KEY (command_id) REFERENCES commands (id)
            )
        ''')
        
        # Screenshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                system_id INTEGER,
                filename TEXT,
                path TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (system_id) REFERENCES systems (id)
            )
        ''')
        
        # Insert default quick commands
        default_commands = [
            ('System Info', 'uname -a && cat /etc/os-release', 'info', 'Basic system information'),
            ('Disk Usage', 'df -h', 'info', 'Disk space usage'),
            ('Memory Info', 'free -h', 'info', 'Memory usage'),
            ('Network Interfaces', 'ip addr show', 'network', 'Network interface configuration'),
            ('Running Processes', 'ps aux --sort=-%cpu | head -20', 'monitoring', 'Top processes by CPU'),
            ('Service Status', 'systemctl list-units --type=service --state=running', 'services', 'Running services'),
            ('Logged in Users', 'who', 'security', 'Currently logged in users'),
            ('Recent Logins', 'last -10', 'security', 'Recent user logins'),
            ('Open Ports', 'netstat -tulpn', 'security', 'Listening ports and services'),
            ('Package Updates', 'apt list --upgradable 2>/dev/null || yum check-update 2>/dev/null', 'maintenance', 'Available package updates')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO commands (name, command, category, description)
            VALUES (?, ?, ?, ?)
        ''', default_commands)
        
        conn.commit()
        conn.close()
        
    def load_quick_commands(self):
        """Load quick commands from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, command, category, description FROM commands ORDER BY category, name')
        commands = cursor.fetchall()
        conn.close()
        
        organized = {}
        for cmd_id, name, command, category, description in commands:
            if category not in organized:
                organized[category] = []
            organized[category].append({
                'id': cmd_id,
                'name': name,
                'command': command,
                'description': description
            })
        
        return organized
    
    def add_system(self, name, hostname, username, port=22, auth_type='password', 
                   password=None, key_file=None, os_type='linux', description='', tags=''):
        """Add a new system to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO systems (name, hostname, port, username, auth_type, password, key_file, os_type, description, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, hostname, port, username, auth_type, password, key_file, os_type, description, tags))
            
            conn.commit()
            print(f"✅ System '{name}' added successfully!")
            return True
        except sqlite3.IntegrityError:
            print(f"❌ System '{name}' already exists!")
            return False
        finally:
            conn.close()
    
    def list_systems(self, show_status=True):
        """List all systems with their status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if show_status:
            cursor.execute('''
                SELECT id, name, hostname, port, os_type, status, last_seen 
                FROM systems ORDER BY status, name
            ''')
        else:
            cursor.execute('''
                SELECT id, name, hostname, port, os_type, status, last_seen 
                FROM systems ORDER BY name
            ''')
        
        systems = cursor.fetchall()
        conn.close()
        
        if not systems:
            print("❌ No systems found in database.")
            return
        
        print("\n" + "="*80)
        print("SYSTEMS MANAGEMENT")
        print("="*80)
        print(f"{'ID':<3} {'Name':<15} {'Hostname':<20} {'Port':<6} {'OS':<8} {'Status':<10} {'Last Seen'}")
        print("-"*80)
        
        for system in systems:
            sys_id, name, hostname, port, os_type, status, last_seen = system
            
            # Status emojis
            status_emoji = "🟢" if status == 'online' else "🔴" if status == 'offline' else "⚫"
            
            # Format last seen
            if last_seen:
                last_seen = datetime.strptime(last_seen, '%Y-%m-%d %H:%M:%S').strftime('%m/%d %H:%M')
            else:
                last_seen = "Never"
            
            print(f"{sys_id:<3} {name:<15} {hostname:<20} {port:<6} {os_type:<8} {status_emoji} {status:<8} {last_seen}")
    
    def test_connection(self, system_id):
        """Test connection to a system"""
        system = self.get_system(system_id)
        if not system:
            print("❌ System not found!")
            return False
        
        print(f"🔍 Testing connection to {system[1]} ({system[2]})...")
        
        try:
            if system[2] == 'local':
                # Test local system
                result = subprocess.run(['echo', 'test'], capture_output=True, text=True)
                success = result.returncode == 0
            else:
                # Test SSH connection
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if system[5] == 'key':
                    ssh.connect(system[2], port=system[3], username=system[4], 
                               key_filename=system[7], timeout=10)
                else:
                    ssh.connect(system[2], port=system[3], username=system[4], 
                               password=system[6], timeout=10)
                
                ssh.close()
                success = True
            
            # Update status in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE systems SET status = ?, last_seen = ? WHERE id = ?
            ''', ('online' if success else 'offline', datetime.now(), system_id))
            conn.commit()
            conn.close()
            
            if success:
                print("✅ Connection successful!")
            else:
                print("❌ Connection failed!")
            
            return success
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            
            # Update status
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE systems SET status = ? WHERE id = ?
            ''', ('offline', system_id))
            conn.commit()
            conn.close()
            
            return False
    
    def get_system(self, system_id):
        """Get system details by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM systems WHERE id = ?', (system_id,))
        system = cursor.fetchone()
        conn.close()
        return system
    
    def run_command(self, system_id, command, save_result=True):
        """Run a command on a system"""
        system = self.get_system(system_id)
        if not system:
            print("❌ System not found!")
            return None
        
        print(f"🚀 Executing command on {system[1]}...")
        print(f"💻 Command: {command}")
        print("-" * 50)
        
        try:
            if system[2] == 'local':
                # Run locally
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                output = result.stdout + result.stderr
                exit_code = result.returncode
            else:
                # Run via SSH
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if system[5] == 'key':
                    ssh.connect(system[2], port=system[3], username=system[4], 
                               key_filename=system[7], timeout=30)
                else:
                    ssh.connect(system[2], port=system[3], username=system[4], 
                               password=system[6], timeout=30)
                
                stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
                output = stdout.read().decode() + stderr.read().decode()
                exit_code = stdout.channel.recv_exit_status()
                ssh.close()
            
            print(output)
            print("-" * 50)
            print(f"📊 Exit code: {exit_code}")
            
            if save_result:
                # Save to database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Get command ID if it exists in quick commands
                cursor.execute('SELECT id FROM commands WHERE command = ?', (command,))
                command_row = cursor.fetchone()
                command_id = command_row[0] if command_row else None
                
                cursor.execute('''
                    INSERT INTO command_results (system_id, command_id, output, exit_code, execution_time)
                    VALUES (?, ?, ?, ?, ?)
                ''', (system_id, command_id, output, exit_code, 0.0))
                
                conn.commit()
                conn.close()
            
            return output, exit_code
            
        except Exception as e:
            error_msg = f"❌ Command execution failed: {e}"
            print(error_msg)
            return error_msg, -1
    
    def run_quick_command(self, system_id, command_id):
        """Run a predefined quick command"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name, command FROM commands WHERE id = ?', (command_id,))
        command_data = cursor.fetchone()
        conn.close()
        
        if not command_data:
            print("❌ Quick command not found!")
            return
        
        command_name, command = command_data
        print(f"🎯 Running quick command: {command_name}")
        
        return self.run_command(system_id, command)
    
    def take_screenshot(self, system_id):
        """Take a screenshot on the remote system (if supported)"""
        system = self.get_system(system_id)
        if not system:
            print("❌ System not found!")
            return False
        
        print(f"📸 Attempting screenshot on {system[1]}...")
        
        # Different screenshot commands for different OS types
        screenshot_commands = {
            'linux': ['import -window root screenshot.png', 'scrot screenshot.png', 'gnome-screenshot -f screenshot.png'],
            'windows': ['screencapture -x screenshot.png'],
            'macos': ['screencapture -x screenshot.png']
        }
        
        os_type = system[8] or 'linux'
        commands = screenshot_commands.get(os_type, screenshot_commands['linux'])
        
        success = False
        for cmd in commands:
            output, exit_code = self.run_command(system_id, cmd, save_result=False)
            if exit_code == 0:
                success = True
                break
        
        if success:
            print("✅ Screenshot captured successfully!")
            # TODO: Add file transfer functionality here
        else:
            print("❌ Screenshot capture failed. System may not support this feature.")
        
        return success
    
    def show_quick_commands(self):
        """Display available quick commands"""
        print("\n" + "="*80)
        print("QUICK COMMANDS")
        print("="*80)
        
        for category, commands in self.quick_commands.items():
            print(f"\n📂 {category.upper()}:")
            print("-" * 40)
            for cmd in commands:
                print(f"  {cmd['id']:>2}. {cmd['name']:<25} - {cmd['description']}")
    
    def interactive_menu(self):
        """Main interactive menu"""
        while True:
            print("\n" + "="*80)
            print("🛠️  SYSTEM MANAGER - MAIN MENU")
            print("="*80)
            print("1. 📋 List Systems")
            print("2. ➕ Add New System")
            print("3. 🔍 Test System Connections")
            print("4. 🚀 Run Command")
            print("5. ⚡ Quick Commands")
            print("6. 📸 Take Screenshot")
            print("7. 📊 Show Command History")
            print("8. 🗑️  Delete System")
            print("9. 🚪 Exit")
            print("-" * 80)
            
            choice = input("Enter your choice (1-9): ").strip()
            
            if choice == '1':
                self.list_systems()
                
            elif choice == '2':
                self.add_system_interactive()
                
            elif choice == '3':
                self.list_systems(show_status=False)
                system_id = input("Enter system ID to test (or 'all' for all systems): ").strip()
                if system_id.lower() == 'all':
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('SELECT id FROM systems')
                    systems = cursor.fetchall()
                    conn.close()
                    
                    for sys_id in systems:
                        self.test_connection(sys_id[0])
                        time.sleep(1)  # Avoid overwhelming the network
                else:
                    try:
                        self.test_connection(int(system_id))
                    except ValueError:
                        print("❌ Invalid system ID!")
                        
            elif choice == '4':
                self.list_systems()
                try:
                    system_id = int(input("Enter system ID: "))
                    command = input("Enter command to execute: ")
                    self.run_command(system_id, command)
                except ValueError:
                    print("❌ Invalid system ID!")
                    
            elif choice == '5':
                self.list_systems()
                try:
                    system_id = int(input("Enter system ID: "))
                    self.show_quick_commands()
                    command_id = int(input("Enter quick command ID: "))
                    self.run_quick_command(system_id, command_id)
                except ValueError:
                    print("❌ Invalid input!")
                    
            elif choice == '6':
                self.list_systems()
                try:
                    system_id = int(input("Enter system ID: "))
                    self.take_screenshot(system_id)
                except ValueError:
                    print("❌ Invalid system ID!")
                    
            elif choice == '7':
                self.show_command_history()
                
            elif choice == '8':
                self.list_systems()
                try:
                    system_id = int(input("Enter system ID to delete: "))
                    self.delete_system(system_id)
                except ValueError:
                    print("❌ Invalid system ID!")
                    
            elif choice == '9':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice!")
    
    def add_system_interactive(self):
        """Interactive system addition"""
        print("\n➕ ADD NEW SYSTEM")
        print("-" * 40)
        
        name = input("System name: ").strip()
        hostname = input("Hostname/IP (use 'local' for current system): ").strip()
        username = input("Username: ").strip()
        port = input("Port (default 22): ").strip() or "22"
        auth_type = input("Auth type (password/key) [password]: ").strip() or "password"
        
        password = None
        key_file = None
        
        if auth_type == 'password':
            password = input("Password: ").strip()
        else:
            key_file = input("SSH key file path: ").strip()
        
        os_type = input("OS type (linux/windows/macos) [linux]: ").strip() or "linux"
        description = input("Description (optional): ").strip()
        tags = input("Tags (comma separated, optional): ").strip()
        
        try:
            self.add_system(name, hostname, username, int(port), auth_type, 
                           password, key_file, os_type, description, tags)
        except ValueError:
            print("❌ Invalid port number!")
    
    def delete_system(self, system_id):
        """Delete a system from database"""
        system = self.get_system(system_id)
        if not system:
            print("❌ System not found!")
            return
        
        confirm = input(f"⚠️  Are you sure you want to delete system '{system[1]}'? (y/N): ")
        if confirm.lower() == 'y':
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM systems WHERE id = ?', (system_id,))
            conn.commit()
            conn.close()
            print("✅ System deleted successfully!")
    
    def show_command_history(self):
        """Show command execution history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cr.timestamp, s.name, c.name, cr.exit_code
            FROM command_results cr
            LEFT JOIN systems s ON cr.system_id = s.id
            LEFT JOIN commands c ON cr.command_id = c.id
            ORDER BY cr.timestamp DESC
            LIMIT 20
        ''')
        history = cursor.fetchall()
        conn.close()
        
        if not history:
            print("📭 No command history found.")
            return
        
        print("\n" + "="*80)
        print("COMMAND HISTORY (Last 20)")
        print("="*80)
        print(f"{'Timestamp':<19} {'System':<15} {'Command':<20} {'Status'}")
        print("-" * 80)
        
        for timestamp, system_name, command_name, exit_code in history:
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%m/%d %H:%M:%S')
            system_name = system_name or 'Unknown'
            command_name = command_name or 'Custom Command'
            status = "✅ Success" if exit_code == 0 else "❌ Failed"
            
            print(f"{timestamp:<19} {system_name:<15} {command_name:<20} {status}")

if __name__ == "__main__":
    manager = SystemManager()
    manager.interactive_menu()
