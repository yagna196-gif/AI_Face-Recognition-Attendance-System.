import sqlite3
import os
from datetime import datetime

# Path to local attendance.db file
DB_PATH = os.path.join(os.path.dirname(__file__), '../data/attendance.db')

def init_db():
    """Initialize SQLite database tables for student profiles and attendance logs."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table 1: Registered student profiles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enroll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            course TEXT NOT NULL,
            year TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table 2: Daily attendance scans
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enroll_no TEXT NOT NULL,
            name TEXT NOT NULL,
            course TEXT NOT NULL,
            year TEXT NOT NULL,
            scan_date DATE DEFAULT (DATE('now', 'localtime')),
            scan_time TIME DEFAULT (TIME('now', 'localtime')),
            status TEXT DEFAULT 'Present',
            FOREIGN KEY (enroll_no) REFERENCES users (enroll_no)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database schema initialized successfully at data/attendance.db")


def add_student(enroll_no, name, course, year):
    """Register a new student profile in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (enroll_no, name, course, year)
            VALUES (?, ?, ?, ?)
        ''', (enroll_no, name, course, year))
        conn.commit()
        print(f"Student {name} ({enroll_no}) registered successfully.")
    except sqlite3.IntegrityError:
        print(f"Student with Enrollment No {enroll_no} already exists.")
    finally:
        conn.close()


def mark_attendance(enroll_no):
    """Mark attendance for a student using their Enrollment No.
    Prevents duplicate entries on the same day.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if student exists in the system
    cursor.execute('SELECT name, course, year FROM users WHERE enroll_no = ?', (enroll_no,))
    student = cursor.fetchone()

    if not student:
        print(f"No student found with Enrollment No: {enroll_no}")
        conn.close()
        return False

    name, course, year = student
    today_date = datetime.now().strftime('%Y-%m-%d')

    # Check if student has already been marked present today
    cursor.execute('''
        SELECT id FROM attendance 
        WHERE enroll_no = ? AND scan_date = ?
    ''', (enroll_no, today_date))
    already_marked = cursor.fetchone()

    if already_marked:
        print(f"Attendance already recorded today for {name} ({enroll_no}).")
        conn.close()
        return False

    # Insert attendance entry with current date and time
    current_time = datetime.now().strftime('%H:%M:%S')
    cursor.execute('''
        INSERT INTO attendance (enroll_no, name, course, year, scan_date, scan_time, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Present')
    ''', (enroll_no, name, course, year, today_date, current_time))

    conn.commit()
    conn.close()
    print(f"Attendance marked for {name} at {current_time} on {today_date}")
    return True


def get_daily_attendance(date_str=None):
    """Fetch attendance records for a specific date (defaults to today)."""
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT enroll_no, name, course, year, scan_date, scan_time, status
        FROM attendance
        WHERE scan_date = ?
        ORDER BY scan_time DESC
    ''', (date_str,))

    records = cursor.fetchall()
    conn.close()
    return records


if __name__ == '__main__':
    # Initialize DB and test with sample data
    init_db()

    # Add sample students
    add_student('EN202601', 'Rahul Sharma', 'Computer Science', '3rd Year')
    add_student('EN202602', 'Ananya Patel', 'Information Technology', '3rd Year')

    # Test marking attendance
    mark_attendance('EN202601')

    # Print logs
    logs = get_daily_attendance()
    print("\nToday's Attendance Logs:")
    for log in logs:
        print(log)