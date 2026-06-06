import rclpy 
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException

import board
import busio
import adafruit_mpu6050

from std_msgs.msg import String

from sensor_msgs.msg import Imu
from geometry_msgs.msg import Vector3

class ImuSensorNode(Node):
    def __init__(self):
        super().__init__("imu_sensor_node")

        # callback for shutdown
        self.create_subscription( 
            String,
            "/rover/system_shutdown",
            self.shutdown_callback,
            10
        )

        self.get_logger().info("IMU sensor node started")

        self.declare_parameter("addresses", [0x68, 0x69])
        self.declare_parameter("publish_rate_hz", 50.0)
    
        addresses = [int(a) for a in self.get_parameter("addresses").value]
        rate = float(self.get_parameter("publish_rate_hz").value)
        if rate <= 0:
            self.get_logger().warning(
                f"publish_rate_hz={rate} is invalid, falling back to 50.0 Hz"
            )
            rate = 50.0

        self.i2c = busio.I2C(board.SCL, board.SDA)

        self.imus = {}
        self.imu_publishers = {}

        for addr in addresses:
            self.imus[addr] = adafruit_mpu6050.MPU6050(self.i2c, address=addr)
            topic_name = f"sensors/imu_{addr:x}"
            self.imu_publishers[addr] = self.create_publisher(Imu, topic_name, 10)

        self.timer = self.create_timer(1.0 / rate, self.publish_imus)

    def publish_imus(self):
        for addr, imu in self.imus.items():
            ax, ay, az = imu.acceleration
            gx, gy, gz = imu.gyro

            msg = Imu()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = f"imu_{addr:x}"

            msg.linear_acceleration = Vector3(x=ax, y=ay, z=az)
            msg.angular_velocity = Vector3(x=gx, y=gy, z=gz)

            # orientation is not estimated in this node right now, maybe add or overkill?
            msg.orientation_covariance[0] = -1.0

            self.imu_publishers[addr].publish(msg)

    def destroy_node(self):
        if hasattr(self, "i2c") and hasattr(self.i2c, "deinit"):
            self.i2c.deinit()
        super().destroy_node()
    
    def shutdown_callback(self, msg):
        if msg.data.strip().lower() == "shutdown":
            self.get_logger().info("Shutdown signal received. Shutting down IMU sensor node.")
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = ImuSensorNode()

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
