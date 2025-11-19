FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    curl \
    && apt-get clean

# Create app directory
WORKDIR /app

# Copy requirements (so Docker caching works well)
COPY requirements ./requirements

# Install your custom wheel first
RUN pip install requirements/django_nose-1.4.7-py2.py3-none-any.whl

# Install dev requirements as requested
RUN pip install -r requirements/dev.txt

# Copy the full project code
COPY . .

# Collect static files (if needed in prod)
RUN python manage.py collectstatic --noinput || true

EXPOSE 6000

# Default command to run server
CMD ["gunicorn", "src.wsgi:application", "--bind", "0.0.0.0:6000"]
