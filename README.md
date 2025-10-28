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
source venv/bin/activate  # On Windows: venv\Scripts\activate
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

## API Endpoints

### 1. Upload Image
- **POST** `/api/images/upload/`
- Upload an image for processing

### 2. Analyze Image
- **POST** `/api/images/analyze/`
- Detect faces and analyze blur

### 3. Get Results
- **GET** `/api/images/results/<id>/`
- Retrieve analysis results

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

## Testing

Sample test with cURL:
```bash
curl -X POST http://localhost:8000/api/images/upload/ \
  -F "image=@path/to/image.jpg"
```