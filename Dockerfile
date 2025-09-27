# Multi-stage Dockerfile for NSE Data ETL
# Production-ready with security best practices and optimizations

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add metadata labels
LABEL org.opencontainers.image.title="NSE Data ETL"
LABEL org.opencontainers.image.description="High-performance NSE financial data ETL system"
LABEL org.opencontainers.image.created=$BUILD_DATE
LABEL org.opencontainers.image.revision=$VCS_REF
LABEL org.opencontainers.image.version=$VERSION
LABEL org.opencontainers.image.vendor="NSE Data ETL Team"
LABEL org.opencontainers.image.licenses="MIT"

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e .

# Production stage
FROM python:3.11-slim as production

# Set production arguments
ARG APP_USER=nse_etl
ARG APP_UID=1000
ARG APP_GID=1000

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for ClickHouse driver
    ca-certificates \
    # Health check utilities
    curl \
    # Process monitoring
    procps \
    # Timezone data
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -g $APP_GID $APP_USER && \
    useradd -u $APP_UID -g $APP_GID -m -s /bin/bash $APP_USER

# Set work directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=$APP_USER:$APP_USER src/ ./src/
COPY --chown=$APP_USER:$APP_USER configs/ ./configs/
COPY --chown=$APP_USER:$APP_USER scripts/ ./scripts/
COPY --chown=$APP_USER:$APP_USER pyproject.toml ./

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/tmp && \
    chown -R $APP_USER:$APP_USER /app

# Set Python path
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Security and performance environment variables
ENV PYTHONHASHSEED=random
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Application environment variables
ENV APP_ENV=production
ENV LOG_LEVEL=INFO
ENV LOG_FORMAT=json
ENV API_HOST=0.0.0.0
ENV API_PORT=8080
ENV METRICS_PORT=8000

# Switch to non-root user
USER $APP_USER

# Expose application ports
EXPOSE 8080 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "nse_etl.main"]

# Alternative development stage
FROM production as development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Install additional development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Set development environment
ENV APP_ENV=development
ENV DEBUG=true
ENV LOG_LEVEL=DEBUG
ENV LOG_FORMAT=text

# Switch back to app user
USER $APP_USER

# Development command with hot reload
CMD ["python", "-m", "nse_etl.main", "--reload"]