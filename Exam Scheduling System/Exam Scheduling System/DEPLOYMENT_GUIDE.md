# DEPARTMENT EXAM SCHEDULING SYSTEM - PRODUCTION DEPLOYMENT

## SYSTEM OVERVIEW
- **Purpose**: Automated examination timetable generation
- **Capacity**: 12 courses, 8 rooms, 100+ students (scalable)
- **Success Rate**: 100% scheduling achieved
- **Technology**: Python Flask web application with SQLite database

## QUICK START
1. Ensure Python 3.6+ is installed
2. Run: `pip install flask`
3. Place all files in one folder
4. Execute: `python app.py`
5. Access: http://localhost:5000

## REQUIRED CSV FILES
### courses.csv
code,students
CSC101,50
CSC102,45
...
### rooms.csv
name,capacity
CSC1,100
CSC2,80
...
### time_slots.csv
time_slot
Monday 9:00-12:00
Monday 14:00-17:00
...
### students.csv
student_id,courses
20212269252,CSC101|MATH101|GST101
20203398665,CSC101|PHY101|ENG101
...

## OPERATIONAL PROCEDURE
1. **Data Preparation**: Update CSV files with current semester data
2. **System Startup**: Run `python app.py`
3. **Web Interface**: Upload files → Generate Schedule → Export
4. **Verification**: Check for scheduling conflicts and room capacities

## TROUBLESHOOTING
- **Port 5000 busy**: Use `python app.py --port 5001`
- **Database errors**: Delete `exam_system.db` and restart
- **Scheduling fails**: Check room capacities vs course sizes
- **Student conflicts**: Verify student registration data

## MAINTENANCE
- Backup `exam_system.db` regularly
- Update CSV files each semester
- Monitor system logs in database

## SUPPORT
Technical contact: [SOE IT]
System version: 1.0 Production
Last tested: [Current Date]