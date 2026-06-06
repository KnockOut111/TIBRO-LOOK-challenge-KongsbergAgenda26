import math
import random

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String

try:
    import numpy as np
    import pyrealsense2 as rs

    REALSENSE_AVAILABLE = True
except ImportError:
    np = None
    rs = None
    REALSENSE_AVAILABLE = False


class DepthCameraNode(Node):
    def __init__(self):
        super().__init__("depth_camera_node")

        self.declare_parameter("frame_id", "depth_camera")
        self.declare_parameter("publish_rate_hz", 5.0)
        self.declare_parameter("demo_mode", not REALSENSE_AVAILABLE)
        self.declare_parameter("width", 640)
        self.declare_parameter("height", 480)
        self.declare_parameter("fps", 30)
        self.declare_parameter("horizontal_fov_deg", 75.0)
        self.declare_parameter("vertical_fov_deg", 50.0)
        self.declare_parameter("min_range_m", 0.2)
        self.declare_parameter("max_range_m", 6.0)
        self.declare_parameter("obstacle_stop_distance_m", 0.8)
        self.declare_parameter("center_window_deg", 20.0)
        self.declare_parameter("column_step", 8)
        self.declare_parameter("row_step", 12)
        self.declare_parameter("publish_sensor_msg", True)

        self.frame_id = self.get_parameter("frame_id").value
        self.demo_mode = bool(self.get_parameter("demo_mode").value)
        self.width = int(self.get_parameter("width").value)
        self.height = int(self.get_parameter("height").value)
        self.fps = int(self.get_parameter("fps").value)
        self.horizontal_fov = math.radians(
            float(self.get_parameter("horizontal_fov_deg").value)
        )
        self.vertical_fov = math.radians(
            float(self.get_parameter("vertical_fov_deg").value)
        )
        self.min_range = float(self.get_parameter("min_range_m").value)
        self.max_range = float(self.get_parameter("max_range_m").value)
        self.obstacle_stop_distance = float(
            self.get_parameter("obstacle_stop_distance_m").value
        )
        self.center_window = math.radians(
            float(self.get_parameter("center_window_deg").value)
        )
        self.column_step = max(1, int(self.get_parameter("column_step").value))
        self.row_step = max(1, int(self.get_parameter("row_step").value))
        self.publish_sensor_msg = bool(self.get_parameter("publish_sensor_msg").value)

        publish_rate = float(self.get_parameter("publish_rate_hz").value)
        if publish_rate <= 0.0:
            self.get_logger().warning(
                f"publish_rate_hz={publish_rate} is invalid, falling back to 5.0 Hz"
            )
            publish_rate = 5.0

        self.pipeline = None
        if not self.demo_mode:
            self.start_realsense()
        else:
            self.get_logger().warning("Depth camera running in demo mode")

        self.scan_pub = self.create_publisher(LaserScan, "/sensors/depth_scan", 10)
        self.sensor_msg_pub = None
        if self.publish_sensor_msg:
            self.sensor_msg_pub = self.create_publisher(String, "/rover/sensorMsg", 10)
        self.create_subscription(
            String,
            "/rover/system_shutdown",
            self.shutdown_callback,
            10,
        )

        self.demo_tick = 0
        self.last_path_state = None
        self.timer = self.create_timer(1.0 / publish_rate, self.publish_depth_scan)
        self.get_logger().info("Depth camera node started")

    def start_realsense(self):
        try:
            self.pipeline = rs.pipeline()
            cfg = rs.config()
            cfg.enable_stream(
                rs.stream.depth,
                self.width,
                self.height,
                rs.format.z16,
                self.fps,
            )
            self.pipeline.start(cfg)
            for _ in range(15):
                self.pipeline.wait_for_frames()
            self.get_logger().info("RealSense depth stream started")
        except Exception as exc:
            self.get_logger().error(
                f"Could not start RealSense depth stream, using demo mode: {exc}"
            )
            self.demo_mode = True
            self.pipeline = None

    def publish_depth_scan(self):
        if self.demo_mode:
            ranges = self.make_demo_ranges()
        else:
            ranges = self.capture_realsense_ranges()

        if not ranges:
            return

        scan = LaserScan()
        scan.header.stamp = self.get_clock().now().to_msg()
        scan.header.frame_id = self.frame_id
        scan.angle_min = -self.horizontal_fov / 2.0
        scan.angle_max = self.horizontal_fov / 2.0
        scan.angle_increment = self.horizontal_fov / (len(ranges) - 1)
        scan.time_increment = 0.0
        scan.scan_time = 0.0
        scan.range_min = self.min_range
        scan.range_max = self.max_range
        scan.ranges = ranges
        self.scan_pub.publish(scan)

        if self.publish_sensor_msg:
            self.publish_obstacle_state(scan)

    def capture_realsense_ranges(self):
        try:
            frames = self.pipeline.wait_for_frames(timeout_ms=1000)
            depth_frame = frames.get_depth_frame()
            if not depth_frame:
                self.get_logger().warning("No depth frame received")
                return []

            ranges = []
            y_values = range(0, self.height, self.row_step)

            for x in range(0, self.width, self.column_step):
                horizontal_angle = ((x / (self.width - 1)) - 0.5) * self.horizontal_fov
                valid_distances = []

                for y in y_values:
                    distance = depth_frame.get_distance(x, y)
                    if not self.min_range < distance < self.max_range:
                        continue

                    vertical_angle = ((y / (self.height - 1)) - 0.5) * self.vertical_fov
                    horizontal_distance = distance * math.cos(vertical_angle)
                    valid_distances.append(horizontal_distance)

                if valid_distances:
                    ranges.append(float(np.median(valid_distances)))
                else:
                    ranges.append(float("inf"))

            return ranges
        except Exception as exc:
            self.get_logger().error(f"Depth capture failed: {exc}")
            return []

    def make_demo_ranges(self):
        ranges = []
        count = max(2, self.width // self.column_step)
        moving_obstacle_angle = math.radians(25.0 * math.sin(self.demo_tick * 0.2))
        for i in range(count):
            angle = -self.horizontal_fov / 2.0 + self.horizontal_fov * i / (count - 1)
            wall_distance = self.max_range
            if abs(angle - moving_obstacle_angle) < math.radians(8.0):
                wall_distance = 1.1 + 0.15 * math.sin(self.demo_tick * 0.3)
            ranges.append(max(self.min_range, wall_distance + random.gauss(0.0, 0.02)))
        self.demo_tick += 1
        return ranges

    def publish_obstacle_state(self, scan):
        center_ranges = []
        angle = scan.angle_min
        for distance in scan.ranges:
            if abs(angle) <= self.center_window / 2.0 and math.isfinite(distance):
                center_ranges.append(distance)
            angle += scan.angle_increment

        center_distance = min(center_ranges) if center_ranges else float("inf")
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

    def shutdown_callback(self, msg):
        if msg.data.strip().lower() == "shutdown":
            self.get_logger().info("Shutdown signal received")
            rclpy.shutdown()

    def destroy_node(self):
        if self.pipeline is not None:
            self.pipeline.stop()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DepthCameraNode()

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
