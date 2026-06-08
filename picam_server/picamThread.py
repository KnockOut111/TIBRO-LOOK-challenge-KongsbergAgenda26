#!/usr/bin/env python3

"""Raspberry Pi capture node for the TIBRO LOOK camera pipeline.

The Pi captures frames continuously at 5 Hz, stores every frame locally, keeps
the latest 100 captures in memory, and only publishes a compressed image when
the computer-side server requests one.
"""

import os
import sys
import time
import types
from collections import deque
from threading import Lock

import cv2
import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Empty, String


BASE_DIR = os.path.dirname(__file__)
LOCAL_PHOTO_DIR = os.path.join(BASE_DIR, "photos_rpi")
REQUEST_TOPIC = "/picam/request_capture"
IMAGE_TOPIC = "/picam/captured_image"


def get_camera():
    class MagicMock:
        def __getattr__(self, name):
            return self

    magic_instance = MagicMock()
    fake_kms = types.ModuleType("pykms")
    fake_kms.PixelFormat = magic_instance
    fake_kms.PixelFormats = magic_instance
    sys.modules["pykms"] = fake_kms
    sys.modules["kms"] = fake_kms

    from picamzero import Camera

    return Camera()


class PiCamThreadNode(Node):
    def __init__(self):
        super().__init__("picam_thread")

        self.declare_parameter("capture_rate_hz", 5.0)
        self.declare_parameter("buffer_size", 100)
        self.declare_parameter("storage_dir", LOCAL_PHOTO_DIR)

        self.capture_rate_hz = float(self.get_parameter("capture_rate_hz").value)
        self.buffer_size = int(self.get_parameter("buffer_size").value)
        self.storage_dir = str(self.get_parameter("storage_dir").value)

        if self.capture_rate_hz <= 0.0:
            self.get_logger().warning("capture_rate_hz must be > 0, falling back to 5.0 Hz")
            self.capture_rate_hz = 5.0
        if self.buffer_size <= 0:
            self.get_logger().warning("buffer_size must be > 0, falling back to 100")
            self.buffer_size = 100

        os.makedirs(self.storage_dir, exist_ok=True)

        self.camera = get_camera()
        self.frame_buffer = deque(maxlen=self.buffer_size)
        self.buffer_lock = Lock()

        self.capture_pub = self.create_publisher(CompressedImage, IMAGE_TOPIC, 10)
        self.create_subscription(Empty, REQUEST_TOPIC, self.request_callback, 10)
        self.create_subscription(String, "/rover/system_shutdown", self.shutdown_callback, 10)

        self.capture_timer = self.create_timer(1.0 / self.capture_rate_hz, self.capture_frame)
        self.get_logger().info(
            f"PiCam thread running at {self.capture_rate_hz:.1f} Hz, storing frames in {self.storage_dir}"
        )

    def capture_frame(self):
        try:
            frame = self.camera.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            timestamp_ms = int(time.time() * 1000)
            filename = f"picam_{timestamp_ms}.jpg"
            file_path = os.path.join(self.storage_dir, filename)

            success, encoded = cv2.imencode(".jpg", frame)
            if not success:
                raise RuntimeError("Failed to encode camera frame as JPEG")

            jpeg_bytes = encoded.tobytes()
            cv2.imwrite(file_path, frame)

            with self.buffer_lock:
                self.frame_buffer.append(
                    {
                        "timestamp_ms": timestamp_ms,
                        "filename": filename,
                        "file_path": file_path,
                        "jpeg_bytes": jpeg_bytes,
                    }
                )
        except Exception as exc:
            self.get_logger().error(f"Capture error: {exc}")

    def request_callback(self, _msg):
        with self.buffer_lock:
            if not self.frame_buffer:
                self.get_logger().warning("Capture requested before any frames were buffered")
                return

            latest = self.frame_buffer[-1]

        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "picam"
        msg.format = "jpeg"
        msg.data = latest["jpeg_bytes"]
        self.capture_pub.publish(msg)
        self.get_logger().info(f"Published {latest['filename']} to {IMAGE_TOPIC}")

    def shutdown_callback(self, msg):
        if msg.data.strip().lower() == "shutdown":
            self.get_logger().info("Shutdown signal received")
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = PiCamThreadNode()

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


if __name__ == "__main__":
    main()