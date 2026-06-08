import rclpy 
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException

import math
import time
import board
import busio
import adafruit_mpu6050

from std_msgs.msg import String

from sensor_msgs.msg import Imu
from geometry_msgs.msg import Vector3
from geometry_msgs.msg import Quaternion

class ImuSensorNode(Node):
    def __init__(self):
        super().__init__("imu_sensor_node")

        # For calibration
        self.gyro_bias = {}
        self.accel_bias = {}
        self.calibrated = False

        # callback for shutdown
        self.create_subscription( 
            String,
            "/rover/system_shutdown",
            self.shutdown_callback,
            10
        )

        self.get_logger().info("IMU sensor node started")

        self.declare_parameter("addresses", [0x68, 0x69])
        self.declare_parameter("publish_rate_hz", 10.0)
        self.declare_parameter("estimate_orientation", True)
        self.declare_parameter("orientation_filter_alpha", 0.98)
    
        addresses = [int(a) for a in self.get_parameter("addresses").value]
        rate = float(self.get_parameter("publish_rate_hz").value)
        self.estimate_orientation = bool(
            self.get_parameter("estimate_orientation").value
        )
        self.orientation_filter_alpha = float(
            self.get_parameter("orientation_filter_alpha").value
        )
        if rate <= 0:
            self.get_logger().warning(
                f"publish_rate_hz={rate} is invalid, falling back to 50.0 Hz"
            )
            rate = 30.0 #40
        if not 0.0 <= self.orientation_filter_alpha <= 1.0:
            self.get_logger().warning(
                "orientation_filter_alpha must be between 0.0 and 1.0, "
                "falling back to 0.98"
            )
            self.orientation_filter_alpha = 0.98

        self.i2c = busio.I2C(board.SCL, board.SDA)

        self.imus = {}
        self.imu_publishers = {}
        self.orientation_states = {}

        for addr in addresses:
            self.imus[addr] = adafruit_mpu6050.MPU6050(self.i2c, address=addr)
            topic_name = f"sensors/imu_{addr:x}"
            self.imu_publishers[addr] = self.create_publisher(Imu, topic_name, 10)
            self.orientation_states[addr] = {
                "roll": 0.0,
                "pitch": 0.0,
                "yaw": 0.0,
                "last_stamp": None,
            }

        # Calibrate all IMUs before publishing
        self.imu_calibration()

        # Start publishing after calibration completes
        self.timer = self.create_timer(
        1.0 / rate,
        self.publish_imus
        )

    def publish_imus(self):
        for addr, imu in self.imus.items():
            ax, ay, az = imu.acceleration
            gx, gy, gz = imu.gyro

            if self.calibrated:
                bx, by, bz = self.gyro_bias[addr]
                gx -= bx
                gy -= by
                gz -= bz

                bax, bay, baz = self.accel_bias[addr]
                ax -= bax
                ay -= bay
                az -= baz

            # self.get_logger().info(f"acceleration: {ax, ay, az}")
            # self.get_logger().info(f"gyro: {gx, gy, gz}")


            msg = Imu()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = f"imu_{addr:x}"

            msg.linear_acceleration = Vector3(x=ax, y=ay, z=az)
            msg.angular_velocity = Vector3(x=gx, y=gy, z=gz)

            if self.estimate_orientation:
                msg.orientation = self.estimate_orientation_from_imu(
                    addr, ax, ay, az, gx, gy, gz
                )
                 self.get_logger().info(f"Estimated orientatio x {msg.orientation.x}")
                 self.get_logger().info(f"Estimated orientation y {msg.orientation.y}")
                 self.get_logger().info(f"Estimated orientation z {msg.orientation.z}")
                 self.get_logger().info(f"Estimated orientation w {msg.orientation.w}")



                self.set_covariances(msg)
            else:
                msg.orientation_covariance[0] = -1.0

            self.imu_publishers[addr].publish(msg)

    def estimate_orientation_from_imu(self, addr, ax, ay, az, gx, gy, gz):
        now = self.get_clock().now()
        state = self.orientation_states[addr]

        last_stamp = state["last_stamp"]
        state["last_stamp"] = now

        if last_stamp is None:
            dt = 0.0
        else:
            dt = (now - last_stamp).nanoseconds / 1e9
            if dt < 0.0 or dt > 1.0:
                dt = 0.0

        accel_norm = math.sqrt(ax * ax + ay * ay + az * az)
        if accel_norm > 0.0:
            accel_roll = math.atan2(ay, az)
            accel_pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az))
        else:
            accel_roll = state["roll"]
            accel_pitch = state["pitch"]

        gyro_roll = state["roll"] + gx * dt
        gyro_pitch = state["pitch"] + gy * dt
        gyro_yaw = state["yaw"] + gz * dt

        alpha = self.orientation_filter_alpha if dt > 0.0 else 0.0
        state["roll"] = alpha * gyro_roll + (1.0 - alpha) * accel_roll
        state["pitch"] = alpha * gyro_pitch + (1.0 - alpha) * accel_pitch
        state["yaw"] = self.normalize_angle(gyro_yaw)

        return self.quaternion_from_euler(
            state["roll"],
            state["pitch"],
            state["yaw"],
        )

    def set_covariances(self, msg):
        msg.orientation_covariance = [
            0.05, 0.0, 0.0,
            0.0, 0.05, 0.0,
            0.0, 0.0, 999.0,
        ]
        msg.angular_velocity_covariance = [
            0.01, 0.0, 0.0,
            0.0, 0.01, 0.0,
            0.0, 0.0, 0.01,
        ]
        msg.linear_acceleration_covariance = [
            0.1, 0.0, 0.0,
            0.0, 0.1, 0.0,
            0.0, 0.0, 0.1,
        ]

    @staticmethod
    def normalize_angle(angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    @staticmethod
    def quaternion_from_euler(roll, pitch, yaw):
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        return Quaternion(
            x=sr * cp * cy - cr * sp * sy,
            y=cr * sp * cy + sr * cp * sy,
            z=cr * cp * sy - sr * sp * cy,
            w=cr * cp * cy + sr * sp * sy,
        )

    def destroy_node(self):
        if hasattr(self, "i2c") and hasattr(self.i2c, "deinit"):
            self.i2c.deinit()
        super().destroy_node()
    
    def shutdown_callback(self, msg):
        if msg.data.strip().lower() == "shutdown":
            self.get_logger().info("Shutdown signal received. Shutting down IMU sensor node.")
            rclpy.shutdown()
            
    def imu_calibration(self, samples=500, delay=0.005):
        self.get_logger().info(
            "Waiting 2 seconds for IMUs to stabilize..."
            )
        time.sleep(2.0)

        self.get_logger().info(
            "Starting IMU calibration. Keep rover still."
        )

        for addr, imu in self.imus.items():
            gx_sum = gy_sum = gz_sum = 0.0
            ax_sum = ay_sum = az_sum = 0.0

            for _ in range(samples):
                ax, ay, az = imu.acceleration
                gx, gy, gz = imu.gyro

                ax_sum += ax
                ay_sum += ay
                az_sum += az

                gx_sum += gx
                gy_sum += gy
                gz_sum += gz

                time.sleep(delay)

            self.gyro_bias[addr] = (
                gx_sum / samples,
                gy_sum / samples,
                gz_sum / samples,
            )

            self.accel_bias[addr] = (
                ax_sum / samples,
                ay_sum / samples,
                (az_sum / samples) - 9.81  # remove gravity
            )

            self.get_logger().info(
                f"Calibration done for {hex(addr)}: "
                f"gyro={self.gyro_bias[addr]}, accel={self.accel_bias[addr]}"
            )

        for state in self.orientation_states.values():
            state["roll"] = 0.0
            state["pitch"] = 0.0
            state["yaw"] = 0.0
            state["last_stamp"] = None

        self.calibrated = True
        self.get_logger().info("IMU calibration complete.")



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
