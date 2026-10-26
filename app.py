import cv2
import time
from flask import Flask, render_template, Response, request, redirect, url_for, flash, jsonify
from src.database import init_db, get_daily_attendance, add_student, get_registered_students
from src.face_recognizer import FaceRecognizer

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = 'super_secret_attendance_key'

init_db()
recognizer = FaceRecognizer()
camera = cv2.VideoCapture(0)

@app.route('/')
def index():
    """Main Attendance Terminal Dashboard."""
    logs = get_daily_attendance()
    return render_template('index.html', logs=logs)

@app.route('/students')
def students():
    """Registered Students Roster Page."""
    student_list = get_registered_students()
    return render_template('students.html', students=student_list)

@app.route('/enroll')
def enroll():
    """Dedicated Biometric Student Setup Page."""
    return render_template('enroll.html')

@app.route('/register_student_api', methods=['POST'])
def register_student_api():
    """API endpoint triggered when user initiates 50-second face scanning."""
    data = request.json
    enroll_no = data.get('enroll_no')
    name = data.get('name')
    course = data.get('course')
    year = data.get('year')

    if not (enroll_no and name and course and year):
        return jsonify({'status': 'error', 'message': 'Missing form fields'}), 400

    success = add_student(enroll_no, name, course, year)
    if not success:
        return jsonify({'status': 'error', 'message': f'Student {enroll_no} already registered'}), 400

    # Auto-capture 20 face crops over 50 seconds
    count = recognizer.capture_and_register(camera, enroll_no, max_samples=20)
    return jsonify({'status': 'success', 'message': f'Enrolled {name} with {count} face samples!'})

@app.route('/video_feed')
def video_feed():
    def generate_frames():
        while True:
            success, frame = camera.read()
            if not success:
                break
            processed_frame = recognizer.process_frame(frame)
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)