# Face Blur Detection & Correction API

A Django REST API that detects faces in images, identifies blurred faces, and applies automatic correction.

## Features

- Face detection using OpenCV
- Blur detection using Laplacian variance
- Automatic image sharpening/deblurring
- RESTful API with JSON responses
- Swagger API documentation
- Asynchronous task processing with Celery (optional)

## Tech Stack

- Django 4.2
- Django REST Framework
- OpenCV
- NumPy
- PyTorch
- Celery + Redis (for async processing)

## Architecture & Flow  
1. Client uploads an image via API → stored in `media/`  
2. Face detection service runs (OpenCV Haar Cascade)  
3. For each detected face → blur detector computes blur metric (Laplacian variance)  
4. If blur metric is below threshold → image correction service applied (unsharp masking / de-blurring)  
5. Result saved and API provides access to analysis + corrected image  

---

## Setup Instructions

### Prerequisites

- Python 3.8+
- Redis (for Celery tasks)

### Installation

1. Clone the repository:
```bash
git clone 
cd face-blur-detection
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Start Redis (for Celery):
```bash
redis-server
```

6. Start Celery worker (in separate terminal):
```bash
celery -A face_blur_api worker --loglevel=info
```

7. Run development server:
```bash
python manage.py runserver
```

### Option 2: Docker setup
```bash
# 1. Build and start all services
docker-compose up --build -d

# 2. Run migrations
docker-compose exec web python manage.py migrate

# 3. Create superuser (optional)
docker-compose exec web python manage.py createsuperuser

# 4. View logs
docker-compose logs -f

# 5. Stop services
docker-compose down

# alternate
./dev_run.sh
```
## API Endpoints

### 1. Upload Image
- **POST** `/api/images/upload/`
- Upload an image for processing

```bash
curl -X POST http://localhost:8000/api/images/upload/ \
  -F "image=@path/to/image.jpg"
```

**Response:**
```json
{
  "message": "Image uploaded successfully",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "pending",
    "original_image_url": "http://localhost:8000/media/uploads/image.jpg"
  }
}
```

### 2. Analyze Image
- **POST** `/api/images/analyze/`
- Detect faces and analyze blur
```bash
curl -X POST http://localhost:8000/api/images/analyze/ \
  -H "Content-Type: application/json" \
  -d '{
    "image_id": "123e4567-e89b-12d3-a456-426614174000",
    "apply_correction": true,
    "blur_threshold": 100.0,
    "async_processing": false
  }'
```

**Response:**
```json
{
  "message": "Image analysis completed",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "completed",
    "total_faces": 3,
    "blurred_faces": 1,
    "blur_percentage": 33.33,
    "face_data": [
      {
        "face_id": 1,
        "bounding_box": {"x": 100, "y": 150, "width": 200, "height": 200},
        "blur_analysis": {
          "blur_score": 45.67,
          "is_blurred": true,
          "blur_level": "severe"
        }
      }
    ],
    "processed_image_url": "http://localhost:8000/media/processed/processed_123e4567.jpg"
  }
}
```
### 3. Get Results
- **GET** `/api/images/results/<id>/`
- Retrieve analysis results
```bash
curl http://localhost:8000/api/images/123e4567-e89b-12d3-a456-426614174000/
```
## API Documentation

Access Swagger documentation at: `http://localhost:8000/swagger/`

## Model Choice & Reasoning

**Face Detection**: OpenCV's Haar Cascade classifier
- Lightweight and fast
- No GPU required
- Suitable for production deployment

**Blur Detection**: Laplacian Variance Method
- Simple and effective
- Fast computation
- Good accuracy for blur detection

**Deblurring**: Unsharp Masking
- Classical image processing technique
- Computationally efficient
- Produces good results for mild blur

## Project Structure
```
face-blur-detection/
├── face_blur_api/          # Django project settings
├── api/                    # Main API application
│   ├── models.py          # Database models
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API views
│   ├── services/          # Business logic
│   │   ├── face_detector.py
│   │   ├── blur_detector.py
│   │   └── image_processor.py
│   └── tasks.py           # Celery tasks
├── media/                 # Uploaded images
├── requirements.txt
└── README.md
```


