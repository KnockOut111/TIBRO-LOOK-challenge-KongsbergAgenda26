from adafruit_servokit import ServoKit
import time

kit = ServoKit(channels=16)

servo = kit.servo[0]

print("Starting servo test...")

while True:
    print("0 degrees")
    servo.angle = 0
    time.sleep(1)

    print("90 degrees")
    servo.angle = 90
    time.sleep(1)

    print("180 degrees")
    servo.angle = 180
    time.sleep(1)
