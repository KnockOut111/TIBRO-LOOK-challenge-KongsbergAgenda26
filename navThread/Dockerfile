FROM ros:jazzy-ros-base

WORKDIR /app

COPY navThread/requirements.txt .

RUN apt update && apt install -y \
    python3-pip \
    python3-lgpio \
    python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "-u", "roverPi_init.py"]
