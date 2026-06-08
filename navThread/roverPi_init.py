# from localTesting.mainLogicLocal import main #for local testing without ROS2
from mainLogic import main
from locomotionController import LocomotionController, LocomotionModes, SteeringServos
import time 

def init_roverPi():
    print("Initializing roverPi system... ")
       
   #Need to implement initialization logic here ....
    wheel_calibration()
    camera1_calibration()
    camera2_calibration()
    imu_calibration()

    print("Initializing of tibro-roverPi is completed. ")

def wheel_calibration(self):
    print("Calibrating the servos for straight forward motion and 90 degree turn. ")

    for steeringPos in SteeringServos:
        self.LocomotionController.setting_netural_steering_states(steeringPos) # Set all wheels to 90 degrees for straight forward motion. Adjust if needed.
    
    print("Finished calibrating the servos for straight forward motion. ")
    return

def camera1_calibration(self):
    print("Starting stereo camera calibraiton sequence. ")
    return

def camera2_calibration(self):
    print("Starting rasPi cam module2 calibraiton sequence. ")
    return

def imu_calibration(self):
    print("Starting IMU calibraiton sequence. ")
    return

if __name__ == "__main__":
    init_roverPi()
    main() 