import rclpy

from typing import Callable
from rclpy.timer import Timer
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.executors import ExternalShutdownException


class AutonomousController(Node):
    def __init__(self):
        super().__init__("autonomous_controller_node")

    # Subscriptions
    self.create_subscription(String, "/rover/sensorMsg", self.autonomous_mode, 10)

    def starting_procedure():
        print("Starting up rover and driving off ramp...")

        # Drive off ramp until IMU shows planer surfaces again. 0 at beginning, 
        # then tilt some degrees (going off ramp), 0 agan when off ramp + some deviation in level hight.
        # As the ramp is higher up than the main area of traversal. 

    def scanning_mode(self):
        print("Starting scanning the area by turning 360 degrees. ")
        # Scan the area by turning 360 degrees in point_turn mode, as long as no obsticles are detected. 
        # Simultaneously as stereo camera is taking in the suroundings. 

    def main_loop(self):
        print("Entering the main logic of the rover driving. ")
        # Drive forward, untill object detected inside a given distance.
        # Then stop, move backwards for 2s? then move random? left or right.
        # Now continuing on the new path, until new object is 'detected' again or 
        # innside the given limit of radius to possible obstacle.

def main(args=None):
    rclpy.init(args=args)
    mainLogic_node = MainLogicNode()
    
    try:
        rclpy.spin(mainLogic_node)
    
    except ExternalShutdownException:
        pass

    finally:
        mainLogic_node.cancel_all_timers()
        mainLogic_node.controller.stop()

        if rclpy.ok():
            rclpy.shutdown()