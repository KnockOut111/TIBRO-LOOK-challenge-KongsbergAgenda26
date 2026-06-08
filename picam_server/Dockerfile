FROM ros:jazzy-ros-base

WORKDIR /app

RUN apt-get \
    -o Acquire::Check-Date=false \
    -o Acquire::Check-Valid-Until=false \
    update && \
    apt-get install -y \
        python3-pip \
        python3-opencv \
        python3-numpy \
        libcamera-tools \
        python3-libcamera \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages --no-cache-dir \
    picamera2 \
    picamzero

COPY picam_server/ /app/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["bash", "-lc", "source /opt/ros/jazzy/setup.bash && python3 -u picamThread.py"]