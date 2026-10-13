import cv2
from flask import Flask, render_template, Response
from src.database import init_db, get_daily_attendance
from src.face_recognizer import FaceRecognizer

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# Initialize database
init_db()

# Initialize Face Recognizer module
recognizer = FaceRecognizer()

# OpenCV Video Capture
camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Pass frame through face detection & recognition pipeline
            processed_frame = recognizer.process_frame(frame)

            # Encode frame into JPEG
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    logs = get_daily_attendance()
    return render_template('index.html', logs=logs)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)