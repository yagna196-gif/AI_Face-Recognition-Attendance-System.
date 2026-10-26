import os
import cv2
import cv2.data
import numpy as np
import pickle
import tensorflow as tf
from src.database import mark_attendance

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/face_model.h5')
EMBEDDINGS_PATH = os.path.join(os.path.dirname(__file__), '../data/embeddings.pkl')

class FaceRecognizer:
    def __init__(self):
        self.model = None
        self.known_embeddings = {}
        
        # Load Haar Cascade Classifier
        cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        # Mode 1: Load pre-trained .h5 model if present
        self.load_pretrained_model()
        
        # Mode 2: Load dynamic local embeddings if present
        self.load_embeddings()

    def load_pretrained_model(self):
        """Mode 1: Load offline TensorFlow model exported by Person A."""
        if os.path.exists(MODEL_PATH):
            try:
                self.model = tf.keras.models.load_model(MODEL_PATH)
                print("Mode 1 Active: Pre-trained TensorFlow model loaded successfully!")
            except Exception as e:
                print(f"Warning: Could not load {MODEL_PATH}: {e}")
        else:
            print("Mode 1 Status: No face_model.h5 found. Ready for dynamic website enrollment.")

    def load_embeddings(self):
        """Mode 2: Load vector embeddings generated from website enrollments."""
        if os.path.exists(EMBEDDINGS_PATH):
            with open(EMBEDDINGS_PATH, 'rb') as f:
                self.known_embeddings = pickle.load(f)
            print(f"Mode 2 Active: Loaded dynamic embeddings for {len(self.known_embeddings)} students.")

    def capture_and_register(self, camera, enroll_no, max_samples=20):
        """Mode 2: Auto-capture 20 cropped face samples from webcam and store embeddings."""
        save_path = os.path.join(os.path.dirname(__file__), f'../dataset/{enroll_no}')
        os.makedirs(save_path, exist_ok=True)

        count = 0
        samples = []

        while count < max_samples:
            success, frame = camera.read()
            if not success:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

            for (x, y, w, h) in faces:
                count += 1
                face_roi = cv2.resize(gray[y:y+h, x:x+w], (100, 100))
                
                # Save cropped image file to dataset folder
                img_name = os.path.join(save_path, f"{enroll_no}_{count}.jpg")
                cv2.imwrite(img_name, face_roi)
                
                samples.append(face_roi.flatten())
                cv2.waitKey(80)

        # Save averaged feature embedding for instant website-added recognition
        if samples:
            avg_embedding = np.mean(samples, axis=0)
            self.known_embeddings[enroll_no] = avg_embedding
            
            os.makedirs(os.path.dirname(EMBEDDINGS_PATH), exist_ok=True)
            with open(EMBEDDINGS_PATH, 'wb') as f:
                pickle.dump(self.known_embeddings, f)

        return count

    def process_frame(self, frame):
        """Processes live camera feed using either Mode 1 (.h5 model) or Mode 2 (embeddings)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            face_roi = frame[y:y+h, x:x+w]

            matched_enroll = None
            confidence_str = ""

            # Check Mode 1 (.h5 Model)
            if self.model is not None:
                resized = cv2.resize(face_roi, (128, 128)) / 255.0
                tensor = np.expand_dims(resized, axis=0)
                preds = self.model.predict(tensor, verbose=0)
                idx = np.argmax(preds[0])
                conf = preds[0][idx]
                if conf > 0.80:
                    matched_enroll = f"EN20260{idx + 1}"
                    confidence_str = f"{int(conf * 100)}%"

            # Check Mode 2 (Dynamic Website Embeddings) if Mode 1 didn't match
            if not matched_enroll and self.known_embeddings:
                current_feat = cv2.resize(gray[y:y+h, x:x+w], (100, 100)).flatten()
                best_dist = float('inf')
                best_match = None

                for enroll_no, saved_feat in self.known_embeddings.items():
                    dist = np.linalg.norm(current_feat - saved_feat)
                    if dist < best_dist:
                        best_dist = dist
                        best_match = enroll_no

                if best_dist < 4000:  # Matching distance threshold
                    matched_enroll = best_match
                    confidence_str = "Website Reg"

            # Log attendance and draw labels
            if matched_enroll:
                mark_attendance(matched_enroll)
                cv2.putText(frame, f"{matched_enroll} ({confidence_str})", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Face Detected", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame