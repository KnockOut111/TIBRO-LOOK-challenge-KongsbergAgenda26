FROM python:3.12-slim

WORKDIR /app

# Install system deps commonly needed for hardware access and building wheels
RUN apt-get update && apt-get install -y \
    i2c-tools \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY metalSensorThread/requirements.txt /tmp/requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Copy sources
COPY metalSensorThread/ /app/

# Default command runs the metal sensor node
CMD ["python3", "metalSensorLogic.py"]
