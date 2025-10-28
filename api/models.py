from django.db import models
from django.core.validators import FileExtensionValidator
import uuid


class ImageAnalysis(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_image = models.ImageField(
        upload_to='uploads/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    processed_image = models.ImageField(
        upload_to='processed/',
        null=True,
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_faces = models.IntegerField(default=0)
    blurred_faces = models.IntegerField(default=0)
    face_data = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Image Analysis'
        verbose_name_plural = 'Image Analyses'

    def __str__(self):
        return f"Analysis {self.id} - {self.status}"

    @property
    def has_blurred_faces(self):
        return self.blurred_faces > 0

    @property
    def blur_percentage(self):
        """Calculate percentage of blurred faces"""
        if self.total_faces == 0:
            return 0
        return (self.blurred_faces / self.total_faces) * 100