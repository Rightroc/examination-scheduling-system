import sqlite3
import csv
from datetime import datetime
import os

class ExamDatabase:
    def __init__(self, db_name='exam_system.db'):
        # Delete old database if exists to ensure clean schema
        if os.path.exists(db_name):
            os.remove(db_name)
            
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        print("🔧 Creating database tables...")
        
        # Drop tables if they exist to ensure clean start
        self.conn.execute("DROP TABLE IF EXISTS courses")
        self.conn.execute("DROP TABLE IF EXISTS rooms")
        self.conn.execute("DROP TABLE IF EXISTS schedules")
        self.conn.execute("DROP TABLE IF EXISTS system_log")
        
        tables = [
            '''CREATE TABLE courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                students INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL, 
                capacity INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_slot TEXT NOT NULL,
                room_name TEXT NOT NULL,
                course_code TEXT NOT NULL,
                student_count INTEGER NOT NULL,
                schedule_version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE system_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )'''
        ]
        
        for table in tables:
            try:
                self.conn.execute(table)
                print(f"✓ Created table: {table.split('(')[0].replace('CREATE TABLE ', '')}")
            except Exception as e:
                print(f"❌ Table creation error: {e}")
        
        self.conn.commit()
        self.log_action("SYSTEM_START", "Database initialized with clean schema")
        print("✅ Database schema created successfully")
    
    def log_action(self, action, details=""):
        try:
            self.conn.execute(
                "INSERT INTO system_log (action, details) VALUES (?, ?)",
                (action, details)
            )
            self.conn.commit()
        except Exception as e:
            print(f"Logging error: {e}")
    
    def save_courses(self, courses):
        try:
            self.conn.execute("DELETE FROM courses")
            for course in courses:
                self.conn.execute(
                    "INSERT INTO courses (code, students) VALUES (?, ?)",
                    (course['code'], course['students'])
                )
            self.conn.commit()
            self.log_action("COURSES_IMPORT", f"Imported {len(courses)} courses")
            print(f"✓ Saved {len(courses)} courses to database")
        except Exception as e:
            print(f"❌ Error saving courses: {e}")
    
    def save_rooms(self, rooms):
        try:
            self.conn.execute("DELETE FROM rooms")
            for room in rooms:
                self.conn.execute(
                    "INSERT INTO rooms (name, capacity) VALUES (?, ?)",
                    (room['name'], room['capacity'])
                )
            self.conn.commit()
            self.log_action("ROOMS_IMPORT", f"Imported {len(rooms)} rooms")
            print(f"✓ Saved {len(rooms)} rooms to database")
        except Exception as e:
            print(f"❌ Error saving rooms: {e}")
    
    def save_schedule(self, schedule, version=1):
        try:
            # Clear existing schedule for this version
            self.conn.execute("DELETE FROM schedules WHERE schedule_version = ?", (version,))
            
            schedule_data = []
            for time_slot, rooms in schedule.items():
                for room_name, exam in rooms.items():
                    if exam['course'] != 'FREE':
                        schedule_data.append((
                            time_slot, room_name, exam['course'], 
                            exam['students'], version
                        ))
            
            if schedule_data:
                self.conn.executemany(
                    "INSERT INTO schedules (time_slot, room_name, course_code, student_count, schedule_version) VALUES (?, ?, ?, ?, ?)",
                    schedule_data
                )
                self.conn.commit()
                self.log_action("SCHEDULE_GENERATED", f"Saved {len(schedule_data)} exam slots")
                print(f"✓ Saved {len(schedule_data)} exam slots to database")
            else:
                print("⚠️ No schedule data to save")
                
        except Exception as e:
            print(f"❌ Error saving schedule: {e}")
            raise e
    
    def get_latest_schedule(self):
        try:
            cursor = self.conn.execute(
                "SELECT time_slot, room_name, course_code, student_count FROM schedules WHERE schedule_version = 1"
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error fetching schedule: {e}")
            return []
    
    def get_system_stats(self):
        stats = {}
        try:
            stats['total_courses'] = self.conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
            stats['total_rooms'] = self.conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
            stats['total_scheduled'] = self.conn.execute("SELECT COUNT(*) FROM schedules").fetchone()[0]
            stats['last_action'] = self.conn.execute("SELECT action, timestamp FROM system_log ORDER BY timestamp DESC LIMIT 1").fetchone()
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            stats = {'total_courses': 0, 'total_rooms': 0, 'total_scheduled': 0, 'last_action': None}
        
        return stats

# Singleton instance
db = ExamDatabase()