# --- Stage 1: Build ---
FROM ghcr.io/astral-sh/uv:latest AS uv_base

FROM python:3.13-slim AS build
COPY --from=uv_base /uv /uv /usr/bin/

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_CACHE=1

# Copy project files for dependency resolution
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
# We use --no-install-project because we'll copy the source later
RUN /usr/bin/uv sync --frozen --no-install-project --no-dev

# --- Stage 2: Runtime ---
FROM python:3.13-slim
LABEL maintainer="ScrapeBee Team"
LABEL description="Optimized ScrapeBee Web & PDF Toolset"

WORKDIR /app

# Python environment variables for optimization and stability
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=1 \
    PATH="/app/.venv/bin:$PATH"

# Install system dependencies in a single layer and cleanup
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    chromium \
    chromium-driver \
    xvfb \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the build stage
COPY --from=build /app/.venv /app/.venv

# Copy the source code and necessary files
COPY src /app/src
COPY README.md /app/

# Create a non-root user for security
RUN useradd -m -U scrapebee && \
    chown -R scrapebee:scrapebee /app

USER scrapebee

# Expose Streamlit port
EXPOSE 8501

# Healthcheck to ensure service is up
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the application
ENTRYPOINT ["streamlit", "run", "src/scrapebee/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
