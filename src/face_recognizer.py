import os
import cv2
import cv2.data
import numpy as np
import tensorflow as tf
from src.database import mark_attendance

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/face_model.h5')

class FaceRecognizer:
    def __init__(self):
        self.model = None
        
        # Load Haar Cascade
        cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            print("Warning: Haar Cascade XML failed to load.")
            
        self.load_model()

    def load_model(self):
        """Load the TensorFlow model exported by Person A."""
        if os.path.exists(MODEL_PATH):
            self.model = tf.keras.models.load_model(MODEL_PATH)
            print("Face recognition model loaded successfully!")
        else:
            print(f"Warning: Model file not found at {MODEL_PATH}. Running in camera-only preview mode.")

    def process_frame(self, frame):
        """Detect faces in live frame and trigger attendance logging if recognized."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            face_roi = frame[y:y+h, x:x+w]
            
            if self.model is not None:
                resized = cv2.resize(face_roi, (128, 128))
                normalized = resized / 255.0
                input_tensor = np.expand_dims(normalized, axis=0)

                predictions = self.model.predict(input_tensor, verbose=0)
                class_idx = np.argmax(predictions[0])
                confidence = predictions[0][class_idx]

                if confidence > 0.80:
                    detected_enroll_no = f"EN20260{class_idx + 1}"
                    mark_attendance(detected_enroll_no)

                    label_text = f"{detected_enroll_no} ({int(confidence * 100)}%)"
                    cv2.putText(frame, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Face Detected", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame