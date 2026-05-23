# ─────────────────────────────────────────────────────────────────────────────
# Backend Dockerfile — production-ready, multi-stage build
# Stage 1 (builder): installs Python deps into a venv
# Stage 2 (runtime): copies only the venv + source — no build tools in prod image
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.14-slim AS builder

# Prevents Python from writing .pyc files (saves disk I/O in containers)
ENV PYTHONDONTWRITEBYTECODE=1
# Prevents Python output buffering (logs appear immediately in Docker logs)
ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Install system deps needed to compile Python packages (e.g. asyncpg needs C headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest first — Docker layer caches this step if pyproject.toml
# hasn't changed, avoiding a full pip install on every code change.
COPY pyproject.toml .

# Create an isolated virtual environment inside the image
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install all project dependencies from pyproject.toml
# --no-cache-dir: don't store pip's download cache in the image layer
RUN pip install --upgrade pip && pip install --no-cache-dir .


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Create a non-root user — running as root in containers is a security risk
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install only runtime system libraries (libpq for asyncpg at runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built venv from the builder stage — no compiler needed in runtime
COPY --from=builder /opt/venv /opt/venv

# Copy application source code
COPY --chown=appuser:appgroup . .

# Switch to non-root user for all subsequent commands and at runtime
USER appuser

# Expose the port Uvicorn will listen on
EXPOSE 8000

# Health check — Docker uses this to mark the container healthy/unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn with:
#   --host 0.0.0.0  — bind to all interfaces (not just loopback) inside the container
#   --workers 2     — 2 worker processes; tune to (2 * CPU_cores) + 1 in production
#   --no-access-log — disable per-request logs; use structured middleware logging instead
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
