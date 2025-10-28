from django.contrib import admin
from .models import ImageAnalysis


@admin.register(ImageAnalysis)
class ImageAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'total_faces', 'blurred_faces', 'blur_percentage', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'processed_at']

    fieldsets = (
        ('Image Information', {
            'fields': ('id', 'original_image', 'processed_image')
        }),
        ('Analysis Results', {
            'fields': ('status', 'total_faces', 'blurred_faces', 'face_data')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )