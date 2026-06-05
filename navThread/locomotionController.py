from enum import Enum
from adafruit_servokit import ServoKit
import json


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

        # self.steering_neutral = {
        #     SteeringServos.FL: 90,
        #     SteeringServos.FR: 90,
        #     SteeringServos.CL: 90,
        #     SteeringServos.CR: 90,
        #     SteeringServos.RL: 90,
        #     SteeringServos.RR: 90,
        # }

        self.current_steering_angles = {}
        

### Steering servo initialization, calibration, storage and loading ###
    def initialize_steering_state(self, steering_neutral):
        print("Initializing steering servo state...")

        for wheel, neutral_angle in steering_neutral.items():
            self.set_wheel_steering(wheel, neutral_angle)
            self.current_steering_angles[wheel] = neutral_angle
        
        print("Steering servos initialized to neutral positions")

    def update_steering_neutral_positions(self, wheel: SteeringServos, angle: int, steering_neutral):
        angle = max(0, min(180, angle))
        steering_neutral[wheel] = angle
        self.current_steering_angles[wheel] = angle
        print(f"Updated neutral position for {wheel.name} to {angle} degrees")

    def update_neutral_position(self, wheel: SteeringServos, angle, steering_neutral):
        steering_neutral[wheel] = angle
        print(f"Updated neutral position for {wheel.name} to {angle} degrees")
    
    def save_neutral_positions(self, steering_neutral):
        data = {
            wheel.name: angle
            for wheel, angle in steering_neutral.items()
        }

        with open("steering_calibration.json", "w") as f:
            json.dump(data, f, indent=4)

    def load_neutral_positions(self, steering_neutral):
        try:
            with open("steering_calibration.json", "r") as f:
                data = json.load(f)

            steering_neutral.update({
                SteeringServos[name]: angle
                for name, angle in data.items()
            })

            print("Loaded steering calibration")

        except FileNotFoundError:
            print("No steering calibration found, using defaults")



### Different set fuctions for different modes, e.g. set_mode, set_drive, set_steering, etc. ###
    def set_mode(self, mode: LocomotionModes):
        self.mode = mode

    def get_mode(self):
        return self.mode

    def set_drive(self, left_speed, right_speed):
        for motor in self.drive_motors_left:
            motor.throttle = left_speed

        for motor in self.drive_motors_right:
            motor.throttle = right_speed
    
    def set_all_steering(self, angle):
        angle = max(0, min(180, angle)) # Ensure angle is within valid range
        for servo in self.steering_servos:
            servo.angle = angle

    def set_wheel_steering(self, wheel: SteeringServos, angle):
        angle = max(0, min(180, angle)) # Ensure angle is within valid range
        self.kit.servo[wheel.value].angle = angle
        self.current_steering_angles[wheel] = angle



### Main drive functions ###
    def stop(self):
        self.set_drive(self.STOP, self.STOP)

    def forward(self):
        self.set_drive(self.LEFT_FORWARD, self.RIGHT_FORWARD)

    def backward(self):
        self.set_drive(self.LEFT_BACKWARD, self.RIGHT_BACKWARD)

### Different locomotion modes ###
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
        # This should work if wheels are calibrated at start, but maybe add a limit so that only 0 (straight) or 90 (sideways) is allowed.




### Own file ??? ###
# class AutonomousController():
#     def starting_procedure():
#         print("Starting up rover and driving off ramp...")

#         # Drive off ramp until IMU shows planer surfaces again. 0 at beginning, 
#         # then tilt some degrees (going off ramp), 0 agan when off ramp + some deviation in level hight.
#         # As the ramp is higher up than the main area of traversal. 

#     def scanning_mode(self):
#         print("Starting scanning the area by turning 360 degrees. ")
#         # Scan the area by turning 360 degrees in point_turn mode, as long as no obsticles are detected. 
#         # Simultaneously as stereo camera is taking in the suroundings. 

#     def main_loop(self):
#         print("Entering the main logic of the rover driving. ")
#         # Drive forward, untill object detected inside a given distance.
#         # Then stop, move backwards for 2s? then move random? left or right.
#         # Now continuing on the new path, until new object is 'detected' again or 
#         # innside the given limit of radius to possible obstacle.
        

# class MetelDetectionController():
    
    
#     def metal_detected(bool):
#         metalDetected = bool
#         print("Metal detected! ")
        