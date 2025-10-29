from rest_framework import serializers
from .models import ImageAnalysis


class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)

    def validate_image(self, value):
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Image file too large. Max size is 10MB.")

        allowed_extensions = ['jpg', 'jpeg', 'png']
        ext = value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Unsupported file extension. Allowed: {', '.join(allowed_extensions)}"
            )

        return value


class FaceDataSerializer(serializers.Serializer):
    face_id = serializers.IntegerField()
    bounding_box = serializers.DictField()
    confidence = serializers.FloatField()
    blur_analysis = serializers.DictField(required=False)


class ImageAnalysisSerializer(serializers.ModelSerializer):
    face_data = FaceDataSerializer(many=True, read_only=True)
    blur_percentage = serializers.FloatField(read_only=True)
    has_blurred_faces = serializers.BooleanField(read_only=True)
    original_image_url = serializers.SerializerMethodField()
    processed_image_url = serializers.SerializerMethodField()

    class Meta:
        model = ImageAnalysis
        fields = [
            'id',
            'status',
            'total_faces',
            'blurred_faces',
            'blur_percentage',
            'has_blurred_faces',
            'face_data',
            'original_image_url',
            'processed_image_url',
            'created_at',
            'updated_at',
            'processed_at',
            'error_message'
        ]
        read_only_fields = [
            'id',
            'status',
            'total_faces',
            'blurred_faces',
            'face_data',
            'created_at',
            'updated_at',
            'processed_at',
            'error_message'
        ]

    def get_original_image_url(self, obj):
        if obj.original_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.original_image.url)
            return obj.original_image.url
        return None

    def get_processed_image_url(self, obj):
        if obj.processed_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.processed_image.url)
            return obj.processed_image.url
        return None


class ImageAnalysisDetailSerializer(ImageAnalysisSerializer):
    statistics = serializers.SerializerMethodField()

    class Meta(ImageAnalysisSerializer.Meta):
        fields = ImageAnalysisSerializer.Meta.fields + ['statistics']

    def get_statistics(self, obj):
        if not obj.face_data:
            return None

        blur_scores = [
            face.get('blur_analysis', {}).get('blur_score', 0)
            for face in obj.face_data
        ]

        return {
            'total_faces': obj.total_faces,
            'sharp_faces': obj.total_faces - obj.blurred_faces,
            'blurred_faces': obj.blurred_faces,
            'blur_percentage': obj.blur_percentage,
            'average_blur_score': round(sum(blur_scores) / len(blur_scores), 2) if blur_scores else 0,
            'min_blur_score': round(min(blur_scores), 2) if blur_scores else 0,
            'max_blur_score': round(max(blur_scores), 2) if blur_scores else 0,
        }


class AnalyzeImageSerializer(serializers.Serializer):
    image_id = serializers.UUIDField(required=False)
    image = serializers.ImageField(required=False)
    apply_correction = serializers.BooleanField(default=True)
    blur_threshold = serializers.FloatField(default=100.0, min_value=0)
    async_processing = serializers.BooleanField(default=False)

    def validate(self, data):
        if not data.get('image_id') and not data.get('image'):
            raise serializers.ValidationError(
                "Either 'image_id' or 'image' must be provided"
            )

        if data.get('image_id') and data.get('image'):
            raise serializers.ValidationError(
                "Provide either 'image_id' or 'image', not both"
            )

        return data
