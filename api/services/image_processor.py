import cv2
import numpy as np
from typing import Tuple, List, Dict
import os
from PIL import Image


class ImageProcessor:

    def __init__(self):
        pass

    def sharpen_image(self, image: np.ndarray, strength: float = 1.5) -> np.ndarray:

        blurred = cv2.GaussianBlur(image, (0, 0), 3)

        sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)

        return sharpened

    def deblur_wiener(self, image: np.ndarray) -> np.ndarray:

        img_float = image.astype(np.float64) / 255.0

        deblurred = cv2.bilateralFilter(image, 9, 75, 75)

        deblurred = self.sharpen_image(deblurred, strength=2.0)

        return deblurred

    def enhance_face_region(self, face_region: np.ndarray, is_blurred: bool) -> np.ndarray:

        if not is_blurred:
            return face_region

        enhanced = self.deblur_wiener(face_region)

        lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        return enhanced

    def process_full_image(self, image: np.ndarray, face_data: List[Dict]) -> np.ndarray:

        result_image = image.copy()

        for face in face_data:
            bbox = face['bounding_box']
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']

            is_blurred = face.get('blur_analysis', {}).get('is_blurred', False)

            if is_blurred:
                face_region = image[y:y + h, x:x + w]

                enhanced_face = self.enhance_face_region(face_region, True)

                result_image[y:y + h, x:x + w] = enhanced_face

        return result_image

    def add_annotations(self, image: np.ndarray, face_data: List[Dict]) -> np.ndarray:

        annotated = image.copy()

        for face in face_data:
            bbox = face['bounding_box']
            x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']

            is_blurred = face.get('blur_analysis', {}).get('is_blurred', False)
            blur_score = face.get('blur_analysis', {}).get('blur_score', 0)

            color = (0, 0, 255) if is_blurred else (0, 255, 0)  # Red if blurred, green if sharp

            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

            status = "BLURRED" if is_blurred else "SHARP"
            label = f"Face {face['face_id']}: {status}"
            score_label = f"Score: {blur_score:.1f}"

            cv2.putText(annotated, label, (x, y - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            cv2.putText(annotated, score_label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        return annotated

    def save_image(self, image: np.ndarray, output_path: str) -> str:

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        cv2.imwrite(output_path, image)

        return output_path