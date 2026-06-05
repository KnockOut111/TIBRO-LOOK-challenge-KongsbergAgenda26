FROM ros:jazzy-ros-base

WORKDIR /app

RUN apt-get update && apt-get install -y \
    i2c-tools \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY sensorThread/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "-u", "sensorThread/imuSensorLogic.py"]