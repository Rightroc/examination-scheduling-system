import sqlite3
import csv
from datetime import datetime
import os
import time

class ExamDatabase:
    def __init__(self, db_name='exam_system.db'):
        self.db_name = db_name
        self.conn = None
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize database with retry logic for Flask restart"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Try to delete old database if it exists
                if os.path.exists(self.db_name):
                    print("🗑️  Deleting old database for fresh start...")
                    os.remove(self.db_name)
                
                # Create new connection
                self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
                self.create_tables()
                return  # Success!
                
            except PermissionError:
                if attempt < max_retries - 1:
                    print(f"⚠️  Database busy, retrying in {retry_delay} second...")
                    time.sleep(retry_delay)
                else:
                    print("⚠️  Could not delete old database, using existing...")
                    self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
                    self.create_tables()
                    return
            except Exception as e:
                print(f"❌ Database initialization error: {e}")
                raise
    
    def create_tables(self):
        print("🔧 Creating/updating database tables...")
        
        tables = [
            '''CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                students INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL, 
                capacity INTEGER NOT NULL,
                invigilators_required INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS invigilators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                department TEXT,
                max_sessions INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_slot TEXT NOT NULL,
                room_name TEXT NOT NULL,
                course_code TEXT NOT NULL,
                student_count INTEGER NOT NULL,
                invigilators_assigned TEXT,
                schedule_version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS system_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )'''
        ]
        
        for table in tables:
            try:
                self.conn.execute(table)
                table_name = table.split('(')[0].replace('CREATE TABLE IF NOT EXISTS ', '')
                print(f"✓ Table ready: {table_name}")
            except Exception as e:
                print(f"❌ Table creation error: {e}")
        
        self.conn.commit()
        self.log_action("SYSTEM_START", "Database initialized successfully")
        print("✅ Database ready for use!")
    
    def clear_all_data(self):
        """Manual method to clear all data for fresh start"""
        try:
            tables = ['courses', 'rooms', 'invigilators', 'schedules', 'system_log']
            for table in tables:
                self.conn.execute(f"DELETE FROM {table}")
            self.conn.commit()
            self.log_action("DATA_CLEARED", "All data cleared manually")
            print("✅ All data cleared manually")
            return True
        except Exception as e:
            print(f"❌ Error clearing data: {e}")
            return False
    
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
                # Calculate invigilators required based on capacity
                capacity = room['capacity']
                if capacity <= 30:
                    invigilators = 1
                elif capacity <= 60:
                    invigilators = 2
                elif capacity <= 100:
                    invigilators = 3
                else:
                    invigilators = 4
                
                self.conn.execute(
                    "INSERT INTO rooms (name, capacity, invigilators_required) VALUES (?, ?, ?)",
                    (room['name'], room['capacity'], invigilators)
                )
            self.conn.commit()
            self.log_action("ROOMS_IMPORT", f"Imported {len(rooms)} rooms")
            print(f"✓ Saved {len(rooms)} rooms to database")
        except Exception as e:
            print(f"❌ Error saving rooms: {e}")
    
    def save_invigilators(self, invigilators):
        """Save invigilators to database - FIXED VERSION"""
        try:
            # Clear existing invigilators
            self.conn.execute("DELETE FROM invigilators")
        
            for invigilator in invigilators:
                self.conn.execute(
                    "INSERT INTO invigilators (staff_id, name, department, max_sessions) VALUES (?, ?, ?, ?)",
                    (invigilator['staff_id'], invigilator['name'], invigilator.get('department', ''), invigilator.get('max_sessions', 5))
                )
            self.conn.commit()
            self.log_action("INVIGILATORS_IMPORT", f"Imported {len(invigilators)} invigilators")
            print(f"✓ Saved {len(invigilators)} invigilators to database")
        
            # VERIFY they were saved
            count = self.conn.execute("SELECT COUNT(*) FROM invigilators").fetchone()[0]
            print(f"✅ DATABASE CONFIRMATION: {count} invigilators in database")
        
        except Exception as e:
            print(f"❌ Error saving invigilators: {e}")
    
    def get_invigilators(self):
        """Get all invigilators from database"""
        try:
            cursor = self.conn.execute("SELECT staff_id, name, department, max_sessions FROM invigilators")
            return [{'staff_id': row[0], 'name': row[1], 'department': row[2], 'max_sessions': row[3]} for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error fetching invigilators: {e}")
            return []
    
    def get_rooms_with_invigilators(self):
        """Get rooms with their invigilator requirements"""
        try:
            cursor = self.conn.execute("SELECT name, capacity, invigilators_required FROM rooms")
            return [{'name': row[0], 'capacity': row[1], 'invigilators_required': row[2]} for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error fetching rooms: {e}")
            return []
    
    def save_schedule(self, schedule, invigilator_assignments=None, version=1):
        try:
            # Clear existing schedule for this version
            self.conn.execute("DELETE FROM schedules WHERE schedule_version = ?", (version,))
            
            schedule_data = []
            for time_slot, rooms in schedule.items():
                for room_name, exam in rooms.items():
                    if exam['course'] != 'FREE':
                        # Get invigilators for this exam slot
                        invigilators_str = ""
                        if invigilator_assignments and time_slot in invigilator_assignments and room_name in invigilator_assignments[time_slot]:
                            invigilators_str = "|".join(invigilator_assignments[time_slot][room_name])
                        
                        schedule_data.append((
                            time_slot, room_name, exam['course'], 
                            exam['students'], invigilators_str, version
                        ))
            
            if schedule_data:
                self.conn.executemany(
                    "INSERT INTO schedules (time_slot, room_name, course_code, student_count, invigilators_assigned, schedule_version) VALUES (?, ?, ?, ?, ?, ?)",
                    schedule_data
                )
                self.conn.commit()
                self.log_action("SCHEDULE_GENERATED", f"Saved {len(schedule_data)} exam slots with invigilators")
                print(f"✓ Saved {len(schedule_data)} exam slots with invigilator assignments")
            else:
                print("⚠️ No schedule data to save")
                
        except Exception as e:
            print(f"❌ Error saving schedule: {e}")
            raise e
    
    def get_latest_schedule(self):
        try:
            cursor = self.conn.execute(
                "SELECT time_slot, room_name, course_code, student_count, invigilators_assigned FROM schedules WHERE schedule_version = 1 ORDER BY time_slot, room_name"
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
            stats['total_invigilators'] = self.conn.execute("SELECT COUNT(*) FROM invigilators").fetchone()[0]
            stats['total_scheduled'] = self.conn.execute("SELECT COUNT(*) FROM schedules").fetchone()[0]
            stats['last_action'] = self.conn.execute("SELECT action, timestamp FROM system_log ORDER BY timestamp DESC LIMIT 1").fetchone()
            
            print(f"📊 DATABASE STATS: {stats['total_courses']} courses, {stats['total_rooms']} rooms, {stats['total_invigilators']} invigilators in DB")
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            stats = {'total_courses': 0, 'total_rooms': 0, 'total_invigilators': 0, 'total_scheduled': 0, 'last_action': None}
        
        return stats

# Singleton instance
db = ExamDatabase()