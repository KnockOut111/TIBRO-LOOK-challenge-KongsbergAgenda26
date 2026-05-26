# Check: forward, backward, stop, quit works


from adafruit_servokit import ServoKit

kit = ServoKit(channels=16)

left_engines = [kit.servo[i] for i in range(3)]      # 0,1,2
right_engines = [kit.servo[i] for i in range(3, 6)]  # 3,4,5

STOP = 90
LEFT_FORWARD = 0
LEFT_BACKWARD = 180
RIGHT_FORWARD = 180
RIGHT_BACKWARD = 0


def set_drive(left_speed, right_speed):
    for engine in left_engines:
        engine.angle = left_speed
    for engine in right_engines:
        engine.angle = right_speed

set_drive(STOP, STOP)

try:

    while True:
        command = input("Enter command (forward/backward/stop/quit): ").strip().lower()
        

        if command == "forward":
            print("Driving forward")
            set_drive(LEFT_FORWARD, RIGHT_FORWARD)

        elif command == "backward":
            print("Driving backward")
            set_drive(LEFT_BACKWARD, RIGHT_BACKWARD)

        elif command == "stop":
            print("Stopping")
            set_drive(STOP, STOP)

        elif command == "quit":
            print("Exiting")
            set_drive(STOP, STOP)
            break

        else:
            print("Unknown command")

except KeyboardInterrupt:
    print("\nEmergency stop")
    set_drive(STOP, STOP)