FROM python:3.11-slim

LABEL description="LegalLens AI — Indian Legal Problem Analyzer — OpenEnv"
LABEL version="1.0.0"

# Create user
RUN useradd -m -u 1000 user

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY --chown=user:user . .

# Ensure package install (CRITICAL for validator)
RUN pip install .

# Ensure __init__.py exists (safety)
RUN mkdir -p laws tasks && touch laws/__init__.py tasks/__init__.py

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch user
USER user

# Expose port
EXPOSE 7860

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:7860/health || exit 1

# Start app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]