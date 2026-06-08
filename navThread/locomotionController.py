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

        self.wheelState_crabbing = True
        self.right_turn_ack = False
        self.left_turn_ack = False


        self.STOP = -1
        self.LEFT_FORWARD = 0
        self.LEFT_BACKWARD = 1
        self.RIGHT_FORWARD = 1
        self.RIGHT_BACKWARD = 0

        self.steering_neutral = {
            SteeringServos.FL: 70,
            SteeringServos.FR: 105,
            SteeringServos.CL: 115,
            SteeringServos.CR: 80,
            SteeringServos.RL: 115,
            SteeringServos.RR: 83,
        }

        self.current_steering_angles = {}
        

### Steering servo initialization, calibration, storage and loading ###
    def setting_neutral_steering_states(self):
        print("Setting neutral steering servo states...")

        for wheel, neutral_angle in self.steering_neutral.items():
            self.set_wheel_steering(wheel, neutral_angle)
        
        print("Steering servos set to neutral positions")

    def update_steering_neutral_positions(self, wheel: SteeringServos, angle: int):
        angle = max(0, min(180, angle))
        self.steering_neutral[wheel] = angle
        print(f"Updated neutral position for {wheel.name} to {angle} degrees")

    def save_neutral_positions(self):
        data = {
            wheel.name: angle
            for wheel, angle in self.steering_neutral.items()
        }

        with open("steering_calibration.json", "w") as f:
            json.dump(data, f, indent=4)

    def load_neutral_positions(self):
        try:
            with open("steering_calibration.json", "r") as f:
                data = json.load(f)

            self.steering_neutral.update({
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

    # Set wheels for driving forward or backwards
    def set_drive(self, left_speed, right_speed):
        for motor in self.drive_motors_left:
            motor.throttle = left_speed

        for motor in self.drive_motors_right:
            motor.throttle = right_speed

    # Resetting all wheels
    def reset_to_neutral(self):
        for wheel, angle in self.steering_neutral.items():
            self.set_wheel_steering(wheel, angle)


    def crab_straight(self):
        self.reset_to_neutral()

    def crab_sideways(self):
        for wheel, neutral_angle in self.steering_neutral.items():
            if neutral_angle <= 90:
                self.set_wheel_steering(wheel, neutral_angle + 90)
            else:
                self.set_wheel_steering(wheel, neutral_angle - 90)

    # Setting one wheel to a given angle
    def set_wheel_steering(self, wheel: SteeringServos, angle: int):
        angle = max(0, min(180, angle)) # Ensure angle is within valid range
        self.kit.servo[wheel.value].angle = angle
        #self.current_steering_angles[wheel] = angle #Uncomment if new values are wante to calibrate for neutral pos

    # Setting all wheels to same amount of degrees
    def set_all_steering_servos(self, angle: int):
        angle = max(0, min(180, angle))
        for wheel in SteeringServos:
            self.set_wheel_steering(wheel, angle)
        


### Main drive functions ###
    def stop(self):
        self.set_drive(self.STOP, self.STOP)

    def forward(self):
        self.wheelState_crabbing = True
        self.set_drive(self.LEFT_FORWARD, self.RIGHT_FORWARD)

    def backward(self):
        self.wheelState_crabbing = True
        self.set_drive(self.LEFT_BACKWARD, self.RIGHT_BACKWARD)

    def right_turn(self):
        self.wheelState_crabbing = False
        self.right_turn_ack = True

    def left_turn(self):
        self.wheelState_crabbing = False
        self.left_turn_ack = True



### Different locomotion modes ###
    # Left and right turn is set each time the ackermann func is called. Need to be called periodic!
    def ackermann(self, steering_angle):
        if self.right_turn_ack == True:
            self.set_wheel_steering(SteeringServos.FR, 90 - steering_angle) #Need checking of angles.
            self.set_wheel_steering(SteeringServos.FL, 90 + steering_angle)
            self.right_turn_ack = False

        elif self.left_turn_ack == True:
            self.set_wheel_steering(SteeringServos.FR, 90 - steering_angle) #Need checking of angles.
            self.set_wheel_steering(SteeringServos.FL, 90 + steering_angle)
            self.left_turn_ack = False

        else:
            self.reset_to_neutral()

    ##########@@@@@@ Need to adjus these angles for correct behavor
    # Only turn on the spot, so need only to know how long to turn or how many rounds wheels need to turn
    def point_turn(self):
        target_angles = {
            SteeringServos.FL: 135,
            SteeringServos.FR: 45,
            SteeringServos.CL: 90,
            SteeringServos.CR: 90,
            SteeringServos.RL: 40,
            SteeringServos.RR: 130,
        } #Check if angles is on right servo pos

        for wheel, angle in target_angles.items():
            self.set_wheel_steering(wheel, angle)

        #Motion: Fix so that only rear and front wheels turn in opposite direction, the middle ones must be still.

    # Only pointed forward or 90 deg sideways.
    def crabbing(self):
        if self.wheelState_crabbing:
            for wheel, angle in self.steering_neutral.items():
                if angle >= 90:
                    self.set_wheel_steering(wheel, angle - 100) #Increse this and the one bellow? 
                else:
                    self.set_wheel_steering(wheel, 0)
        else:
            for wheel, angle in self.steering_neutral.items():
                if angle <= 90:
                    self.set_wheel_steering(wheel, angle + 100)
                else:
                    self.set_wheel_steering(wheel, angle + 0) #Maybe something else here as calibrating or something as it will be a case where the wheels are not properly alligned with driection of motion.
                    print(f"Angle is greater than 90 and moving wheels 90 deg more does not make sense for wheel {wheel}, currently at {angle}. ")
        # This should work if wheels are calibrated at start, but maybe add a limit so that only 0 (straight) or 90 (sideways) is allowed.
        # Motion: forward and backwards as normal

        ### GPT suggestion ###
        # def crabbing(self):
        #     for wheel, neutral_angle in self.steering_neutral.items():
        #         crab_angle = min(180, neutral_angle + 90)
        #         self.set_wheel_steering(wheel, crab_angle)




class MetelDetectionController():
    def __init__(self):
        self.numberOfTimes_MetalDetected = 0

    def metal_detected(self, bool):
        if bool:
            self.numberOfTimes_MetalDetected += 1
            return