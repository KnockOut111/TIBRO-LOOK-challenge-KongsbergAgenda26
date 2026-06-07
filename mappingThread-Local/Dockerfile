FROM osrf/ros:jazzy-desktop

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install system dependencies, USB tools, and Python environment tools
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-numpy \
    python3-opencv \
    python3-flask \
    libusb-1.0-0-dev \
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Intel RealSense SDK bindings natively for Ubuntu Noble / Jazzy
RUN apt-get update && apt-get install -y \
    ros-jazzy-librealsense2 \
    ros-jazzy-realsense2-camera \
    && rm -rf /var/lib/apt/lists/*

# 3. Use pip only for pyrealsense2 if needed, though native apt is preferred.
# --break-system-packages is required by modern Ubuntu versions inside containers.
RUN pip3 install --break-system-packages pyrealsense2

# Set the working directory inside the container
WORKDIR /app

# Ensure output prints directly to docker logs in real-time
ENV PYTHONUNBUFFERED=1