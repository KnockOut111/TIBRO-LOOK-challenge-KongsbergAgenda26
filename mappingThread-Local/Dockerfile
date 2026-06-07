FROM ros:jazzy-ros-base

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-numpy \
    python3-opencv \
    python3-flask \
    libusb-1.0-0-dev \
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    ros-jazzy-librealsense2 \
    ros-jazzy-realsense2-camera \
    ros-jazzy-depthimage-to-laserscan \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

ENV PYTHONUNBUFFERED=1
