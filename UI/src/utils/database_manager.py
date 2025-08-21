import sqlite3
import datetime
import os

class DatabaseManager:
    def __init__(self, db_path='faults.db'):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faults (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                fault_type TEXT,
                image_index INTEGER,
                details TEXT,
                measurement REAL
            )
        ''')
        conn.commit()
        conn.close()
        
    def log_fault(self, fault_type, image_index, details, measurement=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO faults (timestamp, fault_type, image_index, details, measurement)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
              fault_type, image_index, details, measurement))
        conn.commit()
        conn.close()
        
    def get_all_faults(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM faults ORDER BY timestamp DESC')
        faults = cursor.fetchall()
        conn.close()
        return faults
        
    def get_faults_by_type(self, fault_type):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM faults WHERE fault_type = ? ORDER BY timestamp DESC', (fault_type,))
        faults = cursor.fetchall()
        conn.close()
        return faults
        
    def clear_faults(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM faults')
        conn.commit()
        conn.close() 