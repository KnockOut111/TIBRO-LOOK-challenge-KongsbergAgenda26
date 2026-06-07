import rclpy

from typing import Callable
from rclpy.timer import Timer
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.executors import ExternalShutdownException


class AutonomousController(Node):
    def __init__(self):
        super().__init__("autonomous_controller_node")

        #Defining a callback for the shutdown topic 
	    self.create_subscription(String, "/rover/system_shutdown", self.shutdown_callback, 10)

        # Subscriptions
        self.create_subscription(String, "/autonomousController_node/start_autonomous_program", self.starting_procedure, 10)


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

    def destroy_node(self):
        super().destroy_node()
    
    def shutdown_callback(self, msg):
        if msg.data.strip().lower() == "shutdown":
            self.get_logger().info("Shutdown signal received. Shutting down metal sensor node...")
            rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    node = AutonomousController()
    
    try:
	    rclpy.spin(node)
    
    except ExternalShutdownException:
        pass
    
    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
		
        if rclpy.ok():
            rclpy.shutdown()