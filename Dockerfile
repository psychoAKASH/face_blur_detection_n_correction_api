FROM python:3.11.3-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/* \

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p media/uploads media/processed staticfiles

EXPOSE 8000

CMD ["gunicorn", "face_blur_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]