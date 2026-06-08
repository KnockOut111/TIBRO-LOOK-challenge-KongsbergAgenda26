FROM --platform=linux/arm64 ros:jazzy-ros-base
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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONUNBUFFERED=1