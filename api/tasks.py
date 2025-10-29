from celery import shared_task
from django.utils import timezone
from django.db import models
import os
import logging

from .models import ImageAnalysis
from .services import FaceDetector, BlurDetector, ImageProcessor

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_image_async(self, analysis_id, blur_threshold=100.0, apply_correction=True):
    
    try:
        analysis = ImageAnalysis.objects.get(id=analysis_id)
        analysis.status = 'processing'
        analysis.save()

        logger.info(f"Starting processing for analysis {analysis_id}")

        image_path = analysis.original_image.path

        face_detector = FaceDetector()
        blur_detector = BlurDetector(threshold=blur_threshold)
        image_processor = ImageProcessor()

        image, face_data = face_detector.detect_faces(image_path)
        logger.info(f"Detected {len(face_data)} faces")

        face_regions = face_detector.extract_face_regions(image, face_data)

        face_data_with_blur = blur_detector.analyze_faces_blur(face_regions, face_data)

        blur_stats = blur_detector.get_overall_blur_stats(face_data_with_blur)
        logger.info(f"Blur stats: {blur_stats}")

        if apply_correction:
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

        logger.info(f"Successfully completed processing for analysis {analysis_id}")

        return {
            'analysis_id': str(analysis_id),
            'status': 'completed',
            'total_faces': blur_stats['total_faces'],
            'blurred_faces': blur_stats['blurred_faces']
        }

    except ImageAnalysis.DoesNotExist:
        logger.error(f"Analysis {analysis_id} not found")
        raise

    except Exception as e:
        logger.error(f"Error processing analysis {analysis_id}: {str(e)}")

        try:
            analysis = ImageAnalysis.objects.get(id=analysis_id)
            analysis.status = 'failed'
            analysis.error_message = str(e)
            analysis.save()
        except:
            pass

        raise self.retry(exc=e, countdown=60)


@shared_task
def cleanup_old_images(days=30):

    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)
    old_analyses = ImageAnalysis.objects.filter(created_at__lt=cutoff_date)

    deleted_count = 0
    for analysis in old_analyses:
        try:
            if analysis.original_image and os.path.exists(analysis.original_image.path):
                os.remove(analysis.original_image.path)

            if analysis.processed_image and os.path.exists(analysis.processed_image.path):
                os.remove(analysis.processed_image.path)

            analysis.delete()
            deleted_count += 1

        except Exception as e:
            logger.error(f"Error deleting analysis {analysis.id}: {str(e)}")

    logger.info(f"Cleaned up {deleted_count} old image analyses")
    return {'deleted_count': deleted_count}


@shared_task
def generate_statistics_report():

    from django.db.models import Count, Avg, Q

    stats = ImageAnalysis.objects.aggregate(
        total_analyses=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        failed=Count('id', filter=Q(status='failed')),
        avg_faces=Avg('total_faces'),
        avg_blurred=Avg('blurred_faces')
    )

    logger.info(f"System statistics: {stats}")
    return stats