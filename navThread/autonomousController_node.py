import rclpy

from typing import Callable
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.executors import ExternalShutdownException

from locomotionController import LocomotionController
from timer import TimerManager

# Implement autonomous behavior logic here, e.g.:
        # - Use sensor data to navigate - IMU at start, turning using point turn etc.
        # - Implement obstacle avoidance
        # - Follow a predefined path or explore randomly

#### State machine ####
class AutonomousController(Node):
    def __init__(self):
        super().__init__("autonomous_controller_node")

        self.controller = LocomotionController()
        self.timer_manager = self.TimerManager(self)

        # Subscriptions
        self.create_subscription(String, "/autonomousController_node/start_autonomous_program", self.starting_state, 10)
        self.create_subscription(String, "/rover/system_shutdown", self.shutdown_callback, 10)  # Defining a callback for the shutdown topic 

        # Publications
        self.mainState_pub = self.create_publisher(String, "/rover/mainMode/", 10)

        self.mainState_pub = self.create_publisher(String, "/rover/mainMode", 10)
        self.mainState_msg = String()

        self.loco_mode_msg_pub = self.create_publisher(String, "/rover/locoMode", 10)
        self.mainState_msg = String()

        self.command_msg_pub = self.create_publisher(String, "/rover/command", 10)
        self.command_msg = String()



    def starting_state(self):
        self.get_logger().info("Starting up rover and driving off ramp...")
        
        self.arm_rover()
        self.set_loco_mode("crabbing") # Is set to this by default so maybe obsolete?
        self.set_command("forward")
        # Taking in IMU data - when in plannar state again, continue
        self.set_command("stop")

        # Drive off ramp until IMU shows planer surfaces again. 0 at beginning, 
        # then tilt some degrees (going off ramp), 0 again when off ramp + some deviation in level hight.
        # As the ramp is higher up than the main area of traversal. 

    def scanning_state(self):
        self.get_logger().info("Starting scanning the area by turning 360 degrees. ")
        
        self.set_loco_mode("point_turn")
        self.TimerManager.start_timer("stop_delay", 1.0, self.set_command("right_turn"))



        # Scan the area by turning 360 degrees in point_turn mode, as long as no obsticles are detected. 
        # Simultaneously as stereo camera is taking in the suroundings. 


    def obsticle_detected(self):
        self.get_logger().info("Obsticle detected! ")

    def driving_and_mapping(self):
        self.get_logger().info("Entering main logic for driving and mapping. ")
        self.set_command("forward")


        # Drive forward, untill object detected inside a given distance.
        # Then stop, move backwards for 2s? then move random? left or right.
        # Now continuing on the new path, until new object is 'detected' again or 
        # innside the given limit of radius to possible obstacle.

    def idle(self):
        self.get_logger().info("The rover is in idle state. ")
        self.set_command("stop")


#### Helper functions ####
    def arm_rover(self):
        self.mainState_msg.data = "arm"
        self.mainState_pub.publish(self.mainState_msg)

    def set_loco_mode(self, msg):
        self.loco_mode_msg.data = msg
        self.loco_mode_msg_pub.publish(self.loco_mode_msg)

    def set_command(self, cmd):
        self.command_msg.data = cmd
        self.command_msg_pub.publish(self.command_msg)


#### Shutdown clean functions ####
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