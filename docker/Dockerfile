# === Stage 1: Python dependencies ===
FROM python:3.11-slim AS deps

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# === Stage 2: Runtime ===
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# System deps: only runtime libraries (not -dev), tesseract, java, archive tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    openjdk-17-jre-headless \
    wget curl \
    unrar p7zip-full \
    && rm -rf /var/lib/apt/lists/*

# PlantUML
RUN wget -q https://github.com/plantuml/plantuml/releases/download/v1.2024.0/plantuml-1.2024.0.jar \
    -O /opt/plantuml.jar
ENV PLANTUML_JAR=/opt/plantuml.jar

# Copy Python packages from build stage
COPY --from=deps /install /usr/local

# Create non-root user
RUN groupadd -r d2a && useradd -r -g d2a -d /app -s /sbin/nologin d2a

WORKDIR /app

# Application code
COPY app/ ./app/
COPY main.py .
COPY static/ ./static/

RUN ln -sf /opt/plantuml.jar /app/plantuml.jar && \
    mkdir -p /app/data /app/eval_output && \
    chown -R d2a:d2a /app

USER d2a

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
