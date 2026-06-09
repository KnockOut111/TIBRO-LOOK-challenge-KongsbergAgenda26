# autonomous_simple_node.py

import math
import random
from enum import Enum, auto
from typing import Dict, Optional

import numpy as np
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, Imu
from std_msgs.msg import Bool, String

try:
    from adafruit_servokit import ServoKit
except ImportError as exc:
    ServoKit = None
    SERVO_IMPORT_ERROR = exc
else:
    SERVO_IMPORT_ERROR = None

try:
    from gpiozero import DigitalInputDevice
except ImportError as exc:
    DigitalInputDevice = None
    GPIO_IMPORT_ERROR = exc
else:
    GPIO_IMPORT_ERROR = None


TICK_PERIOD_S = 0.1
RAMP_PITCH_THRESHOLD_RAD = math.radians(10.0)
SCAN_DURATION_S = 8.0

RECOVERY_STOP_S = 1.0
RECOVERY_BACKUP_S = 2.0
RECOVERY_TURN_MIN_S = 1.5
RECOVERY_TURN_MAX_S = 3.0


class RoverState(Enum):
    IDLE = auto()
    STARTING = auto()
    SCANNING = auto()
    DRIVING = auto()
    RECOVERY = auto()
    STOPPED = auto()


class RecoveryState(Enum):
    STOPPING = auto()
    BACKING_UP = auto()
    TURNING = auto()


class SteeringServos(Enum):
    FL = 6
    CL = 7
    RL = 8
    FR = 9
    CR = 10
    RR = 11


