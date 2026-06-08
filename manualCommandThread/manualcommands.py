# pil opp      -> forward
# pil ned      -> backward
# pil venstre  -> left_turn
# pil høyre    -> right_turn
# space        -> stop
# a            -> arm
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
        
        self.create_subscription(String, "/rover/system_shutdown", self.shutdown_callback, 10)

        self.get_logger().info("Manual command node running")
        self.get_logger().info("Controls: arrows = drive, space = stop, a = arm, q = quit")



    def publish_main_mode(self, command: str):
        msg = String()
        msg.data = command
        self.main_mode_pub.publish(msg)

    def publish_command(self, command: str):
        msg = String()
        msg.data = command
        self.command_pub.publish(msg)

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

    def run(self):
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
                self.get_logger().info("Armed")

            elif key == "q":
                self.publish_command("stop")
                self.publish_main_mode("quit")
                self.get_logger().info("Quit")
                break
        
    def shutdown_callback(self, msg):
        if msg.data.strip().lower() == "shutdown":
            self.get_logger().info("Shutdown signal received. Shutting down metal sensor node...")
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