FROM ros:jazzy-ros-base

WORKDIR /app

RUN apt-get -o Acquire::Check-Date=false \
            -o Acquire::Check-Valid-Until=false \
            update && \
    apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

CMD ["bash", "-lc", "source /opt/ros/jazzy/setup.bash && python3 -u manualcommands.py"]