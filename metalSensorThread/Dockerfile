FROM ros:jazzy-ros-base

WORKDIR /app

RUN apt-get -o Acquire::Check-Date=false \
            -o Acquire::Check-Valid-Until=false \
            update && \
    apt-get install -y \
        python3-gpiozero \
        i2c-tools \
    && rm -rf /var/lib/apt/lists/*

COPY metalSensorThread/ /app/

CMD ["bash", "-lc", "source /opt/ros/jazzy/setup.bash && python3 -u metalSensorLogic.py"]