# Working code for driving straight with 6 engines. 
# Uses keyboard inputs forward, backward, stop and quit to control the engines.

print("Starting forward motion driver...")

from adafruit_servokit import ServoKit

kit = ServoKit(channels=16)
left_engines = [kit.continuous_servo[i] for i in range(3)]
right_engines = [kit.continuous_servo[i] for i in range(3, 6)]
forwardMotionMode = False

# command = { forwardMotionMode: False/True, motion: forward/backward/stop/quit  }

STOP = 0
LEFT_FORWARD = -1.0
LEFT_BACKWARD = 1.0
RIGHT_FORWARD = 1.0
RIGHT_BACKWARD = -1.0


#FUNCTIONS
def set_forward_motion_mode(enabled):
    global forwardMotionMode
    forwardMotionMode = enabled

def set_drive(left_speed, right_speed):
    for engine in left_engines:
        engine.throttle = left_speed
    for engine in right_engines:
        engine.throttle = right_speed


#LOGIC
set_drive(STOP, STOP) # Remember this one to later as it may cause some logic issues

while forwardMotionMode == True:
    command = input("Enter command (forward/backward/stop/quit): ").strip().lower() # use later: command = os.getenv("ROVER_MODE", "still_motion_mode")


    if command == "forward":
        print("Forward motion activated. ")
        #set_drive(LEFT_FORWARD, RIGHT_FORWARD)

    elif command == "backward":
        print("Backward motion activated. ")
        #set_drive(LEFT_BACKWARD, RIGHT_BACKWARD)

    elif command == "stop":
        print("Stop motion activated. ")
        #set_drive(STOP, STOP)

    elif command == "quit":
        print("Quit command received. ")
        #set_drive(STOP, STOP)
        break

    else:
        print("Error; unknown command! ")

