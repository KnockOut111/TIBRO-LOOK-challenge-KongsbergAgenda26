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
import rospy
import math


class LocomotionModes(Enum):
    ACKERMANN = 0
    POINT_TURN = 1
    CRABBING = 2



# From https://github.com/esa-prl/ExoMy_Software/blob/master/src/rover.py
# Contains all motor controls and math for calculating the angles and speeds for the different locomotion modes.
class Rover():
    # Defining wheel names
    FL, FR, CL, CR, RL, RR = range(0, 6)

    # Defining locomotion modes
    ACKERMANN, POINT_TURN, CRABBING = range(0, 3)

    def __init__(self):
        self.locomotion_mode = LocomotionModes.ACKERMANN

        self.wheel_x = 12.0
        self.wheel_y = 20.0

        max_steering_angle = 45
        self.ackermann_r_min = abs(
            self.wheel_y) / math.tan(max_steering_angle * math.pi / 180.0) + self.wheel_x

        self.ackermann_r_max = 250

    # Sets the locomotion mode of the robot.
    def setLocomotionMode(self, locomotion_mode_command):

        if(self.locomotion_mode != locomotion_mode_command):
            self.locomotion_mode = locomotion_mode_command
            rospy.loginfo('Set locomotion mode to: %s',
                          LocomotionModes(locomotion_mode_command).name)

    


class LocomotionController:
    def __init__(self):
        self.kit = ServoKit(channels=16)
        self.left_engines = [self.kit.continuous_servo[i] for i in range(3)]
        self.right_engines = [self.kit.continuous_servo[i] for i in range(3, 6)]
        self.mode = LocomotionModes.ACKERMANN

    def set_mode(self, mode: LocomotionModes):
        self.mode = mode
