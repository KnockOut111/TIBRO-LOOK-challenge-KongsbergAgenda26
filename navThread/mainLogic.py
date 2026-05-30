from enum import Enum

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class LocomotionModes(Enum):
    ACKERMANN = 0
    POINT_TURN = 1
    CRABBING = 2

#remember to implement functionality for the different logic steps (was commented out in local file.)

class MainLogicNode(Node):
    def __init__(self):
        super().__init__("main_logic")

        self.active = False
        self.locomotion_mode = LocomotionModes.ACKERMANN

        self.create_subscription(String, "/rover/mode", self.mode_callback, 10)
        self.create_subscription(String, "/rover/locomotion_mode", self.locomotion_callback, 10)
        self.create_subscription(String, "/rover/command", self.command_callback, 10)

        self.get_logger().info("main_logic node started")

    def mode_callback(self, msg):
        mode = msg.data.strip().lower()

        if mode == "launch":
            self.active = True
            self.get_logger().info("Rover launched")

        elif mode == "quit":
            self.active = False
            self.get_logger().info("Rover stopped")

        else:
            self.get_logger().warn(f"Invalid mode: {mode}")

    def locomotion_callback(self, msg):
        mode = msg.data.strip().lower()

        if mode == "ackermann":
            self.locomotion_mode = LocomotionModes.ACKERMANN

        elif mode == "point_turn":
            self.locomotion_mode = LocomotionModes.POINT_TURN

        elif mode == "crabbing":
            self.locomotion_mode = LocomotionModes.CRABBING

        else:
            self.get_logger().warn(f"Invalid locomotion mode: {mode}")
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