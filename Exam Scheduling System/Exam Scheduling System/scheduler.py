import csv
import random
from typing import List, Dict, Tuple, Set
from database import db

class ExamScheduler:
    def __init__(self):
        self.courses = []
        self.rooms = []
        self.time_slots = []
        self.students = []
        self.invigilators = []
        
    def load_courses_from_csv(self, filename: str):
        """Load courses from CSV file"""
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.add_course(row['code'], int(row['students']))
            print(f"✓ Loaded {len(self.courses)} courses from {filename}")
        except FileNotFoundError:
            print(f"❌ Error: File {filename} not found")
        except Exception as e:
            print(f"❌ Error loading courses: {e}")
    
    def load_rooms_from_csv(self, filename: str):
        """Load rooms from CSV file"""
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.add_room(row['name'], int(row['capacity']))
            print(f"✓ Loaded {len(self.rooms)} rooms from {filename}")
        except FileNotFoundError:
            print(f"❌ Error: File {filename} not found")
        except Exception as e:
            print(f"❌ Error loading rooms: {e}")
    
    def load_time_slots_from_csv(self, filename: str):
        """Load time slots from CSV file"""
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.add_time_slot(row['time_slot'])
            print(f"✓ Loaded {len(self.time_slots)} time slots from {filename}")
        except FileNotFoundError:
            print(f"❌ Error: File {filename} not found")
        except Exception as e:
            print(f"❌ Error loading time slots: {e}")
    
    def load_students_from_csv(self, filename: str):
        """Load students from CSV file"""
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    courses = row['courses'].split('|')
                    self.add_student(row['student_id'], courses)
            print(f"✓ Loaded {len(self.students)} students from {filename}")
        except FileNotFoundError:
            print(f"❌ Error: File {filename} not found")
        except Exception as e:
            print(f"❌ Error loading students: {e}")
    
    def load_invigilators_from_csv(self, filename: str):
        """Load invigilators from CSV file"""
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.add_invigilator(
                        row['staff_id'],
                        row['name'],
                        row.get('department', ''),
                        int(row.get('max_sessions', 5))
                    )
            print(f"✓ Loaded {len(self.invigilators)} invigilators from {filename}")
        except FileNotFoundError:
            print(f"❌ Error: File {filename} not found")
        except Exception as e:
            print(f"❌ Error loading invigilators: {e}")
    
    def add_course(self, course_code: str, student_count: int):
        """Add a course to the system"""
        self.courses.append({
            'code': course_code,
            'students': student_count,
            'conflicts': set(),
            'level': self.get_course_level(course_code)
        })
    
    def add_room(self, room_name: str, capacity: int):
        """Add a room to the system"""
        self.rooms.append({
            'name': room_name,
            'capacity': capacity
        })
    
    def add_time_slot(self, time_slot: str):
        """Add a time slot"""
        self.time_slots.append(time_slot)
    
    def add_student(self, student_id: str, courses: List[str]):
        """Add a student and their courses"""
        self.students.append({
            'id': student_id,
            'courses': courses
        })
    
    def add_invigilator(self, staff_id: str, name: str, department: str = "", max_sessions: int = 5):
        """Add an invigilator to the system"""
        self.invigilators.append({
            'staff_id': staff_id,
            'name': name,
            'department': department,
            'max_sessions': max_sessions,
            'assigned_sessions': 0
        })
    
    def get_course_level(self, course_code: str) -> str:
        """Extract level from course code"""
        if course_code.startswith('CSC1') or course_code.startswith('GST1'):
            return '100L'
        elif course_code.startswith('CSC2') or course_code.startswith('MTH2'):
            return '200L'
        elif course_code.startswith('CSC3') or course_code.startswith('SE3'):
            return '300L'
        elif course_code.startswith('CSC4') or course_code.startswith('TECH4'):
            return '400L'
        elif course_code.startswith('PROJ') or course_code.startswith('CSC5'):
            return '500L'
        else:
            return 'MIXED'
    
    def find_course(self, course_code: str):
        """Find a course by code"""
        for course in self.courses:
            if course['code'] == course_code:
                return course
        return None
    
    def detect_conflicts(self):
        """Find which courses cannot be scheduled together"""
        print("\n🔍 Detecting course conflicts...")
        
        # Reset conflicts
        for course in self.courses:
            course['conflicts'] = set()
        
        conflict_count = 0
        for student in self.students:
            student_courses = student['courses']
            for i, course1_code in enumerate(student_courses):
                for course2_code in student_courses[i+1:]:
                    c1_obj = self.find_course(course1_code)
                    c2_obj = self.find_course(course2_code)
                    
                    if c1_obj and c2_obj:
                        if course2_code not in c1_obj['conflicts']:
                            c1_obj['conflicts'].add(course2_code)
                            conflict_count += 1
                        if course1_code not in c2_obj['conflicts']:
                            c2_obj['conflicts'].add(course1_code)
                            conflict_count += 1
        
        print(f"✓ Found {conflict_count} course conflicts")
        return conflict_count
    
    def calculate_invigilators_required(self, room_capacity: int) -> int:
        """Calculate invigilators needed based on room capacity"""
        if room_capacity <= 40:
            return 1
        elif room_capacity <= 60:
            return 2
        else:
            return 3
    
    def can_schedule_course(self, course, room, scheduled_courses, time_slot_scheduled, current_slot_schedule):
        """Check if a course can be scheduled in given constraints"""
        if (course['code'] in scheduled_courses or 
            course['code'] in time_slot_scheduled or
            course['students'] > room['capacity']):
            return False
        
        # Check conflicts with already scheduled courses in this time slot
        for scheduled_exam in current_slot_schedule.values():
            scheduled_course_code = scheduled_exam['course']
            if (scheduled_course_code in course['conflicts'] or 
                course['code'] in self.find_course(scheduled_course_code)['conflicts']):
                return False
        
        return True
    
    def generate_schedule(self) -> Dict:
        """Generate 3-week examination schedule"""
        print("\n🎯 Generating 3-Week Examination Schedule...")
        self.detect_conflicts()
        
        schedule = {}
        scheduled_courses = set()
        
        # Sort by student count (largest first)
        sorted_courses = sorted(self.courses, key=lambda x: x['students'], reverse=True)
        sorted_rooms = sorted(self.rooms, key=lambda x: x['capacity'], reverse=True)
        
        # Group courses by level for balanced distribution
        level_courses = {'100L': [], '200L': [], '300L': [], '400L': [], '500L': [], 'MIXED': []}
        for course in sorted_courses:
            level_courses[course['level']].append(course)
        
        # Schedule each time slot
        for time_slot in self.time_slots:
            schedule[time_slot] = {}
            time_slot_scheduled = set()
            available_rooms = sorted_rooms.copy()
            
            # Try to schedule courses from different levels in each slot
            for level in ['100L', '200L', '300L', '400L', '500L', 'MIXED']:
                if not available_rooms:
                    break
                    
                for course in level_courses[level]:
                    if not available_rooms:
                        break
                        
                    if self.can_schedule_course(course, available_rooms[0], scheduled_courses, time_slot_scheduled, schedule[time_slot]):
                        schedule[time_slot][available_rooms[0]['name']] = {
                            'course': course['code'],
                            'students': course['students'],
                            'room_capacity': available_rooms[0]['capacity'],
                            'level': course['level']
                        }
                        scheduled_courses.add(course['code'])
                        time_slot_scheduled.add(course['code'])
                        available_rooms.pop(0)
                        # Remove scheduled course from level list
                        level_courses[level].remove(course)
                        break
            
            # Fill any remaining rooms with available courses
            for room in available_rooms:
                course_scheduled = False
                for course in sorted_courses:
                    if course['code'] not in scheduled_courses and course['code'] not in time_slot_scheduled:
                        if self.can_schedule_course(course, room, scheduled_courses, time_slot_scheduled, schedule[time_slot]):
                            schedule[time_slot][room['name']] = {
                                'course': course['code'],
                                'students': course['students'],
                                'room_capacity': room['capacity'],
                                'level': course['level']
                            }
                            scheduled_courses.add(course['code'])
                            time_slot_scheduled.add(course['code'])
                            course_scheduled = True
                            break
                
                if not course_scheduled:
                    schedule[time_slot][room['name']] = {
                        'course': 'FREE', 
                        'students': 0, 
                        'room_capacity': room['capacity'],
                        'level': 'FREE'
                    }
        
        # Check results
        unscheduled = [course['code'] for course in self.courses if course['code'] not in scheduled_courses]
        if unscheduled:
            print(f"⚠️  Warning: Could not schedule {len(unscheduled)} courses: {unscheduled}")
        else:
            print(f"✅ Successfully scheduled all {len(self.courses)} courses across 3 weeks!")
            
        return schedule
    
    def assign_invigilators(self, schedule: Dict) -> Dict:
        """Assign invigilators to each exam session - FIXED VERSION"""
        print(f"\n👥 ASSIGNING INVIGILATORS: {len(self.invigilators)} staff available")
    
        if not self.invigilators:
            print("❌ CRITICAL: No invigilators loaded!")
            return {}
    
        # Show available invigilators
        print("Available invigilators:")
        for inv in self.invigilators:
            print(f"  - {inv['name']} ({inv['staff_id']}) - Max: {inv['max_sessions']} sessions")
        
        # Reset assignment counts
        for invigilator in self.invigilators:
            invigilator['assigned_sessions'] = 0
        
        invigilator_assignments = {}
        total_assignments = 0
        
        for time_slot, rooms in schedule.items():
            invigilator_assignments[time_slot] = {}
            
            for room_name, exam in rooms.items():
                if exam['course'] != 'FREE':
                    room = next((r for r in self.rooms if r['name'] == room_name), None)
                    if room:
                        invigilators_needed = self.calculate_invigilators_required(room['capacity'])
                        
                        # Find available invigilators (those who haven't reached max sessions)
                        available_invigilators = [
                            inv for inv in self.invigilators 
                            if inv['assigned_sessions'] < inv['max_sessions']
                        ]
                        
                        print(f"\n📋 {time_slot} - {room_name}:")
                        print(f"   Needed: {invigilators_needed} invigilators")
                        print(f"   Available: {len(available_invigilators)} staff members")
                        
                        if len(available_invigilators) >= invigilators_needed:
                            # Sort by least assigned first (fair distribution)
                            available_invigilators.sort(key=lambda x: x['assigned_sessions'])
                            
                            # Assign invigilators
                            assigned = available_invigilators[:invigilators_needed]
                            assigned_names = [f"{inv['name']} ({inv['staff_id']})" for inv in assigned]
                            
                            # Update assignment counts
                            for inv in assigned:
                                inv['assigned_sessions'] += 1
                                print(f"   ✅ Assigned: {inv['name']} (now has {inv['assigned_sessions']}/{inv['max_sessions']} sessions)")
                            
                            invigilator_assignments[time_slot][room_name] = assigned_names
                            total_assignments += invigilators_needed
                            
                        else:
                            print(f"   ⚠️ INSUFFICIENT STAFF: Needed {invigilators_needed}, but only {len(available_invigilators)} available")
                            # Assign whoever is available
                            assigned_names = [f"{inv['name']} ({inv['staff_id']})" for inv in available_invigilators]
                            invigilator_assignments[time_slot][room_name] = assigned_names
                            
                            for inv in available_invigilators:
                                inv['assigned_sessions'] += 1
        
        print(f"\n📊 INVIGILATOR ASSIGNMENT SUMMARY:")
        print(f"   Total assignments made: {total_assignments}")
        print(f"   Staff workload distribution:")
        for inv in self.invigilators:
            print(f"   - {inv['name']}: {inv['assigned_sessions']}/{inv['max_sessions']} sessions")
        
        return invigilator_assignments
    
    def get_student_schedule(self, student_id: str, schedule: Dict) -> List:
        """Get personalized schedule for a student"""
        student = next((s for s in self.students if s['id'] == student_id), None)
        if not student:
            return []
        
        student_schedule = []
        for time_slot, rooms in schedule.items():
            for room, exam in rooms.items():
                if exam['course'] in student['courses']:
                    student_schedule.append({
                        'time_slot': time_slot,
                        'room': room,
                        'course': exam['course'],
                        'level': exam['level']
                    })
        
        return student_schedule
    
    def validate_student_schedules(self, schedule: Dict):
        """Validate that all students have proper exam distribution"""
        print("\n📊 Validating student schedules...")
        
        for student in self.students:
            student_exams = self.get_student_schedule(student['id'], schedule)
            
            if len(student_exams) < 8:
                print(f"⚠️  Student {student['id']} has only {len(student_exams)} exams (minimum 8 expected)")
            elif len(student_exams) > 12:
                print(f"⚠️  Student {student['id']} has {len(student_exams)} exams (maximum 12 recommended)")
            
            # Check 24-hour gaps
            exam_times = [exam['time_slot'] for exam in student_exams]
            exam_times.sort()
            
            for i in range(len(exam_times) - 1):
                current = exam_times[i]
                next_exam = exam_times[i + 1]
                
                # Extract day and time for gap calculation
                current_day = current.split('_')[1]  # Monday, Tuesday, etc.
                next_day = next_exam.split('_')[1]
                
                if current_day == next_day:
                    print(f"❌ Student {student['id']} has exams on same day: {current} and {next_exam}")
    
    def export_schedule_to_csv(self, schedule: Dict, invigilator_assignments: Dict, filename: str):
        """Export the final schedule to CSV"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Week', 'Day', 'Time Slot', 'Room', 'Course', 'Level', 'Students', 'Room Capacity', 'Invigilators Required', 'Invigilators Assigned'])
                
                for time_slot, rooms in schedule.items():
                    week, day, time = time_slot.split('_')
                    for room_name, exam in rooms.items():
                        if exam['course'] != 'FREE':
                            invigilators_needed = self.calculate_invigilators_required(exam['room_capacity'])
                            
                            assigned_invigilators = []
                            if (invigilator_assignments and 
                                time_slot in invigilator_assignments and 
                                room_name in invigilator_assignments[time_slot]):
                                assigned_invigilators = invigilator_assignments[time_slot][room_name]
                            
                            invigilators_str = ", ".join(assigned_invigilators) if assigned_invigilators else "Not Assigned"
                            
                            writer.writerow([
                                week, day, time,
                                room_name,
                                exam['course'],
                                exam['level'],
                                exam['students'],
                                exam['room_capacity'],
                                invigilators_needed,
                                invigilators_str
                            ])
            print(f"✓ 3-Week schedule exported to {filename}")
        except Exception as e:
            print(f"❌ Error exporting schedule: {e}")

def test_3_week_scheduler():
    """Test the 3-week scheduling system"""
    print("🚀 Testing 3-Week Examination Scheduling System...")
    scheduler = ExamScheduler()
    
    # Load data
    scheduler.load_courses_from_csv('courses.csv')
    scheduler.load_rooms_from_csv('rooms.csv')
    scheduler.load_time_slots_from_csv('time_slots.csv')
    scheduler.load_students_from_csv('students.csv')
    scheduler.load_invigilators_from_csv('invigilators.csv')
    
    # Generate schedule
    schedule = scheduler.generate_schedule()
    invigilator_assignments = scheduler.assign_invigilators(schedule)
    
    # Validate
    scheduler.validate_student_schedules(schedule)
    
    # Save to database and export
    db.save_schedule(schedule, invigilator_assignments)
    scheduler.export_schedule_to_csv(schedule, invigilator_assignments, '3_week_exam_schedule.csv')
    
    return scheduler, schedule

if __name__ == "__main__":
    test_3_week_scheduler()