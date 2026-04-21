from scheduler import ExamScheduler
import csv

def system_diagnostic():
    print("🔧 RUNNING SYSTEM DIAGNOSTIC")
    print("=" * 50)
    
    scheduler = ExamScheduler()
    
    # Load your real data
    scheduler.load_courses_from_csv('courses.csv')
    scheduler.load_rooms_from_csv('rooms.csv') 
    scheduler.load_time_slots_from_csv('time_slots.csv')
    scheduler.load_students_from_csv('students.csv')
    
    # Capacity Analysis
    total_student_seats = sum(room['capacity'] for room in scheduler.rooms)
    total_exam_students = sum(course['students'] for course in scheduler.courses)
    total_time_slot_capacity = total_student_seats * len(scheduler.time_slots)
    
    print(f"📊 CAPACITY ANALYSIS:")
    print(f"   Total Rooms: {len(scheduler.rooms)}")
    print(f"   Total Time Slots: {len(scheduler.time_slots)}")
    print(f"   Total Student Capacity: {total_student_seats} per slot")
    print(f"   Total Exam Students: {total_exam_students}")
    print(f"   Total System Capacity: {total_time_slot_capacity}")
    print(f"   Utilization Required: {(total_exam_students/total_time_slot_capacity)*100:.1f}%")
    
    # Conflict Analysis
    scheduler.detect_conflicts()
    high_conflict_courses = [c for c in scheduler.courses if len(c['conflicts']) > 3]
    
    print(f"\n⚠️  CONFLICT ANALYSIS:")
    print(f"   High Conflict Courses (>3): {len(high_conflict_courses)}")
    for course in high_conflict_courses:
        print(f"   - {course['code']}: {len(course['conflicts'])} conflicts")
    
    # Generate actual schedule
    print(f"\n🎯 GENERATING SCHEDULE...")
    schedule = scheduler.generate_schedule()
    
    # Success Metrics
    scheduled = sum(1 for time_slot in schedule.values() 
                   for exam in time_slot.values() if exam['course'] != 'FREE')
    success_rate = (scheduled / len(scheduler.courses)) * 100
    
    print(f"\n✅ SCHEDULING SUCCESS: {success_rate:.1f}%")
    print(f"   Scheduled: {scheduled}/{len(scheduler.courses)} courses")
    
    return success_rate >= 85  # 85% minimum acceptable

if __name__ == "__main__":
    diagnostic_passed = system_diagnostic()
    if diagnostic_passed:
        print("\n🎉 SYSTEM READY FOR PRODUCTION")
    else:
        print("\n❌ SYSTEM NEEDS OPTIMIZATION")