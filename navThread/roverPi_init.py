# from localTesting.mainLogicLocal import main #for local testing without ROS2
from mainLogic import main
import time 

def init_roverPi():
    print("Initializing roverPi system... ")
    
    #time.sleep(1) #Simulating inittialization steps
   
   #Need to implement initialization logic here ....
    wheel_calibration()
    camera1_calibration()
    camera2_calibration()
    imu_calibration()

    print("Initializing of tibro-roverPi is completed. ")

def wheel_calibration():
    print("Calibrating the servos for straight forward motion and 90 degree turn. ")
    return

def camera1_calibration():
    print("Starting stereo camera calibraiton sequence. ")
    return

def camera2_calibration():
    print("Starting rasPi cam module2 calibraiton sequence. ")
    return

def imu_calibration():
    print("Starting IMU calibraiton sequence. ")
    return

if __name__ == "__main__":
    init_roverPi()
    main() 