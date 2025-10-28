import cv2
import numpy as np
from typing import Dict, List


class BlurDetector:

    def __init__(self, threshold: float = 100.0):

        self.threshold = threshold

    def calculate_blur_score(self, image: np.ndarray) -> float:

        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        laplacian = cv2.Laplacian(gray, cv2.CV_64F)

        variance = laplacian.var()

        return float(variance)

    def is_blurred(self, image: np.ndarray, threshold: float = None) -> bool:

        if threshold is None:
            threshold = self.threshold

        blur_score = self.calculate_blur_score(image)
        return blur_score < threshold

    def analyze_faces_blur(self, face_regions: List[np.ndarray],
                           face_data: List[Dict]) -> List[Dict]:

        updated_face_data = []

        for i, (face_region, face_info) in enumerate(zip(face_regions, face_data)):
            blur_score = self.calculate_blur_score(face_region)
            is_blurred = blur_score < self.threshold

            face_info_copy = face_info.copy()
            face_info_copy['blur_analysis'] = {
                'blur_score': round(blur_score, 2),
                'is_blurred': is_blurred,
                'threshold': self.threshold,
                'blur_level': self._get_blur_level(blur_score)
            }

            updated_face_data.append(face_info_copy)

        return updated_face_data

    def _get_blur_level(self, blur_score: float) -> str:
        if blur_score < 50:
            return 'severe'
        elif blur_score < 100:
            return 'moderate'
        elif blur_score < 200:
            return 'slight'
        else:
            return 'sharp'

    def get_overall_blur_stats(self, face_data: List[Dict]) -> Dict:
        total_faces = len(face_data)
        if total_faces == 0:
            return {
                'total_faces': 0,
                'blurred_faces': 0,
                'sharp_faces': 0,
                'average_blur_score': 0,
                'blur_percentage': 0
            }

        blurred_faces = sum(1 for face in face_data
                            if face.get('blur_analysis', {}).get('is_blurred', False))

        avg_score = np.mean([face.get('blur_analysis', {}).get('blur_score', 0)
                             for face in face_data])

        return {
            'total_faces': total_faces,
            'blurred_faces': blurred_faces,
            'sharp_faces': total_faces - blurred_faces,
            'average_blur_score': round(float(avg_score), 2),
            'blur_percentage': round((blurred_faces / total_faces) * 100, 2)
        }
