 # Modes:
        # - Ackerman
        # - Point turn
        # - Crab steering

# Ackerman: steering is a conventional steering method where the wheels turn at different angles to achieve smooth and efficient forward turning, similar to a car.
# Point turn: allows the robot to rotate around its own center with little or no forward movement, enabling zero-radius turning.
# Crabbing: Crab steering aligns all wheels in the same direction, allowing the robot to move sideways or diagonally while maintaining its orientation.

print("Starting locomotion controller...")

from adafruit_servokit import ServoKit
from enum import Enum
import math
import rclpy
from rclpy.node import Node



class LocomotionModes(Enum):
    ACKERMANN = 0
    POINT_TURN = 1
    CRABBING = 2


# Get inspiration from https://github.com/esa-prl/ExoMy_Software/blob/master/src/rover.py

# class LocomotionController(Node):

    # def __init__(self):
    #     super().__init__('locomotion_controller') # Initialize the node with a name

    #     # Default Ackermann mode
    #     self.mode = LocomotionModes.ACKERMANN

    #     self.wheel_x = 12.0
    #     self.wheel_y = 20.0

    #     max_steering_angle = 45
    #     self.ackermann_r_min = abs(self.wheel_y) / math.tan(math.radians(max_steering_angle)) + self.wheel_x
    #     self.ackermann_r_max = 250

    #     self.kit = ServoKit(channels=16)
    #     self.left_engines = [self.kit.continuous_servo[i] for i in range(3)]
    #     self.right_engines = [self.kit.continuous_servo[i] for i in range(3, 6)]

    #     self.get_logger().info("Locomotion controller started")

        # Default Point turn mode


        # Default Crabbing mode


    # def set_mode(self, mode: LocomotionModes):
    #     if self.mode != mode:
    #         self.mode = mode
    #         self.get_logger().info(f"Set locomotion mode to: {mode.name}")



class LocomotionController:
    FL, FR, CL, CR, RL, RR = range(6)

    def __init__(self):
        super().__init__("locomotion_controller")

        self.kit = ServoKit(channels=16)
        self.drive_motors_left = [self.kit.continuous_servo[i] for i in range(3)]
        self.drive_motors_right = [self.kit.continuous_servo[i] for i in range(3, 6)]

        # Example steering channels. Adjust to your real wiring.
        self.steering_servos = [self.kit.servo[i] for i in range(6, 12)]

        self.mode = LocomotionModes.ACKERMANN

        self.STOP = -1
        self.LEFT_FORWARD = 0
        self.LEFT_BACKWARD = 1
        self.RIGHT_FORWARD = 1
        self.RIGHT_BACKWARD = 0

    def set_mode(self, mode: LocomotionModes):
        self.mode = mode
        print(f"Set locomotion mode to: {mode.name}")

    def set_drive(self, left_speed, right_speed):
        for motor in self.drive_motors_left:
            motor.throttle = left_speed

        for motor in self.drive_motors_right:
            motor.throttle = right_speed

    def stop(self):
        self.set_drive(self.STOP, self.STOP)

    def forward(self):
        self.set_drive(self.LEFT_FORWARD, self.RIGHT_FORWARD)

    def backward(self):
        self.set_drive(self.LEFT_BACKWARD, self.RIGHT_BACKWARD)

    def set_all_steering(self, angle):
        for servo in self.steering_servos:
            servo.angle = angle

    def ackermann(self, steering_angle):
        print(f"Ackermann steering: {steering_angle}")
        # Temporary simple version
        self.set_all_steering(90 + steering_angle)

    def point_turn(self):
        print("Point turn mode")
        # Example placeholder angles
        # You must adjust these for your mechanical layout
        angles = [45, 135, 90, 90, 135, 45]
        for servo, angle in zip(self.steering_servos, angles):
            servo.angle = angle

    def crabbing(self, angle):
        print(f"Crabbing angle: {angle}")
        self.set_all_steering(90 + angle)