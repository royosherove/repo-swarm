# Use a slim Python base image
FROM python:3.12-slim

# Build arguments
ARG GITHUB_TOKEN
ARG BUILD_ENV=development
ARG GIT_COMMIT=unknown
ARG TEMPORAL_SERVER_URL=localhost:7233
ARG TEMPORAL_NAMESPACE=default
ARG TEMPORAL_TASK_QUEUE=investigate-task-queue
ARG TEMPORAL_IDENTITY=investigate-worker
ARG LOCAL_TESTING=false
ARG TEMPORAL_API_KEY

# Install system dependencies with optimizations for speed
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        -o APT::Install-Suggests=0 \
        -o APT::Install-Recommends=0 \
        build-essential \
        curl \
        git \
        ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install uv for fast Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app

# Install mise and uv for the app user
USER app
RUN curl https://mise.run | MISE_VERSION=v2025.7.26 sh
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add mise and uv to PATH for app user
ENV PATH="/home/app/.local/bin:/home/app/.cargo/bin:$PATH"

# Set the working directory inside the container
WORKDIR /app

# Copy the entire application source code
COPY --chown=app:app . .

# Set Python path to include the project root
ENV PYTHONPATH=/app/src

# Set build-time environment variables
ENV BUILD_ENV=${BUILD_ENV}
ENV GIT_COMMIT=${GIT_COMMIT}

# Runtime environment variables (can be overridden)
ENV TEMPORAL_SERVER_URL=${TEMPORAL_SERVER_URL}
ENV TEMPORAL_NAMESPACE=${TEMPORAL_NAMESPACE}
ENV TEMPORAL_TASK_QUEUE=${TEMPORAL_TASK_QUEUE}
ENV TEMPORAL_IDENTITY=${TEMPORAL_IDENTITY}
ENV LOCAL_TESTING=${LOCAL_TESTING}

ENV GITHUB_TOKEN=${GITHUB_TOKEN}
ENV TEMPORAL_API_KEY=${TEMPORAL_API_KEY}

# Trust the mise configuration
RUN /home/app/.local/bin/mise trust

# Install mise tools (like Python, Temporal CLI)
RUN /home/app/.local/bin/mise install

# Install Python dependencies using uv
RUN uv sync

# Set up mise environment properly for runtime
# This ensures the mise-installed Python and packages are used
RUN echo 'eval "$(/home/app/.local/bin/mise activate bash)"' >> /home/app/.bashrc
ENV MISE_SHELL=bash

# Ensure proper logging output
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Expose ports for health checks and metrics
EXPOSE 4567 9090

# Health check for ECS task - verifies the worker is running and updating its health file
# ECS will use this to determine container health status
# --interval: How often to check health (30s)
# --timeout: How long to wait for health check to complete (10s)
# --start-period: Grace period before health checks start counting (60s for worker startup)
# --retries: How many consecutive failures before marking unhealthy (3)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /home/app/.local/bin/mise exec python /app/src/health_check.py || exit 1

# Default command runs the worker using mise environment
# Ensure all output goes to stdout/stderr for proper logging
CMD ["/bin/bash", "-c", "/home/app/.local/bin/mise run worker 2>&1"] 