class SimpleRoverNode(Node):
    def __init__(self) -> None:
        super().__init__("autonomous_simple_node")

        if ServoKit is None:
            raise RuntimeError(
                "adafruit_servokit is not installed on this machine."
            ) from SERVO_IMPORT_ERROR

        if DigitalInputDevice is None:
            raise RuntimeError(
                "gpiozero is not installed on this machine."
            ) from GPIO_IMPORT_ERROR

        self.kit = ServoKit(channels=16)

        self.drive_left = [self.kit.continuous_servo[i] for i in range(3)]
        self.drive_right = [self.kit.continuous_servo[i] for i in range(3, 6)]

        self.steering_neutral = {
            SteeringServos.FL: 90,
            SteeringServos.FR: 30,
            SteeringServos.CL: 105,
            SteeringServos.CR: 70,
            SteeringServos.RL: 100,
            SteeringServos.RR: 80,
        }

        self.state = RoverState.IDLE
        self.recovery_state: Optional[RecoveryState] = None
        self.state_entered_at = self.now_s()
        self.recovery_entered_at = self.now_s()
        self.turn_duration_s = RECOVERY_TURN_MIN_S

        self.is_armed = False
        self.latest_obstacle = "clear_path"
        self.last_obstacle_state = "clear_path"
        self.latest_imu_68: Optional[Imu] = None
        self.latest_imu_69: Optional[Imu] = None
        self.metal_count = 0

        self.declare_parameter("depth_topic", "/camera/camera/depth/image_rect_raw")
        self.declare_parameter("stop_distance_m", 0.8)
        self.declare_parameter("clear_distance_m", 1.0)
        self.declare_parameter("sample_radius_px", 10)

        self.stop_dist = float(self.get_parameter("stop_distance_m").value)
        self.clear_dist = float(self.get_parameter("clear_distance_m").value)
        self.radius = int(self.get_parameter("sample_radius_px").value)

        self.declare_parameter("metal_pins", [17, 22, 27])
        self.declare_parameter("metal_pull_up", False)
        self.declare_parameter("metal_publish_rate_hz", 10.0)
        self.declare_parameter("metal_detect_cooldown_s", 0.2)

        pins = [int(pin) for pin in self.get_parameter("metal_pins").value]
        pull_up = bool(self.get_parameter("metal_pull_up").value)
        self.metal_devices = {pin: DigitalInputDevice(pin, pull_up=pull_up) for pin in pins}
        self.metal_pin_publishers = {
            pin: self.create_publisher(Bool, f"metal_sensor/gpio{pin}", 10) for pin in pins
        }
        self.metal_pub = self.create_publisher(String, "metal_sensor/metal_detected", 10)
        self._any_pin_high = False
        self._last_detect_publish_s = 0.0
        self._detect_cooldown_s = float(self.get_parameter("metal_detect_cooldown_s").value)

        self.fsm_pub = self.create_publisher(String, "/rover/fsm_state", 10)
        self.command_pub = self.create_publisher(String, "/rover/command", 10)
        self.obstacle_pub = self.create_publisher(String, "/sensors/obstacle_state", 10)

        self.create_subscription(String, "/rover/mainMode", self.main_mode_callback, 10)
        self.create_subscription(
            String,
            "/autonomousController_node/start_autonomous_program",
            self.start_callback,
            10,
        )
        self.create_subscription(String, "/rover/system_shutdown", self.shutdown_callback, 10)
        self.create_subscription(Imu, "/sensors/imu_68", self.imu68_callback, 10)
        self.create_subscription(Imu, "/sensors/imu_69", self.imu69_callback, 10)
        self.create_subscription(
            Image,
            self.get_parameter("depth_topic").value,
            self.depth_callback,
            qos_profile_sensor_data,
        )

        self.create_timer(TICK_PERIOD_S, self.tick)

        metal_rate = float(self.get_parameter("metal_publish_rate_hz").value)
        metal_period = 1.0 / metal_rate if metal_rate > 0 else 0.1
        self.create_timer(metal_period, self.poll_metal)

        self.stop_motion()
        self.reset_steering()
        self.get_logger().info("Simple autonomous node started.")

    def now_s(self) -> float:
        return self.get_clock().now().nanoseconds / 1e9

    def elapsed_state(self) -> float:
        return self.now_s() - self.state_entered_at

    def elapsed_recovery(self) -> float:
        return self.now_s() - self.recovery_entered_at

    def transition(self, new_state: RoverState) -> None:
        self.state = new_state
        self.state_entered_at = self.now_s()
        self.recovery_state = None

        msg = String()
        msg.data = new_state.name
        self.fsm_pub.publish(msg)
        self.get_logger().info(f"FSM -> {new_state.name}")

    def set_recovery(self, new_state: RecoveryState) -> None:
        self.recovery_state = new_state
        self.recovery_entered_at = self.now_s()
        if new_state == RecoveryState.TURNING:
            self.turn_duration_s = random.uniform(RECOVERY_TURN_MIN_S, RECOVERY_TURN_MAX_S)

    def publish_command(self, text: str) -> None:
        msg = String()
        msg.data = text
        self.command_pub.publish(msg)

    def set_servo(self, wheel: SteeringServos, angle: int) -> None:
        angle = max(0, min(180, angle))
        self.kit.servo[wheel.value].angle = angle

    def reset_steering(self) -> None:
        for wheel, angle in self.steering_neutral.items():
            self.set_servo(wheel, angle)

    def point_turn_pose(self) -> None:
        target = {
            SteeringServos.FL: 140,
            SteeringServos.FR: 100,
            SteeringServos.CL: 90,
            SteeringServos.CR: 90,
            SteeringServos.RL: 40,
            SteeringServos.RR: 130,
        }
        for wheel, angle in target.items():
            self.set_servo(wheel, angle)

    def set_drive(self, left: float, right: float) -> None:
        left = max(-1.0, min(1.0, left))
        right = max(-1.0, min(1.0, right))

        for motor in self.drive_left:
            motor.throttle = left
        for motor in self.drive_right:
            motor.throttle = right

    def stop_motion(self) -> None:
        self.set_drive(0.0, 0.0)
        self.publish_command("stop")

    def forward(self) -> None:
        self.reset_steering()
        self.set_drive(1.0, -1.0)
        self.publish_command("forward")

    def backward(self) -> None:
        self.reset_steering()
        self.set_drive(-1.0, 1.0)
        self.publish_command("backward")

    def point_turn_left(self) -> None:
        self.point_turn_pose()
        self.set_drive(-1.0, 1.0)
        self.publish_command("left_turn")

    def point_turn_right(self) -> None:
        self.point_turn_pose()
        self.set_drive(1.0, -1.0)
        self.publish_command("right_turn")

    def imu68_callback(self, msg: Imu) -> None:
        self.latest_imu_68 = msg

    def imu69_callback(self, msg: Imu) -> None:
        self.latest_imu_69 = msg

    def current_pitch(self) -> Optional[float]:
        imu = self.latest_imu_68 or self.latest_imu_69
        if imu is None:
            return None

        q = imu.orientation
        if q.x == 0.0 and q.y == 0.0 and q.z == 0.0 and q.w == 0.0:
            return None

        sinp = 2.0 * (q.w * q.y - q.z * q.x)
        if sinp >= 1.0:
            return math.pi / 2.0
        if sinp <= -1.0:
            return -math.pi / 2.0
        return math.asin(sinp)

    def depth_callback(self, msg: Image) -> None:
        try:
            if msg.encoding == "16UC1":
                depth = (
                    np.frombuffer(msg.data, np.uint16)
                    .reshape(msg.height, msg.width)
                    .astype(np.float32)
                    * 0.001
                )
            elif msg.encoding == "32FC1":
                depth = np.frombuffer(msg.data, np.float32).reshape(msg.height, msg.width)
            else:
                self.get_logger().error(f"Unsupported depth encoding: {msg.encoding}")
                return
        except ValueError as exc:
            self.get_logger().error(f"Depth image error: {exc}")
            return

        cy, cx = msg.height // 2, msg.width // 2
        r = self.radius
        y0 = max(0, cy - r)
        y1 = min(msg.height, cy + r)
        x0 = max(0, cx - r)
        x1 = min(msg.width, cx + r)

        patch = depth[y0:y1, x0:x1]
        valid = patch[(patch > 0.1) & (patch < 10.0)]

        if valid.size == 0:
            return

        distance = float(np.median(valid))

        if self.last_obstacle_state == "obstacle_detected":
            state = "clear_path" if distance > self.clear_dist else "obstacle_detected"
        else:
            state = "obstacle_detected" if distance < self.stop_dist else "clear_path"

        self.latest_obstacle = state

        if state != self.last_obstacle_state:
            out = String()
            out.data = state
            self.obstacle_pub.publish(out)
            self.last_obstacle_state = state
            self.get_logger().info(f"Obstacle: {state} ({distance:.2f} m)")

    def poll_metal(self) -> None:
        any_high = False

        for pin, dev in self.metal_devices.items():
            value = bool(dev.value)

            pin_msg = Bool()
            pin_msg.data = value
            self.metal_pin_publishers[pin].publish(pin_msg)

            if value:
                any_high = True

        now = self.now_s()
        if any_high and not self._any_pin_high and (now - self._last_detect_publish_s) >= self._detect_cooldown_s:
            self.metal_count += 1
            msg = String()
            msg.data = "metal_detected"
            self.metal_pub.publish(msg)
            self._last_detect_publish_s = now
            self.get_logger().info(f"Metal detected: {self.metal_count}")

        self._any_pin_high = any_high

    def main_mode_callback(self, msg: String) -> None:
        mode = msg.data.strip().lower()
        if mode == "arm":
            self.is_armed = True
            self.get_logger().info("Armed")
        elif mode == "quit":
            self.is_armed = False
            self.transition(RoverState.STOPPED)

    def start_callback(self, msg: String) -> None:
        if msg.data.strip() != "start_autonomous_system":
            return
        if not self.is_armed:
            self.get_logger().warn("Ignored start: not armed")
            return
        if self.state != RoverState.IDLE:
            self.get_logger().warn("Ignored start: not in IDLE")
            return
        self.transition(RoverState.STARTING)

    def shutdown_callback(self, msg: String) -> None:
        if msg.data.strip().lower() == "shutdown":
            self.get_logger().info("Shutdown received")
            rclpy.shutdown()

    def tick(self) -> None:
        if self.state == RoverState.IDLE:
            self.stop_motion()

        elif self.state == RoverState.STARTING:
            pitch = self.current_pitch()
            if pitch is None:
                self.forward()
            elif abs(pitch) > RAMP_PITCH_THRESHOLD_RAD:
                self.forward()
            else:
                self.stop_motion()
                self.transition(RoverState.SCANNING)

        elif self.state == RoverState.SCANNING:
            if self.elapsed_state() < SCAN_DURATION_S:
                self.point_turn_left()
            else:
                self.stop_motion()
                self.transition(RoverState.DRIVING)

        elif self.state == RoverState.DRIVING:
            if self.latest_obstacle == "obstacle_detected":
                self.transition(RoverState.RECOVERY)
                self.set_recovery(RecoveryState.STOPPING)
            else:
                self.forward()

        elif self.state == RoverState.RECOVERY:
            if self.recovery_state is None:
                self.set_recovery(RecoveryState.STOPPING)

            if self.recovery_state == RecoveryState.STOPPING:
                self.stop_motion()
                if self.elapsed_recovery() >= RECOVERY_STOP_S:
                    self.set_recovery(RecoveryState.BACKING_UP)

            elif self.recovery_state == RecoveryState.BACKING_UP:
                self.backward()
                if self.elapsed_recovery() >= RECOVERY_BACKUP_S:
                    self.set_recovery(RecoveryState.TURNING)

            elif self.recovery_state == RecoveryState.TURNING:
                self.point_turn_left()
                if self.elapsed_recovery() >= self.turn_duration_s:
                    self.latest_obstacle = "clear_path"
                    self.last_obstacle_state = "clear_path"
                    self.transition(RoverState.DRIVING)

        elif self.state == RoverState.STOPPED:
            self.stop_motion()

    def destroy_node(self):
        self.stop_motion()
        for dev in self.metal_devices.values():
            dev.close()
        super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SimpleRoverNode()

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