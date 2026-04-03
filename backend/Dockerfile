FROM python:3.11-slim

WORKDIR /app

# Create non-root user early for security
RUN useradd --create-home --shell /bin/bash appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Prisma schema and generate client
COPY --chown=appuser:appuser prisma/ ./prisma/

# Set Prisma to generate binaries in app directory
ENV PRISMA_BINARY_CACHE_DIR=/app/.prisma

# Generate Prisma client
RUN python -m prisma generate

# Copy application code
COPY --chown=appuser:appuser . .

# Ensure correct ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
