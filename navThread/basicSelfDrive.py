import rclpy

from typing import Callable
from rclpy.timer import Timer
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.executors import ExternalShutdownException

from locomotionController import LocomotionController, LocomotionModes, SteeringServos
import TimerManager
from metalSensorThread import metalSensorLogic


class basicSelfDrive():
    def __init__(self):
        super().__init__("basicSelfDrive_node")

        