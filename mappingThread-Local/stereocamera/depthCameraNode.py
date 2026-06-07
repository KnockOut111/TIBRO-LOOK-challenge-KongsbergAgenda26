import math

import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, Image, LaserScan
from std_msgs.msg import String


class DepthObstacleNode(Node):
    def __init__(self):
        super().__init__("depth_obstacle_node")

        self.declare_parameter(
            "depth_image_topic",
            "/camera/camera/depth/image_rect_raw",
        )
        self.declare_parameter(
            "camera_info_topic",
            "/camera/camera/depth/camera_info",
        )
        self.declare_parameter("scan_topic", "/sensors/depth_scan")
        self.declare_parameter("obstacle_topic", "/rover/sensorMsg")
        self.declare_parameter("obstacle_stop_distance_m", 0.8)
        self.declare_parameter("clear_distance_m", 1.0)
        self.declare_parameter("center_window_deg", 20.0)
        self.declare_parameter("scan_height_px", 20)
        self.declare_parameter("column_step", 4)
        self.declare_parameter("range_min_m", 0.2)
        self.declare_parameter("range_max_m", 6.0)
        self.declare_parameter("min_valid_points", 3)
        self.declare_parameter("print_distance_period_s", 1.0)
        self.declare_parameter("waiting_log_period_s", 2.0)

        depth_image_topic = self.get_parameter("depth_image_topic").value
        camera_info_topic = self.get_parameter("camera_info_topic").value
        scan_topic = self.get_parameter("scan_topic").value
        obstacle_topic = self.get_parameter("obstacle_topic").value

        self.obstacle_stop_distance = float(
            self.get_parameter("obstacle_stop_distance_m").value
        )
        self.clear_distance = float(self.get_parameter("clear_distance_m").value)
        self.center_window = math.radians(
            float(self.get_parameter("center_window_deg").value)
        )
        self.scan_height_px = max(1, int(self.get_parameter("scan_height_px").value))
        self.column_step = max(1, int(self.get_parameter("column_step").value))
        self.range_min = float(self.get_parameter("range_min_m").value)
        self.range_max = float(self.get_parameter("range_max_m").value)
        self.min_valid_points = int(self.get_parameter("min_valid_points").value)
        self.print_distance_period = float(
            self.get_parameter("print_distance_period_s").value
        )
        self.waiting_log_period = float(
            self.get_parameter("waiting_log_period_s").value
        )

        if self.clear_distance < self.obstacle_stop_distance:
            self.get_logger().warning(
                "clear_distance_m should be >= obstacle_stop_distance_m; "
                "using obstacle_stop_distance_m for both"
            )
            self.clear_distance = self.obstacle_stop_distance

        self.camera_info = None
        self.last_path_state = None
        self.last_depth_time = None
        self.last_camera_info_time = None
        self.last_distance_print_time = self.get_clock().now()
        self.last_waiting_log_time = self.get_clock().now()

        self.scan_pub = self.create_publisher(LaserScan, scan_topic, 10)
        self.sensor_msg_pub = self.create_publisher(String, obstacle_topic, 10)
        self.create_subscription(
            CameraInfo,
            camera_info_topic,
            self.camera_info_callback,
            qos_profile_sensor_data,
        )
        self.create_subscription(
            Image,
            depth_image_topic,
            self.depth_image_callback,
            qos_profile_sensor_data,
        )
        self.create_subscription(
            String,
            "/rover/system_shutdown",
            self.shutdown_callback,
            10,
        )
        self.create_timer(0.5, self.watchdog_callback)

        self.get_logger().info(
            "Depth obstacle node started, listening on "
            f"{depth_image_topic} and {camera_info_topic}"
        )

    def camera_info_callback(self, msg):
        self.camera_info = msg
        self.last_camera_info_time = self.get_clock().now()

    def depth_image_callback(self, msg):
        self.last_depth_time = self.get_clock().now()
        if self.camera_info is None:
            self.get_logger().warning("Waiting for camera info")
            return

        depth = self.depth_image_to_array(msg)
        if depth is None:
            return

        scan = self.depth_array_to_scan(depth, msg.header)
        if scan is None:
            return

        self.scan_pub.publish(scan)
        self.publish_obstacle_state(scan)

    def depth_image_to_array(self, msg):
        height = msg.height
        width = msg.width

        if msg.encoding == "16UC1":
            dtype = np.uint16
            scale = 0.001
        elif msg.encoding == "32FC1":
            dtype = np.float32
            scale = 1.0
        else:
            self.get_logger().error(f"Unsupported depth encoding: {msg.encoding}")
            return None

        row_stride = msg.step // np.dtype(dtype).itemsize
        depth = np.frombuffer(msg.data, dtype=dtype)
        if depth.size < row_stride * height:
            self.get_logger().error("Depth image data is smaller than expected")
            return None

        depth = depth.reshape((height, row_stride))[:, :width].astype(np.float32)
        depth *= scale
        return depth

    def depth_array_to_scan(self, depth, header):
        height, width = depth.shape
        fx = float(self.camera_info.k[0])
        cx = float(self.camera_info.k[2])
        if fx <= 0.0:
            self.get_logger().error("Invalid camera_info fx")
            return None

        center_row = height // 2
        half_scan_height = self.scan_height_px // 2
        row_start = max(0, center_row - half_scan_height)
        row_end = min(height, center_row + half_scan_height + 1)

        columns = list(range(0, width, self.column_step))
        ranges = []
        angles = []

        for col in columns:
            samples = depth[row_start:row_end, col]
            valid = samples[
                np.isfinite(samples)
                & (samples >= self.range_min)
                & (samples <= self.range_max)
            ]

            if valid.size:
                ranges.append(float(np.median(valid)))
            else:
                ranges.append(float("inf"))

            angles.append(math.atan2((col - cx), fx))

        if len(ranges) < 2:
            return None

        scan = LaserScan()
        scan.header = header
        scan.header.frame_id = self.camera_info.header.frame_id or header.frame_id
        scan.angle_min = angles[0]
        scan.angle_max = angles[-1]
        scan.angle_increment = (angles[-1] - angles[0]) / (len(angles) - 1)
        scan.time_increment = 0.0
        scan.scan_time = 0.0
        scan.range_min = self.range_min
        scan.range_max = self.range_max
        scan.ranges = ranges
        return scan

    def publish_obstacle_state(self, scan):
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

    def watchdog_callback(self):
        if self.waiting_log_period <= 0.0:
            return

        now = self.get_clock().now()
        elapsed = (now - self.last_waiting_log_time).nanoseconds / 1e9
        if elapsed < self.waiting_log_period:
            return

        if self.last_depth_time is None:
            self.last_waiting_log_time = now
            self.get_logger().warning("Waiting for RealSense depth image messages")
        elif self.last_camera_info_time is None:
            self.last_waiting_log_time = now
            self.get_logger().warning("Waiting for RealSense camera info messages")

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
