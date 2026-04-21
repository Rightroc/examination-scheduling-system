import csv
from scheduler import ExamScheduler

def debug_csv_parsing():
    print("🔍 DEBUG: Checking CSV file parsing...")
    
    # First, check the raw CSV file
    print("\n1. READING RAW CSV FILE:")
    try:
        with open('invigilators.csv', 'r', encoding='utf-8') as file:
            content = file.read()
            print(f"File content:\n{content}")
            print(f"File length: {len(content)} characters")
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    # Second, check CSV parsing
    print("\n2. PARSING CSV WITH csv.DictReader:")
    try:
        with open('invigilators.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            print(f"Fieldnames: {reader.fieldnames}")
            
            rows = list(reader)
            print(f"Number of rows found: {len(rows)}")
            
            for i, row in enumerate(rows):
                print(f"Row {i+1}: {dict(row)}")
                
    except Exception as e:
        print(f"❌ Error parsing CSV: {e}")
        return
    
    # Third, test the scheduler loading
    print("\n3. TESTING SCHEDULER LOADING:")
    try:
        scheduler = ExamScheduler()
        scheduler.load_invigilators_from_csv('invigilators.csv')
        print(f"Invigilators loaded: {len(scheduler.invigilators)}")
        
        for inv in scheduler.invigilators:
            print(f"  - {inv['name']} ({inv['staff_id']}) - Dept: {inv['department']} - Max: {inv['max_sessions']}")
            
    except Exception as e:
        print(f"❌ Error in scheduler: {e}")

if __name__ == "__main__":
    debug_csv_parsing()