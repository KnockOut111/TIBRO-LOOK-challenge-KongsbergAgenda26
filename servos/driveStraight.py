# Check: forward, backward, stop, quit works


from adafruit_servokit import ServoKit

kit = ServoKit(channels=16)

left_engines = [kit.continuous_servo[i] for i in range(3)]
right_engines = [kit.continuous_servo[i] for i in range(3, 6)]

STOP = -1
LEFT_FORWARD = 0
LEFT_BACKWARD = 1
RIGHT_FORWARD = 1
RIGHT_BACKWARD = 0

def set_drive(left_speed, right_speed):
    for engine in left_engines:
        engine.throttle = left_speed
    for engine in right_engines:
        engine.throttle = right_speed

set_drive(STOP, STOP)

try:
    while True:
        command = input("Enter command (forward/backward/stop/quit): ").strip().lower()

        if command == "forward":
            set_drive(LEFT_FORWARD, RIGHT_FORWARD)

        elif command == "backward":
            set_drive(LEFT_BACKWARD, RIGHT_BACKWARD)

        elif command == "stop":
            set_drive(STOP, STOP)

        elif command == "quit":
            set_drive(STOP, STOP)
            break

        else:
            print("Unknown command")

except KeyboardInterrupt:
    set_drive(STOP, STOP)
