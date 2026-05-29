# One servo at a time.
# Check that they respond to throttle input. 
# Check that they stop when throttle is set to 0.0. 
# Check that they reverse when throttle is negative. 
# Check that they go forward when throttle is positive.


from adafruit_servokit import ServoKit

kit = ServoKit(channels=16)

while True:
    ch = int(input("Channel 0-5: "))
    throttle = float(input("Throttle -1.0 to 1.0, 0 stop: "))

    if 0 <= ch <= 5 and -1.0 <= throttle <= 1.0:
        kit.continuous_servo[ch].throttle = throttle
    else:
        print("Invalid input")

