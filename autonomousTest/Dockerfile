# Dockerfile
FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-gpiozero \
    python3-libgpiod \
    i2c-tools \
    libgpiod2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    numpy \
    adafruit-circuitpython-servokit

WORKDIR /app

COPY autonomous_simple_node.py /app/autonomous_simple_node.py

CMD ["/bin/bash", "-lc", "source /opt/ros/humble/setup.bash && python3 /app/autonomous_simple_node.py"]