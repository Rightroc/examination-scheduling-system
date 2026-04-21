from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import csv
from scheduler import ExamScheduler
from database import db

app = Flask(__name__)
app.secret_key = 'department_exam_system_2024'

scheduler = None
current_schedule = None
invigilator_assignments = None

@app.route('/')
def index():
    stats = db.get_system_stats()
    
    # FIX: Also get invigilators count from scheduler if available
    global scheduler
    if scheduler and hasattr(scheduler, 'invigilators'):
        stats['total_invigilators'] = len(scheduler.invigilators)
        print(f"🎯 DASHBOARD: Showing {len(scheduler.invigilators)} invigilators from scheduler")
    else:
        print("⚠️ DASHBOARD: No scheduler instance or invigilators loaded")
    
    # Always try to load and display schedule from database
    display_schedule = []
    try:
        db_schedule = db.get_latest_schedule()
        if db_schedule:
            for time_slot, room_name, course_code, student_count, invigilators_assigned in db_schedule:
                display_schedule.append({
                    'time_slot': time_slot,
                    'room': room_name,
                    'course': course_code,
                    'students': student_count,
                    'invigilators': invigilators_assigned.split('|') if invigilators_assigned else []
                })
    except:
        pass
    
    # Get invigilators list for display
    invigilators = []
    if scheduler and hasattr(scheduler, 'invigilators'):
        invigilators = scheduler.invigilators
        print(f"👥 DASHBOARD: Loaded {len(invigilators)} invigilators for display")
    
    return render_template('index.html', 
                         stats=stats, 
                         schedule=display_schedule, 
                         has_schedule=len(display_schedule) > 0,
                         invigilators=invigilators)

@app.route('/upload', methods=['POST'])
def upload_files():
    global scheduler
    
    try:
        scheduler = ExamScheduler()
        
        # Save uploaded files
        files = ['courses', 'rooms', 'time_slots', 'students', 'invigilators']
        uploaded_count = 0
        
        for file_type in files:
            file = request.files.get(f'{file_type}_file')
            if file and file.filename:
                filename = f'{file_type}.csv'
                file.save(filename)
                print(f"✓ Saved {filename}")
                uploaded_count += 1
                flash(f'✓ {file_type.replace("_", " ").title()} uploaded', 'success')
        
        print(f"Total files uploaded: {uploaded_count}")
        
        # Load data with detailed logging
        if os.path.exists('courses.csv'):
            scheduler.load_courses_from_csv('courses.csv')
            db.save_courses(scheduler.courses)
            print(f"Loaded {len(scheduler.courses)} courses")
        
        if os.path.exists('rooms.csv'):
            scheduler.load_rooms_from_csv('rooms.csv')
            db.save_rooms(scheduler.rooms)
            print(f"Loaded {len(scheduler.rooms)} rooms")
        
        if os.path.exists('time_slots.csv'):
            scheduler.load_time_slots_from_csv('time_slots.csv')
            print(f"Loaded {len(scheduler.time_slots)} time slots")
        
        if os.path.exists('students.csv'):
            scheduler.load_students_from_csv('students.csv')
            print(f"Loaded {len(scheduler.students)} students")
        
        # CRITICAL FIX: Load invigilators properly
        if os.path.exists('invigilators.csv'):
            print("🎯 Loading invigilators...")
            try:
                scheduler.load_invigilators_from_csv('invigilators.csv')
                print(f"✅ INVIGILATORS: Loaded {len(scheduler.invigilators)} staff members into scheduler")
                
                # DEBUG: Show what was loaded
                for i, inv in enumerate(scheduler.invigilators):
                    print(f"   {i+1}. {inv['name']} ({inv['staff_id']}) - Dept: {inv.get('department', 'N/A')}")
                
                # FORCE save to database and verify
                db.save_invigilators(scheduler.invigilators)
                
                # Verify database count
                db_stats = db.get_system_stats()
                print(f"✅ DATABASE CONFIRMED: {db_stats['total_invigilators']} invigilators in database")
                
            except Exception as e:
                print(f"❌ Failed to load invigilators: {e}")
                flash(f'Error loading invigilators: {str(e)}', 'error')
        else:
            print("❌ invigilators.csv not found!")
            flash('Invigilators file not found', 'error')            
        stats = db.get_system_stats()
        flash(f'✅ System loaded: {stats["total_courses"]} courses, {stats["total_rooms"]} rooms, {len(scheduler.invigilators)} invigilators', 'success')
        
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        flash(f'❌ Upload error: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/generate_schedule')
def generate_schedule():
    global scheduler, current_schedule, invigilator_assignments
    
    if not scheduler:
        flash('❌ Please upload data files first', 'error')
        return redirect(url_for('index'))
    
    try:
        current_schedule = scheduler.generate_schedule()
        invigilator_assignments = scheduler.assign_invigilators(current_schedule)
        db.save_schedule(current_schedule, invigilator_assignments)
        
        stats = db.get_system_stats()
        flash(f'🎓 Schedule generated! {stats["total_scheduled"]} exams scheduled with invigilator assignments', 'success')
        
        # Convert for display
        display_schedule = []
        for time_slot, rooms in current_schedule.items():
            for room, exam in rooms.items():
                if exam['course'] != 'FREE':
                    invigilators_list = []
                    if invigilator_assignments and time_slot in invigilator_assignments and room in invigilator_assignments[time_slot]:
                        invigilators_list = invigilator_assignments[time_slot][room]
                    
                    display_schedule.append({
                        'time_slot': time_slot,
                        'room': room,
                        'course': exam['course'],
                        'students': exam['students'],
                        'room_capacity': exam['room_capacity'],
                        'invigilators': invigilators_list
                    })
        
        invigilators = db.get_invigilators()
        stats = db.get_system_stats()
        return render_template('index.html', 
                             schedule=display_schedule, 
                             has_schedule=True, 
                             stats=stats,
                             invigilators=invigilators)
        
    except Exception as e:
        flash(f'❌ Schedule generation failed: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/view_schedule')
