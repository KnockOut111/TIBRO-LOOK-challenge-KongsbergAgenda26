#!/usr/bin/env python3
# pyright: reportMissingImports=false

"""ROS 2 node that publishes the high/low state of GPIO 17, 22, and 27.

Each pin is treated as a digital input. The node publishes a Bool message for
each pin so other ROS 2 nodes can subscribe to the status independently.
"""

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException

from std_msgs.msg import String
from std_msgs.msg import Bool

try:
	from gpiozero import DigitalInputDevice
except ImportError as exc:
	DigitalInputDevice = None
	GPIO_IMPORT_ERROR = exc
else:
	GPIO_IMPORT_ERROR = None


class MetalSensorNode(Node):
	def __init__(self):
		super().__init__("metal_sensor_node")

		#Defining a callback for the shutdown topic 
		self.create_subscribtion( 
			String,
            "/rover/system_shutdown",
            self.shutdown_callback,
            10
        )

		self.get_logger().info("Metal sensor node started")

		self.declare_parameter("pins", [17, 22, 27])
		self.declare_parameter("publish_rate_hz", 10.0)
		self.declare_parameter("pull_up", False)

		pins = [int(pin) for pin in self.get_parameter("pins").value]
		publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
		pull_up = bool(self.get_parameter("pull_up").value)

		if DigitalInputDevice is None:
			raise RuntimeError(
				"gpiozero is not installed. Install it on the Raspberry Pi and retry."
			) from GPIO_IMPORT_ERROR

		self.devices = {}
		self.topic_publishers = {}

		for pin in pins:
			self.devices[pin] = DigitalInputDevice(pin, pull_up=pull_up)
			topic_name = f"metal_sensor/gpio{pin}"
			self.topic_publishers[pin] = self.create_publisher(Bool, topic_name, 10)

		timer_period = 1.0 / publish_rate_hz if publish_rate_hz > 0 else 0.1
		self.timer = self.create_timer(timer_period, self.publish_states)

		self.get_logger().info(
			f"Monitoring GPIO pins {pins} at {publish_rate_hz:.1f} Hz with pull_up={pull_up}"
		)

	def publish_states(self):
		for pin, device in self.devices.items():
			msg = Bool()
			msg.data = bool(device.value)
			self.topic_publishers[pin].publish(msg)

	def destroy_node(self):
		for device in self.devices.values():
			device.close()
		super().destroy_node()

	def shutdown_callback(self, msg):
		if msg.data.strip().lower() == "shutdown":
			self.get_logger().info("Shutdown signal received. Shutting down metal sensor node...")
			rclpy.shutdown()


def main():
	rclpy.init(args=args)
	node = MetalSensorNode()

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
