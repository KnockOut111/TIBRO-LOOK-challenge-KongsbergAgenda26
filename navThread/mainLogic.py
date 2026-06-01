from locomotionController import LocomotionController, LocomotionModes, SteeringServos
from enum import Enum
from rclpy.node import Node
from std_msgs.msg import String
import rclpy
import time

# Fix locomotion modes to work as it should, wheels are never set back to 90 degrees after turning, and point turn and crab steering are not implemented propperly.
# Front Right wheel is still not working as intended. Need to find solution.

#### Still having this errors that needs to be fixed: ####
# Stopping rover
# Traceback (most recent call last):
#   File "/app/roverPi_init.py", line 15, in <module>
#     main()
#     ^^^^^^
#   File "/app/mainLogic.py", line 142, in main
#     elif sensorMsg == "metal_detected":
#     ^^^^^^^^^^^^^^^^^^^^^^
#   File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/__init__.py", line 247, in spin
#     executor.spin_once()
#   File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/executors.py", line 926, in spin_once
#     self._spin_once_impl(timeout_sec)
#   File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/executors.py", line 918, in _spin_once_impl
#     raise handler.exception()
#   File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/task.py", line 286, in _execute_coroutine_step
#     result = coro.send(None)
#              ^^^^^^^^^^^^^^^
#   File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/executors.py", line 592, in handler
#     await call_coroutine()
#   File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/executors.py", line 480, in _execute
#     await await_or_execute(sub.callback, *msg_tuple)
#   File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/executors.py", line 115, in await_or_execute
#     return callback(*args)
#            ^^^^^^^^^^^^^^^
#   File "/app/mainLogic.py", line 41, in mode_callback
#     self.active = False
#     ^^^^^^^^^^^^^^^^^^^^
#   File "/app/locomotionController.py", line 87, in shutdown_rover
#     self.controller.stop()
#     ^^^^^^^^^^^^^^^
# AttributeError: 'LocomotionController' object has no attribute 'controller'

# make: *** [Makefile:10: roverpi-startsys] Error 1

class MainLogicNode(Node):
    def __init__(self):
        super().__init__("main_logic")
        
        self.controller = LocomotionController()

        # max_steering_angle = 45
        # self.ackermann_r_min = abs(self.wheel_y) / math.tan(math.radians(max_steering_angle)) + self.wheel_x
        # self.ackermann_r_max = 250

        self.active = False
        self.locomotion_mode = LocomotionModes.ACKERMANN

        self.create_subscription(String, "/rover/mainMode", self.mode_callback, 10)
        self.create_subscription(String, "/rover/locoMode", self.locomotion_callback, 10)
        self.create_subscription(String, "/rover/command", self.command_callback, 10)
        self.create_subscription(String, "/rover/sensorMsg", self.sensor_callback, 10)


        self.get_logger().info("main_logic node started")

    def mode_callback(self, msg):
        mainMode = msg.data.strip().lower()

        if mainMode == "arm":
            self.active = True
            self.get_logger().info("Rover armed! ")

        elif mainMode == "quit":
            self.active = False
            self.controller.stop()
            self.get_logger().info("Rover stopped and program exiting... ")
            self.controller.shutdown_rover()

        else:
            self.get_logger().warn(f"Invalid mode: {mainMode}")

    def locomotion_callback(self, msg):
        locoMode = msg.data.strip().lower()

        if locoMode == "ackermann":
            self.locomotion_mode = LocomotionModes.ACKERMANN
            self.get_logger().info("Ackermann mode activated.")
            print("Ackermann mode activated.")

        elif locoMode == "point_turn":
            self.locomotion_mode = LocomotionModes.POINT_TURN
            self.get_logger().info("Point turn mode activated.")
            print("Point turn mode activated.")

        elif locoMode == "crabbing":
            self.locomotion_mode = LocomotionModes.CRABBING
            self.get_logger().info("Crabbing mode activated.")
            print("Crabbing mode activated.")

        else:
            self.get_logger().warn(f"Invalid locomotion mode: {locoMode}")
            return

        self.controller.set_mode(self.locomotion_mode)
        self.get_logger().info(f"Locomotion mode set to {self.locomotion_mode.name}")

    def command_callback(self, msg):
        command = msg.data.strip().lower()
        parts = command.split()

        if not self.active:
            self.get_logger().warn("Ignoring command because rover is not armed. ")
            return

        # Implement missing command handling logic here, e.g.:
        if command == "forward":
            self.controller.forward()
            self.get_logger().info("Moving forward")

        elif command == "backward":
            self.controller.backward()
            self.get_logger().info("Moving backward")

        elif command == "stop":
            self.controller.stop()
            self.get_logger().info("Stopping rover")

        elif command == "left_turn":
            self.controller.set_all_steering(90 - 45)  # Example angle, adjust as needed
            self.get_logger().info("Turning left")

        elif command == "right_turn":
            self.controller.set_all_steering(90 + 45)  # Example angle, adjust as needed
            self.get_logger().info("Turning right")

        elif command == "reset_steering":
            self.controller.set_all_steering(90)
            self.get_logger().info("Resetting steering")

        elif parts[0] == "set_wheel_steering":
            if len(parts) != 3:
                self.get_logger().warn("Input need to be on this form: set_wheel_steering FR 90")
                return

            wheel_name = parts[1].upper()

            try:
                angle = int(parts[2])
                wheel = SteeringServos[wheel_name]
            except ValueError:
                self.get_logger().warn(f"Invalid angle: {parts[2]}")
                return
            except KeyError:
                self.get_logger().warn(f"Invalid wheel: {wheel_name}")
                return

            self.controller.set_wheel_steering(wheel, angle)
            self.get_logger().info(f"Set {wheel_name} steering to {angle} degrees")

        else:
            self.get_logger().warn(f"Unknown command: {command}")

    def sensor_callback(self, msg):
        sensorMsg = msg.data.strip().lower()
        self.get_logger().info(f"Received sensor data: {sensorMsg}")
        
        # Implement sensor data handling logic here, e.g.: 
        if sensorMsg == "obstacle_detected":
            self.controller.stop()
            self.get_logger().info("Obstacle detected! Stopping rover.")
            time.sleep(3)  # Pause briefly before moving backward
            self.controller.backward()
            time.sleep(2)  # Move backward for a short duration
            self.controller.stop()
            self.get_logger().info("Moving backward and making a stop.")

        elif sensorMsg == "clear_path":
            self.controller.forward()
            self.get_logger().info("Path is clear. Moving forward.")

        elif sensorMsg == "metal_detected":
            self.controller.stop()  
            time.sleep(1)  # Pause briefly before moving backward
            self.controller.backward()
            time.sleep(2)  # Move backward for a short duration
            #Run piCam AI image recognition for more detailed investigation of the metal object or similar, 
            # and publish findings to a topic for further analysis.
            self.controller.stop()  
            self.get_logger().info("Metal detected! Stopping rover and moving backward for more detailed investigation.")


def main(args=None):
    rclpy.init(args=args)

    main_logic = MainLogicNode()

    try:
        rclpy.spin(main_logic)
    finally:
        main_logic.controller.stop()
        main_logic.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()