def view_schedule():
    global current_schedule
    
    # Try to load from database first
    display_schedule = []
    try:
        db_schedule = db.get_latest_schedule()
        if db_schedule:
            for time_slot, room_name, course_code, student_count, invigilators_assigned in db_schedule:
                display_schedule.append({
                    'time_slot': time_slot,
                    'room': room_name,
                    'course': course_code,
                    'students': student_count,
                    'invigilators': invigilators_assigned.split('|') if invigilators_assigned else []
                })
            flash('✅ Schedule loaded from database', 'success')
        else:
            flash('❌ No schedule found in database', 'error')
    except Exception as e:
        flash(f'❌ Error loading schedule: {str(e)}', 'error')
    
    invigilators = db.get_invigilators()
    stats = db.get_system_stats()
    return render_template('index.html', 
                         schedule=display_schedule, 
                         has_schedule=len(display_schedule) > 0, 
                         stats=stats,
                         invigilators=invigilators)

@app.route('/export_basic_schedule')
def export_basic_schedule():
    """Export basic schedule with only essential columns"""
    global current_schedule
    
    if not current_schedule:
        flash('❌ No schedule available to export', 'error')
        return redirect(url_for('index'))
    
    try:
        # Create basic CSV with only essential columns
        with open('basic_schedule.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write only the essential columns
            writer.writerow(['Week', 'Day', 'Time Slot', 'Room', 'Course'])
            
            for time_slot, rooms in current_schedule.items():
                # Parse the time slot into components
                parts = time_slot.split('_')
                if len(parts) == 3:
                    week, day, time = parts
                else:
                    week, day, time = 'Unknown', 'Unknown', time_slot
                
                for room_name, exam in rooms.items():
                    if exam['course'] != 'FREE':
                        writer.writerow([
                            week,
                            day,
                            time,
                            room_name,
                            exam['course']
                        ])
        
        print("✓ Basic schedule exported (Week, Day, Time, Room, Course only)")
        return send_file('basic_schedule.csv', as_attachment=True, download_name='basic_exam_schedule.csv')
        
    except Exception as e:
        flash(f'❌ Error exporting basic schedule: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/export_schedule')
def export_schedule():
    global current_schedule, invigilator_assignments
    
    if not current_schedule:
        flash('❌ No schedule to export', 'error')
        return redirect(url_for('index'))
    
    try:
        scheduler.export_schedule_to_csv(current_schedule, invigilator_assignments, 'final_schedule.csv')
        return send_file('final_schedule.csv', as_attachment=True, download_name='exam_schedule_with_invigilators.csv')
    except Exception as e:
        flash(f'❌ Export error: {str(e)}', 'error')
        return redirect(url_for('index'))
    
@app.route('/debug_invigilators')
def debug_invigilators():
    """Debug route to check invigilator status"""
    global scheduler
    
    debug_info = {
        'scheduler_exists': scheduler is not None,
        'invigilators_in_scheduler': len(scheduler.invigilators) if scheduler else 0,
        'invigilators_in_db': db.get_system_stats()['total_invigilators'],
        'files_exist': {
            'invigilators.csv': os.path.exists('invigilators.csv'),
            'courses.csv': os.path.exists('courses.csv'),
            'rooms.csv': os.path.exists('rooms.csv')
        }
    }
    
    if scheduler and scheduler.invigilators:
        debug_info['sample_invigilators'] = scheduler.invigilators[:3]
    
    return f"""
    <h1>Debug Information</h1>
    <pre>{debug_info}</pre>
    <a href="/">Back to main page</a>
    """    

@app.route('/export_invigilator_schedule')
def export_invigilator_schedule():
    """Export detailed invigilator assignments to CSV"""
    global invigilator_assignments, current_schedule
    
    if not invigilator_assignments:
        flash('❌ No invigilator assignments to export', 'error')
        return redirect(url_for('index'))
    
    try:
        with open('invigilator_assignments.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Time Slot', 'Room', 'Course', 'Students', 'Invigilators Required', 'Invigilators Assigned'])
            
            for time_slot, rooms in invigilator_assignments.items():
                for room_name, invigilators in rooms.items():
                    # Find course details for this room and time slot
                    course = "UNKNOWN"
                    students = 0
                    room_capacity = 0
                    if current_schedule and time_slot in current_schedule and room_name in current_schedule[time_slot]:
                        course = current_schedule[time_slot][room_name]['course']
                        students = current_schedule[time_slot][room_name]['students']
                        room_capacity = current_schedule[time_slot][room_name]['room_capacity']
                    
                    invigilators_needed = scheduler.calculate_invigilators_required(room_capacity)
                    invigilators_str = ", ".join(invigilators) if isinstance(invigilators, list) else str(invigilators)
                    
                    writer.writerow([
                        time_slot,
                        room_name,
                        course,
                        students,
                        invigilators_needed,
                        invigilators_str
                    ])
        
        return send_file('invigilator_assignments.csv', as_attachment=True, download_name='detailed_invigilator_assignments.csv')
    except Exception as e:
        flash(f'❌ Error exporting invigilator schedule: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/export_comprehensive')
