FROM ros:jazzy-ros-base

WORKDIR /app

RUN apt-get update && apt-get install -y \
    i2c-tools \
    python3-pip \
    python3-lgpio \
    python3-libgpiod \
    libgpiod-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt
COPY . .

CMD ["python3", "-u", "sensorThread/imuSensorLogic.py"]