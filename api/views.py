from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import os
import cv2

from .models import ImageAnalysis
from .serializers import (
    ImageUploadSerializer,
    ImageAnalysisSerializer,
    ImageAnalysisDetailSerializer,
    AnalyzeImageSerializer
)
from .services import FaceDetector, BlurDetector, ImageProcessor


class ImageAnalysisViewSet(viewsets.ModelViewSet):
    queryset = ImageAnalysis.objects.all()
    serializer_class = ImageAnalysisSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ImageAnalysisDetailSerializer
        return ImageAnalysisSerializer

    @swagger_auto_schema(
        operation_description="Upload an image for processing",
        request_body=ImageUploadSerializer,
        responses={
            201: ImageAnalysisSerializer,
            400: "Bad Request"
        }
    )
    @action(detail=False, methods=['post'], url_path='upload')
    def upload_image(self, request):
        serializer = ImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        analysis = ImageAnalysis.objects.create(
            original_image=serializer.validated_data['image'],
            status='pending'
        )

        result_serializer = ImageAnalysisSerializer(
            analysis,
            context={'request': request}
        )

        return Response(
            {
                'message': 'Image uploaded successfully',
                'data': result_serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        operation_description="Analyze image for face detection and blur",
        request_body=AnalyzeImageSerializer,
        responses={
            200: ImageAnalysisDetailSerializer,
            400: "Bad Request",
            404: "Not Found"
        }
    )
    @action(detail=False, methods=['post'], url_path='analyze')
    def analyze_image(self, request):
        serializer = AnalyzeImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        if data.get('image_id'):
            analysis = get_object_or_404(ImageAnalysis, id=data['image_id'])
            image_path = analysis.original_image.path
        else:
            analysis = ImageAnalysis.objects.create(
                original_image=data['image'],
                status='pending'
            )
            image_path = analysis.original_image.path
        if data.get('async_processing', False):
            from .tasks import process_image_async
            task = process_image_async.delay(
                str(analysis.id),
                data.get('blur_threshold', 100.0),
                data.get('apply_correction', True)
            )

            analysis.status = 'processing'
            analysis.save()

            return Response({
                'message': 'Image processing started',
                'task_id': task.id,
                'analysis_id': str(analysis.id),
                'status': 'processing'
            }, status=status.HTTP_202_ACCEPTED)

        try:
            analysis.status = 'processing'
            analysis.save()

            face_detector = FaceDetector()
            blur_detector = BlurDetector(threshold=data.get('blur_threshold', 100.0))
            image_processor = ImageProcessor()

            image, face_data = face_detector.detect_faces(image_path)

            face_regions = face_detector.extract_face_regions(image, face_data)

            face_data_with_blur = blur_detector.analyze_faces_blur(face_regions, face_data)

            blur_stats = blur_detector.get_overall_blur_stats(face_data_with_blur)

            if data.get('apply_correction', True):
                processed_image = image_processor.process_full_image(image, face_data_with_blur)
                annotated_image = image_processor.add_annotations(processed_image, face_data_with_blur)

                processed_path = os.path.join(
                    'media',
                    'processed',
                    f'processed_{analysis.id}.jpg'
                )
                image_processor.save_image(annotated_image, processed_path)

                analysis.processed_image = processed_path.replace('media/', '')

            analysis.total_faces = blur_stats['total_faces']
            analysis.blurred_faces = blur_stats['blurred_faces']
            analysis.face_data = face_data_with_blur
            analysis.status = 'completed'
            analysis.processed_at = timezone.now()
            analysis.save()

            result_serializer = ImageAnalysisDetailSerializer(
                analysis,
                context={'request': request}
            )

            return Response({
                'message': 'Image analysis completed',
                'data': result_serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            analysis.status = 'failed'
            analysis.error_message = str(e)
            analysis.save()

            return Response({
                'error': 'Image processing failed',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="Get analysis results by ID",
        responses={
            200: ImageAnalysisDetailSerializer,
            404: "Not Found"
        }
    )
    def retrieve(self, request, pk=None):
        analysis = get_object_or_404(ImageAnalysis, pk=pk)
        serializer = ImageAnalysisDetailSerializer(
            analysis,
            context={'request': request}
        )

        return Response({
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="List all image analyses",
        responses={200: ImageAnalysisSerializer(many=True)}
    )
    def list(self, request):
        queryset = self.get_queryset()
        serializer = ImageAnalysisSerializer(
            queryset,
            many=True,
            context={'request': request}
        )

        return Response({
            'count': queryset.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Delete an image analysis",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, pk=None):
        analysis = get_object_or_404(ImageAnalysis, pk=pk)
        if analysis.original_image:
            if os.path.exists(analysis.original_image.path):
                os.remove(analysis.original_image.path)

        if analysis.processed_image:
            if os.path.exists(analysis.processed_image.path):
                os.remove(analysis.processed_image.path)

        analysis.delete()

        return Response(
            {'message': 'Image analysis deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )