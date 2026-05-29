# Working code for driving straight with 6 engines. 
# Uses keyboard inputs forward, backward, stop and quit to control the engines.

print("Starting forward motion driver...")

from adafruit_servokit import ServoKit


kit = ServoKit(channels=16)

left_engines = [kit.continuous_servo[i] for i in range(3)]
right_engines = [kit.continuous_servo[i] for i in range(3, 6)]

STOP = 0
LEFT_FORWARD = -1.0
LEFT_BACKWARD = 1.0
RIGHT_FORWARD = 1.0
RIGHT_BACKWARD = -1.0

#FUNCTIONS
def set_drive(left_speed, right_speed):
    for engine in left_engines:
        engine.throttle = left_speed
    for engine in right_engines:
        engine.throttle = right_speed

def stop_motion():
    print
    #set_drive(STOP, STOP)

def forward_motion():
    print("Moving forward...")
    #set_drive(LEFT_FORWARD, RIGHT_FORWARD)

def backward_motion():
    print("Moving backward...")
    #set_drive(LEFT_BACKWARD, RIGHT_BACKWARD)

   
