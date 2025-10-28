import cv2
import numpy as np
from typing import List, Tuple, Dict
import os


class FaceDetector:
    def __init__(self):
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        if self.face_cascade.empty():
            raise RuntimeError("Failed to load Haar Cascade classifier")

    def detect_faces(self, image_path: str) -> Tuple[np.ndarray, List[Dict]]:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image from {image_path}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        face_data = []
        for i, (x, y, w, h) in enumerate(faces):
            face_info = {
                'face_id': i + 1,
                'bounding_box': {
                    'x': int(x),
                    'y': int(y),
                    'width': int(w),
                    'height': int(h)
                },
                'confidence': 1.0
            }
            face_data.append(face_info)

        return image, face_data

    def extract_face_regions(self, image: np.ndarray, face_data: List[Dict]) -> List[np.ndarray]:
        face_regions = []
        for face in face_data:
            bbox = face['bounding_box']
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            face_region = image[y:y + h, x:x + w]
            face_regions.append(face_region)

        return face_regions

    def draw_faces(self, image: np.ndarray, face_data: List[Dict],
                   color: Tuple[int, int, int] = (0, 255, 0),
                   thickness: int = 2) -> np.ndarray:
        result_image = image.copy()

        for face in face_data:
            bbox = face['bounding_box']
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
            cv2.rectangle(result_image, (x, y), (x + w, y + h), color, thickness)
            label = f"Face {face['face_id']}"
            cv2.putText(result_image, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        return result_image
