FROM python:3.12-slim

# Avoid writing .pyc files and buffering output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /code

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application code and version file
COPY app ./app
COPY VERSION ./VERSION

# Expose the port uvicorn will serve on
EXPOSE 8000

# Run with auto-reload disabled in the built image; compose can override
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
