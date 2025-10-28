from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from PIL import Image
import io
import os

from .models import ImageAnalysis


class ImageAnalysisAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def create_test_image(self, filename='test_image.jpg', size=(800, 600)):
        file = io.BytesIO()
        image = Image.new('RGB', size, color='red')
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile(
            filename,
            file.getvalue(),
            content_type='image/jpeg'
        )

    def test_upload_image(self):
        image = self.create_test_image()

        response = self.client.post(
            '/api/images/upload/',
            {'image': image},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('data', response.data)
        self.assertIn('id', response.data['data'])
        self.assertEqual(response.data['data']['status'], 'pending')

    def test_upload_invalid_file(self):
        file = SimpleUploadedFile(
            'test.txt',
            b'not an image',
            content_type='text/plain'
        )

        response = self.client.post(
            '/api/images/upload/',
            {'image': file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_analyze_image(self):
        image = self.create_test_image()
        upload_response = self.client.post(
            '/api/images/upload/',
            {'image': image},
            format='multipart'
        )

        image_id = upload_response.data['data']['id']

        analyze_response = self.client.post(
            '/api/images/analyze/',
            {
                'image_id': image_id,
                'apply_correction': True,
                'blur_threshold': 100.0
            },
            format='json'
        )

        self.assertIn(analyze_response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_202_ACCEPTED
        ])

    def test_get_analysis_results(self):
        analysis = ImageAnalysis.objects.create(
            original_image=self.create_test_image(),
            status='completed',
            total_faces=2,
            blurred_faces=1
        )

        response = self.client.get(f'/api/images/{analysis.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['total_faces'], 2)

    def test_list_analyses(self):
        for i in range(3):
            ImageAnalysis.objects.create(
                original_image=self.create_test_image(f'test_{i}.jpg'),
                status='completed'
            )

        response = self.client.get('/api/images/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertEqual(len(response.data['data']), 3)

    def test_delete_analysis(self):
        analysis = ImageAnalysis.objects.create(
            original_image=self.create_test_image(),
            status='completed'
        )

        response = self.client.delete(f'/api/images/{analysis.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ImageAnalysis.objects.filter(id=analysis.id).exists())


class FaceDetectionTestCase(TestCase):

    def test_face_detector_initialization(self):
        from .services import FaceDetector

        detector = FaceDetector()
        self.assertIsNotNone(detector.face_cascade)

    def test_blur_detector_initialization(self):
        from .services import BlurDetector

        detector = BlurDetector(threshold=100.0)
        self.assertEqual(detector.threshold, 100.0)