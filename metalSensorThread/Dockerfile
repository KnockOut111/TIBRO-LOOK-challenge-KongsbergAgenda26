FROM ros:jazzy-ros-base

WORKDIR /app

# Install hardware-related Python support
RUN apt-get update && apt-get install -y \
    python3-gpiozero \
    i2c-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy sources
COPY metalSensorThread/ /app/

# Default command runs the metal sensor node
CMD ["bash", "-lc", "source /opt/ros/jazzy/setup.bash && python3 metalSensorLogic.py"]
