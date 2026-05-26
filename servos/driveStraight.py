from adafruit_servokit import ServoKit
import time

kit = ServoKit(channels=16)
command = str(input("Enter command: "))

#Only for main engines for forword and backward motion = kit.servo[0]
servo0 = kit.servo[0]
servo1 = kit.servo[1]
servo2 = kit.servo[2]
servo3 = kit.servo[3]
servo4 = kit.servo[4]
servo5 = kit.servo[5]

#For locomotion servos
# servo6 = kit.servo[6]
# servo7 = kit.servo[7]
# servo8 = kit.servo[8]
# servo9 = kit.servo[9]
# servo10 = kit.servo[10]
# servo11 = kit.servo[11]


print("Moving forward script started... ")
print("Enter command: " + command)

while command == "forward":
    print("Engine1 drives 360 deg forward... ")
    servo0.angle = 360
    time.sleep(0.1)

    print("Engine2 drives 360 deg forward... ")
    servo1.angle = 360
    time.sleep(0.1)

    print("Engine3 drives 360 deg forward... ")
    servo2.angle = 360
    time.sleep(0.1)

    print("Engine4 drives 360 deg forward... ")
    servo3.angle = 360
    time.sleep(0.1)

    print("Engine5 drives 360 deg forward... ")
    servo4.angle = 360
    time.sleep(0.1)

    print("Engine6 drives 360 deg forward... ")
    servo5.angle = 360
    time.sleep(0.1)

    if command == "stop":
        print("Stopping all engines... ")
        servo0.angle = 90
        servo1.angle = 90
        servo2.angle = 90
        servo3.angle = 90
        servo4.angle = 90
        servo5.angle = 90
        break       
