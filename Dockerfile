# BDOCS API - Production Dockerfile
# Multi-stage build for Python 3.11 with Hypercorn ASGI server

# =============================================================================
# Stage 1: Build dependencies
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv and generate requirements
COPY Pipfile Pipfile.lock ./

# Generate requirements, filtering out problematic packages:
# - cx-oracle: Requires Oracle Instant Client
# - greenlet: Not needed for pure async code with asyncpg
RUN pip install --no-cache-dir pipenv \
    && pipenv requirements > requirements-raw.txt \
    && grep -v -E "^(cx-oracle|greenlet)" requirements-raw.txt > requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Production image
# =============================================================================
FROM python:3.11-slim AS production

# Security: Create non-root user
RUN groupadd --gid 1000 bdocs \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home bdocs

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=bdocs:bdocs . .

# Make entrypoint executable
RUN chmod +x /app/scripts/entrypoint.sh

# Switch to non-root user
USER bdocs

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_ENV=production \
    PORT=5000

# Expose application port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

# Default command
ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["hypercorn", "app:main", "--bind", "0.0.0.0:5000", "--workers", "4"]
