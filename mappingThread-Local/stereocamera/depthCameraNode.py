import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String


class DepthObstacleNode(Node):
    def __init__(self):
        super().__init__("depth_obstacle_node")

        self.declare_parameter("scan_topic", "/sensors/depth_scan")
        self.declare_parameter("obstacle_topic", "/rover/sensorMsg")
        self.declare_parameter("obstacle_stop_distance_m", 0.8)
        self.declare_parameter("clear_distance_m", 1.0)
        self.declare_parameter("center_window_deg", 20.0)
        self.declare_parameter("min_valid_points", 3)
        self.declare_parameter("print_distance_period_s", 1.0)

        scan_topic = self.get_parameter("scan_topic").value
        obstacle_topic = self.get_parameter("obstacle_topic").value
        self.obstacle_stop_distance = float(
            self.get_parameter("obstacle_stop_distance_m").value
        )
        self.clear_distance = float(self.get_parameter("clear_distance_m").value)
        self.center_window = math.radians(
            float(self.get_parameter("center_window_deg").value)
        )
        self.min_valid_points = int(self.get_parameter("min_valid_points").value)
        self.print_distance_period = float(
            self.get_parameter("print_distance_period_s").value
        )
        self.last_path_state = None
        self.last_distance_print_time = self.get_clock().now()

        if self.clear_distance < self.obstacle_stop_distance:
            self.get_logger().warning(
                "clear_distance_m should be >= obstacle_stop_distance_m; "
                "using obstacle_stop_distance_m for both"
            )
            self.clear_distance = self.obstacle_stop_distance

        self.sensor_msg_pub = self.create_publisher(String, obstacle_topic, 10)
        self.create_subscription(LaserScan, scan_topic, self.scan_callback, 10)
        self.create_subscription(
            String,
            "/rover/system_shutdown",
            self.shutdown_callback,
            10,
        )

        self.get_logger().info(
            f"Depth obstacle node started, listening on {scan_topic}"
        )

    def scan_callback(self, scan):
        center_ranges = []
        angle = scan.angle_min
        for distance in scan.ranges:
            if (
                abs(angle) <= self.center_window / 2.0
                and math.isfinite(distance)
                and scan.range_min <= distance <= scan.range_max
            ):
                center_ranges.append(distance)
            angle += scan.angle_increment

        if len(center_ranges) < self.min_valid_points:
            self.get_logger().warning(
                f"Not enough valid center scan points: {len(center_ranges)}"
            )
            return

        center_distance = min(center_ranges)
        self.print_center_distance(center_distance, len(center_ranges))
        if self.last_path_state == "obstacle_detected":
            path_state = (
                "clear_path"
                if center_distance > self.clear_distance
                else "obstacle_detected"
            )
        else:
            path_state = (
                "obstacle_detected"
                if center_distance < self.obstacle_stop_distance
                else "clear_path"
            )

        if path_state != self.last_path_state:
            msg = String()
            msg.data = path_state
            self.sensor_msg_pub.publish(msg)
            self.last_path_state = path_state
            self.get_logger().info(
                f"{path_state}: center distance {center_distance:.2f} m"
            )

    def print_center_distance(self, center_distance, valid_points):
        if self.print_distance_period <= 0.0:
            return

        now = self.get_clock().now()
        elapsed = (now - self.last_distance_print_time).nanoseconds / 1e9
        if elapsed < self.print_distance_period:
            return

        self.last_distance_print_time = now
        self.get_logger().info(
            f"center distance: {center_distance:.2f} m "
            f"({valid_points} valid scan points)"
        )

    def shutdown_callback(self, msg):
        if msg.data.strip().lower() == "shutdown":
            self.get_logger().info("Shutdown signal received")
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = DepthObstacleNode()

    try:
        rclpy.spin(node)
    except (ExternalShutdownException, KeyboardInterrupt):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
