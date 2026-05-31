from locomotionController import LocomotionController, LocomotionModes
from enum import Enum
from rclpy.node import Node
from std_msgs.msg import String

import rclpy
import math

controller = LocomotionController()


class LocomotionModes(Enum):
    ACKERMANN = 0
    POINT_TURN = 1
    CRABBING = 2

#remember to implement functionality for the different logic steps (was commented out in local file.)
# Need to adapt to Ros2 yazzy and using nodes. 
# Fix locomotion modes to work as it should, wheels are never set back to 90 degrees after turning, and point turn and crab steering are not implemented propperly.


class MainLogicNode(Node):
    def __init__(self):
        super().__init__("main_logic")

        max_steering_angle = 45
        self.ackermann_r_min = abs(self.wheel_y) / math.tan(math.radians(max_steering_angle)) + self.wheel_x
        self.ackermann_r_max = 250

        self.active = False
        self.locomotion_mode = None

        self.create_subscription(String, "/rover/mode", self.mode_callback, 10)
        self.create_subscription(String, "/rover/locomotion_mode", self.locomotion_callback, 10)
        self.create_subscription(String, "/rover/command", self.command_callback, 10)

        self.get_logger().info("main_logic node started")

    def mode_callback(self, msg):
        mainMode = msg.data.strip().lower()

        if mainMode == "launch":
            self.active = True
            self.get_logger().info("Rover launched")

        elif mainMode == "quit":
            self.active = False
            self.get_logger().info("Rover stopped and program exiting")

        else:
            self.get_logger().warn(f"Invalid mode: {mainMode}")

    def locomotion_callback(self, msg):
        locoMode = msg.data.strip().lower()

        if locoMode == "ackermann":
            self.locomotion_mode = LocomotionModes.ACKERMANN
            self.get_logger().info("Ackermann mode activated.")
            print("Ackermann mode activated.")

        elif locoMode == "point_turn":
            self.locomotion_mode = LocomotionModes.POINT_TURN
            self.get_logger().info("Point turn mode activated.")
            print("Point turn mode activated.")

        elif locoMode == "crabbing":
            self.locomotion_mode = LocomotionModes.CRABBING
            self.get_logger().info("Crabbing mode activated.")
            print("Crabbing mode activated.")

        else:
            self.get_logger().warn(f"Invalid locomotion mode: {locoMode}")
            return

        self.get_logger().info(f"Locomotion mode set to {self.locomotion_mode.name}")

    def command_callback(self, msg):
        command = msg.data.strip().lower()

        if not self.active:
            self.get_logger().warn("Ignoring command because rover is not launched")
            return

        # Implement missing command handling logic here, e.g.:
        if command == "forward":
            self.get_logger().info("Moving forward")

        elif command == "backward":
            self.get_logger().info("Moving backward")

        elif command == "stop":
            self.get_logger().info("Stopping rover")

        elif command == "left_turn":
            self.get_logger().info("Turning left")

        elif command == "right_turn":
            self.get_logger().info("Turning right")

        else:
            self.get_logger().warn(f"Unknown command: {command}")


def main(args=None):
    rclpy.init(args=args)
    node = MainLogicNode()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()