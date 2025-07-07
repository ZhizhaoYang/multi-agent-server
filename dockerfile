FROM python:3.11-slim

WORKDIR /app

# Install system dependencies, PostgreSQL client libraries, and uv
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Copy uv configuration files
COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Install the project in development mode using uv
RUN uv pip install -e . --system

# Expose port
EXPOSE 8000

# Start command - use Render's dynamic PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload"]