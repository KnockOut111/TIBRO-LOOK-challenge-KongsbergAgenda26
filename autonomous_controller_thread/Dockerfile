FROM ros:jazzy-ros-base

WORKDIR /app

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["bash", "-lc", "source /opt/ros/jazzy/setup.bash && python3 -u autonomousController_node.py"]