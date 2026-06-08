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
        python3-flask \
        python3-picamera2 \
        libcamera-tools \
        libcap-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages --no-cache-dir --no-deps picamzero

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["bash", "-lc", "source /opt/ros/jazzy/setup.bash && python3 -u picamThread.py"]