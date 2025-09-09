# Use the official Python image as build environment
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source
COPY . .

# Final minimal image
FROM python:3.11-slim

# Install CA certificates for HTTPS to work
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python packages and app from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app/bot ./bot
COPY --from=builder /app/data ./data

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Entrypoint
CMD ["python", "-m", "bot.main"]
