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

class LocomotionController():
    def __init__(self):
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

        print("Locomotion controller started")

    def set_mode(self, mode: LocomotionModes):
        self.mode = mode

    def get_mode(self):
        return self.mode

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

    def set_wheel_steering(self, wheel: SteeringServos, angle):
        self.kit.servo[wheel.value].angle = angle

    def ackermann(self, steering_angle):
        self.set_wheel_steering(SteeringServos.FR, 90 - steering_angle) #Need checking of angles.
        self.set_wheel_steering(SteeringServos.FL, 90 + steering_angle)

    def point_turn(self):
        angles = [45, 135, 90, 90, 135, 45] #Check if angles is on right servo pos
        for servo, angle in zip(self.steering_servos, angles):
            servo.angle = angle
        
        #Fix so that only rear and front wheels turn in opposite direction, the middle ones must be still.

    def crabbing(self, angle):
        self.set_all_steering(90 + angle)
        # This should work, but maybe add a limit so that only 0 (straight) or 90 (sideways) is allowed.

    def shutdown_rover(self):
        self.stop()
        print("Shutting down rover...")


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