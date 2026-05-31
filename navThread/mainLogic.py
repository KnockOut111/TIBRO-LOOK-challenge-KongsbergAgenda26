from locomotionController import LocomotionController, LocomotionModes
from enum import Enum
from rclpy.node import Node
from std_msgs.msg import String
import rclpy

#remember to implement functionality for the different logic steps (was commented out in local file.)
# Need to adapt to Ros2 yazzy and using nodes. 
# Fix locomotion modes to work as it should, wheels are never set back to 90 degrees after turning, and point turn and crab steering are not implemented propperly.


class MainLogicNode(Node):
    def __init__(self):
        super().__init__("main_logic")
        
        self.controller = LocomotionController()

        # max_steering_angle = 45
        # self.ackermann_r_min = abs(self.wheel_y) / math.tan(math.radians(max_steering_angle)) + self.wheel_x
        # self.ackermann_r_max = 250

        self.active = False
        self.locomotion_mode = LocomotionModes.ACKERMANN

        self.create_subscription(String, "/rover/mainMode", self.mode_callback, 10)
        self.create_subscription(String, "/rover/locoMode", self.locomotion_callback, 10)
        self.create_subscription(String, "/rover/command", self.command_callback, 10)

        self.get_logger().info("main_logic node started")

    def mode_callback(self, msg):
        mainMode = msg.data.strip().lower()

        if mainMode == "launch":
            self.active = True
            self.get_logger().info("Rover launched")

        elif mainMode == "quit":
            self.active = False
            self.get_logger().info("Rover stopped and program exiting... ")
            self.controller.shutdown_rover()

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

        self.controller.set_mode(self.locomotion_mode)
        self.get_logger().info(f"Locomotion mode set to {self.locomotion_mode.name}")

    def command_callback(self, msg):
        command = msg.data.strip().lower()

        if not self.active:
            self.get_logger().warn("Ignoring command because rover is not launched")
            return

        # Implement missing command handling logic here, e.g.:
        if command == "forward":
            self.controller.forward()
            self.get_logger().info("Moving forward")

        elif command == "backward":
            self.controller.backward()
            self.get_logger().info("Moving backward")

        elif command == "stop":
            self.controller.stop()
            self.get_logger().info("Stopping rover")

        elif command == "left_turn":
            self.controller.set_all_steering(90 - 45)  # Example angle, adjust as needed
            self.get_logger().info("Turning left")

        elif command == "right_turn":
            self.controller.set_all_steering(90 + 45)  # Example angle, adjust as needed
            self.get_logger().info("Turning right")

        elif command == "reset_steering":
            self.controller.set_all_steering(90)
            self.get_logger().info("Resetting steering")

        elif command == "set_wheel_steering": 
            self.controller.set_wheel_steering(LocomotionController.FR, 90) 
            self.get_logger().info("Setting front right wheel servo to 90 degrees")

        else:
            self.get_logger().warn(f"Unknown command: {command}")


def main(args=None):
    rclpy.init(args=args)

    main_logic = MainLogicNode()

    try:
        rclpy.spin(main_logic)
    finally:
        main_logic.controller.stop()
        main_logic.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()