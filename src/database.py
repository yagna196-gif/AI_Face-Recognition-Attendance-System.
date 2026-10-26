import sqlite3
import os
from datetime import datetime

# Define database and dataset folder paths relative to this script
DB_PATH = os.path.join(os.path.dirname(__file__), '../data/attendance.db')
DATASET_DIR = os.path.join(os.path.dirname(__file__), '../dataset')

def init_db():
    """Initialize database tables if they do not exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(DATASET_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            enroll_no TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            course TEXT NOT NULL,
            year TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create attendance logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enroll_no TEXT NOT NULL,
            name TEXT NOT NULL,
            course TEXT NOT NULL,
            year TEXT NOT NULL,
            scan_date DATE NOT NULL,
            scan_time TIME NOT NULL,
            status TEXT DEFAULT 'Present',
            FOREIGN KEY (enroll_no) REFERENCES users (enroll_no)
        )
    ''')

    conn.commit()
    conn.close()
    print("Database schema initialized successfully.")

def add_student(enroll_no, name, course, year):
    """Register student details in SQLite and prepare dataset directory."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (enroll_no, name, course, year)
            VALUES (?, ?, ?, ?)
        ''', (enroll_no, name, course, year))
        conn.commit()

        # Create student folder to save dataset photos
        student_folder = os.path.join(DATASET_DIR, enroll_no)
        os.makedirs(student_folder, exist_ok=True)
        print(f"Student {name} registered and folder created at {student_folder}")
        return True
    except sqlite3.IntegrityError:
        print(f"Student {enroll_no} already exists.")
        return False
    finally:
        conn.close()

def mark_attendance(enroll_no):
    """Log daily attendance once per student per date."""
    today_date = datetime.now().strftime('%Y-%m-%d')
    now_time = datetime.now().strftime('%H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch student details
    cursor.execute("SELECT name, course, year FROM users WHERE enroll_no = ?", (enroll_no,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return False

    name, course, year = student

    # Check if attendance is already marked today
    cursor.execute('''
        SELECT id FROM attendance WHERE enroll_no = ? AND scan_date = ?
    ''', (enroll_no, today_date))
    record = cursor.fetchone()

    if not record:
        cursor.execute('''
            INSERT INTO attendance (enroll_no, name, course, year, scan_date, scan_time, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Present')
        ''', (enroll_no, name, course, year, today_date, now_time))
        conn.commit()
        print(f"Attendance marked for {name} ({enroll_no}) at {now_time}")

    conn.close()
    return True

def get_daily_attendance():
    """Retrieve today's attendance logs for dashboard table."""
    today_date = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT enroll_no, name, course, year, scan_date, scan_time, status
        FROM attendance
        WHERE scan_date = ?
        ORDER BY id DESC
    ''', (today_date,))
    logs = cursor.fetchall()

    conn.close()
    return logs

def get_registered_students():
    """Fetch all registered students from SQLite for Roster Dashboard."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT enroll_no, name, course, year, created_at 
        FROM users 
        ORDER BY created_at DESC
    ''')
    students = cursor.fetchall()
    conn.close()
    return students