# Stage 1: build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build tools needed for some packages (e.g. cryptography, pyodbc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: runtime image
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime ODBC driver libraries required by pyodbc
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY server/ ./server/
COPY static/ ./static/
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Create a non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
