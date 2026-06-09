# pil opp      -> forward
# pil ned      -> backward
# pil venstre  -> left_turn
# pil høyre    -> right_turn
# space        -> stop
# a            -> arm
# m            -> change locomotion mode
# q            -> quit

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import sys
import termios
import tty


class ManualCommandNode(Node):
    def __init__(self):
        super().__init__("manualCommand_node")

        self.main_mode_pub = self.create_publisher(String, "/rover/mainMode", 10)
        self.command_pub = self.create_publisher(String, "/rover/command", 10)
        self.loco_mode_pub = self.create_publisher(String, "/rover/locoMode", 10)

        self.create_subscription(String, "/rover/system_shutdown", self.shutdown_callback, 10)

        # Start in crabbing mode
        self.modes = ["crabbing", "point_turn"]
        self.mode_index = 0
        self.current_mode = self.modes[self.mode_index]

        self.get_logger().info("Manual command node running")
        self.get_logger().info("Controls: arrows = drive, space = stop, a = arm, m = mode, q = quit")
        self.get_logger().info(f"Starting locomotion mode: {self.current_mode}")

        self.calibration_wheels = ["FL", "FR", "CL", "CR", "RL", "RR"]
        self.selected_wheel_index = 0
        self.selected_wheel = self.calibration_wheels[self.selected_wheel_index]
        self.calibration_step = 1

    def publish_main_mode(self, command: str):
        msg = String()
        msg.data = command
        self.main_mode_pub.publish(msg)

    def publish_command(self, command: str):
        msg = String()
        msg.data = command
        self.command_pub.publish(msg)

    def publish_loco_mode(self, command: str):
        msg = String()
        msg.data = command
        self.loco_mode_pub.publish(msg)

    def get_key(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)

            if key == "\x1b":
                key += sys.stdin.read(2)

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        return key

    def change_mode(self):
        self.mode_index = (self.mode_index + 1) % len(self.modes)
        self.current_mode = self.modes[self.mode_index]

        self.publish_loco_mode(self.current_mode)
        self.get_logger().info(f"Changed locomotion mode to: {self.current_mode}")

    def run(self):
        # Set initial locomotion mode when node starts
        self.publish_loco_mode(self.current_mode)

        while rclpy.ok():
            key = self.get_key()

            if key == "\x1b[A":
                self.publish_command("forward")
                self.get_logger().info("Forward")

            elif key == "\x1b[B":
                self.publish_command("backward")
                self.get_logger().info("Backward")

            elif key == "\x1b[C":
                self.publish_command("right_turn")
                self.get_logger().info("Right turn")

            elif key == "\x1b[D":
                self.publish_command("left_turn")
                self.get_logger().info("Left turn")

            elif key == " ":
                self.publish_command("stop")
                self.get_logger().info("Stop")

            elif key == "a":
                self.publish_main_mode("arm")
                self.publish_loco_mode(self.current_mode)
                self.get_logger().info("Armed")

            elif key == "m":
                self.change_mode()

            elif key == "q":
                self.publish_command("stop")
                self.publish_main_mode("quit")
                self.get_logger().info("Quit")
                break

            elif key in ["1","2","3","4","5","6"]:
                self.selected_wheel_index = int(key)-1
                self.selected_wheel = self.calibration_wheels[self.selected_wheel_index]

                self.get_logger().info(
                    f"Selected wheel: {self.selected_wheel}"
                )


            elif key == "+":
                self.publish_command(
                    f"adjust_wheel_steering {self.selected_wheel} 1"
                )

                self.get_logger().info(
                    f"{self.selected_wheel} +1 degree"
                )


            elif key == "-":
                self.publish_command(
                    f"adjust_wheel_steering {self.selected_wheel} -1"
                )

                self.get_logger().info(
                    f"{self.selected_wheel} -1 degree"
                )


            elif key == "s":
                self.publish_command("update_steering")

                self.get_logger().info(
                    "Saved steering calibration"
                )


            elif key == "r":
                self.publish_command("reset_steering")

                self.get_logger().info(
                    "Reset steering"
                )

    def shutdown_callback(self, msg):
        if msg.data.strip().lower() == "shutdown":
            self.get_logger().info("Shutdown signal received. Shutting down manual command node...")
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)

    node = ManualCommandNode()

    try:
        node.run()
    except KeyboardInterrupt:
        node.publish_command("stop")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()