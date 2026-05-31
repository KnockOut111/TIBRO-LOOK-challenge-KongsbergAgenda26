# from localTesting.mainLogicLocal import main #for local testing without ROS2
from mainLogic import main
import time 

def init_roverPi():
    print("Initializing roverPi navThread... ")
    
    time.sleep(1) #Simulating inittialization steps
    #Need to implement initialization logic here ....

    print("Initializing of tibro-roverPi is completed. ")

if __name__ == "__main__":
    init_roverPi()
    main() 