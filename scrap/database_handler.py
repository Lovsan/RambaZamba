#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime
from pathlib import Path

class DatabaseHandler:
    def __init__(self, db_path="systems.db"):
        self.db_path = db_path
        self.ensure_database_dir()
    
    def ensure_database_dir(self):
        """Ensure database directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def execute_query(self, query, params=(), fetch=False):
        """Execute a SQL query"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            
            if fetch:
                result = cursor.fetchall()
            else:
                conn.commit()
                result = None
                
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
            
        return result
    
    def export_to_json(self, filename="systems_export.json"):
        """Export database to JSON file"""
        data = {
            'systems': [],
            'commands': [],
            'export_time': datetime.now().isoformat()
        }
        
        # Export systems
        systems = self.execute_query('SELECT * FROM systems', fetch=True)
        for system in systems:
            data['systems'].append({
                'id': system[0],
                'name': system[1],
                'hostname': system[2],
                'port': system[3],
                'username': system[4],
                'auth_type': system[5],
                'os_type': system[8],
                'description': system[9],
                'tags': system[10],
                'last_seen': system[11],
                'status': system[12]
            })
        
        # Export commands
        commands = self.execute_query('SELECT * FROM commands', fetch=True)
        for command in commands:
            data['commands'].append({
                'id': command[0],
                'name': command[1],
                'command': command[2],
                'category': command[3],
                'description': command[4]
            })
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Database exported to {filename}")
    
    def import_from_json(self, filename="systems_import.json"):
        """Import data from JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Import systems
            for system in data.get('systems', []):
                self.execute_query('''
                    INSERT OR REPLACE INTO systems 
                    (id, name, hostname, port, username, auth_type, os_type, description, tags, last_seen, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    system['id'], system['name'], system['hostname'], system['port'],
                    system['username'], system['auth_type'], system['os_type'],
                    system['description'], system['tags'], system['last_seen'],
                    system['status']
                ))
            
            # Import commands
            for command in data.get('commands', []):
                self.execute_query('''
                    INSERT OR REPLACE INTO commands 
                    (id, name, command, category, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    command['id'], command['name'], command['command'],
                    command['category'], command['description']
                ))
            
            print(f"✅ Database imported from {filename}")
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
    
    def get_system_stats(self):
        """Get system statistics"""
        stats = {}
        
        # Total systems
        result = self.execute_query('SELECT COUNT(*) FROM systems', fetch=True)
        stats['total_systems'] = result[0][0] if result else 0
        
        # Online systems
        result = self.execute_query('SELECT COUNT(*) FROM systems WHERE status = "online"', fetch=True)
        stats['online_systems'] = result[0][0] if result else 0
        
        # Command count
        result = self.execute_query('SELECT COUNT(*) FROM commands', fetch=True)
        stats['total_commands'] = result[0][0] if result else 0
        
        # Recent activity
        result = self.execute_query('''
            SELECT COUNT(*) FROM command_results 
            WHERE timestamp > datetime("now", "-1 day")
        ''', fetch=True)
        stats['recent_commands'] = result[0][0] if result else 0
        
        return stats
    
    def backup_database(self, backup_dir="backups"):
        """Create a database backup"""
        Path(backup_dir).mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/systems_backup_{timestamp}.db"
        
        # Copy database file
        import shutil
        shutil.copy2(self.db_path, backup_file)
        
        print(f"✅ Database backed up to {backup_file}")
        return backup_file

if __name__ == "__main__":
    db = DatabaseHandler()
    stats = db.get_system_stats()
    print("📊 Database Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
