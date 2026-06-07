import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String


class DepthObstacleNode(Node):
    def __init__(self):
        super().__init__("depth_obstacle_node")

        self.declare_parameter("depth_topic", "/camera/camera/depth/image_rect_raw")
        self.declare_parameter("obstacle_topic", "/rover/sensorMsg")
        self.declare_parameter("stop_distance_m", 0.8)
        self.declare_parameter("clear_distance_m", 1.0)
        self.declare_parameter("sample_radius_px", 10)

        self.stop_dist = self.get_parameter("stop_distance_m").value
        self.clear_dist = self.get_parameter("clear_distance_m").value
        self.radius = self.get_parameter("sample_radius_px").value
        self.last_state = None

        self.pub = self.create_publisher(
            String, self.get_parameter("obstacle_topic").value, 10
        )
        self.create_subscription(
            Image,
            self.get_parameter("depth_topic").value,
            self.on_depth,
            qos_profile_sensor_data,
        )

    def on_depth(self, msg):
        if msg.encoding == "16UC1":
            depth = np.frombuffer(msg.data, np.uint16).reshape(msg.height, msg.width).astype(np.float32) * 0.001
        elif msg.encoding == "32FC1":
            depth = np.frombuffer(msg.data, np.float32).reshape(msg.height, msg.width)
        else:
            self.get_logger().error(f"Unsupported encoding: {msg.encoding}")
            return

        cy, cx = msg.height // 2, msg.width // 2
        r = self.radius
        patch = depth[cy - r : cy + r, cx - r : cx + r]
        valid = patch[(patch > 0.1) & (patch < 10.0)]

        if valid.size == 0:
            self.get_logger().warning("No valid depth in center patch")
            return

        distance = float(np.median(valid))
        self.get_logger().info(f"Center distance: {distance:.3f} m")

        if self.last_state == "obstacle_detected":
            state = "clear_path" if distance > self.clear_dist else "obstacle_detected"
        else:
            state = "obstacle_detected" if distance < self.stop_dist else "clear_path"

        if state != self.last_state:
            msg_out = String()
            msg_out.data = state
            self.pub.publish(msg_out)
            self.last_state = state
            self.get_logger().info(f"State change: {state} at {distance:.3f} m")


def main(args=None):
    rclpy.init(args=args)
    node = DepthObstacleNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()