def export_comprehensive():
    """Export comprehensive schedule with separate invigilator columns"""
    global current_schedule, invigilator_assignments
    
    if not current_schedule:
        flash('❌ No schedule to export', 'error')
        return redirect(url_for('index'))
    
    try:
        scheduler.export_comprehensive_schedule(current_schedule, invigilator_assignments, 'comprehensive_schedule.csv')
        return send_file('comprehensive_schedule.csv', as_attachment=True, download_name='comprehensive_exam_schedule.csv')
    except Exception as e:
        flash(f'❌ Export error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/student_lookup', methods=['POST'])
def student_lookup():
    global current_schedule, scheduler
    
    student_id = request.form.get('student_id')
    if not student_id:
        flash('❌ Enter student ID', 'error')
        return redirect(url_for('index'))
    
    try:
        personal_schedule = scheduler.get_student_schedule(student_id, current_schedule)
        stats = db.get_system_stats()
        
        # Also get full schedule for display
        display_schedule = []
        if current_schedule:
            for time_slot, rooms in current_schedule.items():
                for room, exam in rooms.items():
                    if exam['course'] != 'FREE':
                        invigilators_list = []
                        if invigilator_assignments and time_slot in invigilator_assignments and room in invigilator_assignments[time_slot]:
                            invigilators_list = invigilator_assignments[time_slot][room]
                        
                        display_schedule.append({
                            'time_slot': time_slot,
                            'room': room,
                            'course': exam['course'],
                            'students': exam['students'],
                            'room_capacity': exam['room_capacity'],
                            'invigilators': invigilators_list
                        })
        
        invigilators = db.get_invigilators()
        return render_template('index.html', 
                             personal_schedule=personal_schedule, 
                             student_id=student_id,
                             schedule=display_schedule,
                             has_schedule=True,
                             stats=stats,
                             invigilators=invigilators)
    except Exception as e:
        flash(f'❌ Student not found: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/clear_schedule')
def clear_schedule():
    global current_schedule, invigilator_assignments
    current_schedule = None
    invigilator_assignments = None
    flash('🗑️ Schedule cleared from memory. Data remains in database.', 'info')
    return redirect(url_for('index'))

@app.route('/clear_all_data')
def clear_all_data():
    """Manual route to clear all data"""
    try:
        db.clear_all_data()
        flash('✅ All data cleared successfully! Ready for new uploads.', 'success')
    except Exception as e:
        flash(f'❌ Error clearing data: {str(e)}', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("🚀 Software Engineering Exam System Starting...")
    print("🗃️  Database: exam_system.db")
    print("🌐 Web Interface: http://localhost:5000")
    print("👥 Invigilator management: ENABLED")
    print("✅ System READY for department use")
    
    app.run(debug=True, port=5000)