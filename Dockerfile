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

RUN mkdir -p laws tasks \
    && touch laws/__init__.py tasks/__init__.py

USER user

EXPOSE 7860

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:7860/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--app-dir", "/app"]