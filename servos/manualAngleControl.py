# from adafruit_servokit import ServoKit

# #Only for main engines not the locomotion servos.

# kit = ServoKit(channels=16)
# servo0 = kit.servo[0]
# servo1 = kit.servo[1]
# servo2 = kit.servo[2]
# servo3 = kit.servo[3]
# servo4 = kit.servo[4]
# servo5 = kit.servo[5]

# while True:
#     angle = int(input("Angle 0-360: "))
#     servo0.angle = angle

#     angle = int(input("Angle 0-360: "))
#     servo1.angle = angle

#     angle = int(input("Angle 0-360: "))
#     servo2.angle = angle

#     angle = int(input("Angle 0-360: "))
#     servo3.angle = angle

#     angle = int(input("Angle 0-360: "))
#     servo4.angle = angle

#     angle = int(input("Angle 0-360: "))
#     servo5.angle = angle

from adafruit_servokit import ServoKit
import time

kit = ServoKit(channels=16)

servos = [kit.servo[i] for i in range(6)]

print("Starting all motors forward")

for servo in servos:
    servo.angle = 180

time.sleep(5)

print("Stopping all motors")

for servo in servos:
    servo.angle = 90
