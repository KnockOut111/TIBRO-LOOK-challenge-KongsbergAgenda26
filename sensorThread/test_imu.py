import time
import board
import busio
import adafruit_mpu6050

# Initialize I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# First sensor: AD0 low  → address 0x68 (default)
mpu_a = adafruit_mpu6050.MPU6050(i2c, address=0x68)

# Second sensor: AD0 high → address 0x69
mpu_b = adafruit_mpu6050.MPU6050(i2c, address=0x69)

print("Both MPU6050 sensors found! Reading data...\n")

while True:
    for label, mpu in [("Sensor A (0x68)", mpu_a), ("Sensor B (0x69)", mpu_b)]:
        ax, ay, az = mpu.acceleration
        gx, gy, gz = mpu.gyro
        temp = mpu.temperature

        print(f"--- {label} ---")
        print(f"  Accel  X: {ax:7.2f}  Y: {ay:7.2f}  Z: {az:7.2f}  m/s²")
        print(f"  Gyro   X: {gx:7.2f}  Y: {gy:7.2f}  Z: {gz:7.2f}  °/s")
        print(f"  Temp   : {temp:.1f} °C")
        print()

    print("=" * 40)
    time.sleep(10)