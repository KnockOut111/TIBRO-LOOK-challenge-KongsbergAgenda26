FROM ros:jazzy-ros-base

WORKDIR /app

COPY navThread/requirements.txt .

RUN apt-get -o Acquire::Check-Date=false \
            -o Acquire::Check-Valid-Until=false \
            update && \
    apt-get install -y \
        python3-pip \
        python3-lgpio \
        python3-colcon-common-extensions \
        i2c-tools \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

COPY navThread/ /app/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["bash", "-lc", "source /opt/ros/jazzy/setup.bash && python3 -u roverPi_init.py"]