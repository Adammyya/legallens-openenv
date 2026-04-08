FROM python:3.11-slim

LABEL description="LegalLens AI — Indian Legal Problem Analyzer — OpenEnv"
LABEL version="1.0.0"

RUN useradd -m -u 1000 user
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY --chown=user:user . .

# Create __init__ files for subdirs

RUN mkdir -p laws tasks && touch laws/__init__.py tasks/__init__.py

USER user
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:7860/health || exit 1

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]

RUN pip install .

RUN python -m pip install --upgrade pip
