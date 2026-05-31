from enum import Enum

import rclpy
from rclpy.node import Node
from adafruit_servokit import ServoKit


class LocomotionModes(Enum):
    ACKERMANN = 0
    POINT_TURN = 1
    CRABBING = 2

class SteeringServos(Enum):
    FL = 6
    FR = 9
    CL = 7
    CR = 10
    RL = 8
    RR = 11

class LocomotionController(Node):
    def __init__(self):
        super().__init__("locomotion_controller")

        self.kit = ServoKit(channels=16)

        self.drive_motors_left = [self.kit.continuous_servo[i] for i in range(3)]
        self.drive_motors_right = [self.kit.continuous_servo[i] for i in range(3, 6)]
        self.steering_servos = [self.kit.servo[i] for i in range(6, 12)]

        self.mode = LocomotionModes.ACKERMANN

        self.STOP = -1
        self.LEFT_FORWARD = 0
        self.LEFT_BACKWARD = 1
        self.RIGHT_FORWARD = 1
        self.RIGHT_BACKWARD = 0

        self.get_logger().info("Locomotion controller started")

    def set_mode(self, mode: LocomotionModes):
        self.mode = mode
        self.get_logger().info(f"Set locomotion mode to: {mode.name}")

    def get_mode(self):
        return self.mode

    def set_drive(self, left_speed, right_speed):
        for motor in self.drive_motors_left:
            motor.throttle = left_speed

        for motor in self.drive_motors_right:
            motor.throttle = right_speed

    def stop(self):
        self.get_logger().info("Stopping rover")
        self.set_drive(self.STOP, self.STOP)

    def forward(self):
        self.get_logger().info("Moving forward")
        self.set_drive(self.LEFT_FORWARD, self.RIGHT_FORWARD)

    def backward(self):
        self.get_logger().info("Moving backward")
        self.set_drive(self.LEFT_BACKWARD, self.RIGHT_BACKWARD)

    def set_all_steering(self, angle):
        for servo in self.steering_servos:
            servo.angle = angle

    def set_wheel_steering(self, wheel_index, angle):
        self.kit.servo[wheel_index].angle = angle

    def ackermann(self, steering_angle):
        self.get_logger().info(f"Ackermann steering: {steering_angle}")
        self.set_all_steering(90 + steering_angle)

    def point_turn(self):
        self.get_logger().info("Point turn mode")
        angles = [45, 135, 90, 90, 135, 45]
        for servo, angle in zip(self.steering_servos, angles):
            servo.angle = angle

    def crabbing(self, angle):
        self.get_logger().info(f"Crabbing angle: {angle}")
        self.set_all_steering(90 + angle)

    def shutdown_rover(self):
        self.controller.stop()
        self.get_logger().info("Shutting down rover")
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)

    node = LocomotionController()

    try:
        rclpy.spin(node)
    finally:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()