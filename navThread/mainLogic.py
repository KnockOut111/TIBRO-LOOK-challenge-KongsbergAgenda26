import rclpy
import time

from locomotionController import LocomotionController, LocomotionModes, SteeringServos
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.executors import ExternalShutdownException

# Fix locomotion modes to work as it should, wheels are never set back to 90 degrees after turning, and point turn and crab steering are not implemented propperly.
# Front Right wheel is still not working as intended. Need to find solution.
# Need to make a function for calibrating the servos, maybe as an itialization step in the beginning of the program, to ensure that 90 degrees is actually straight for all wheels.
    ## Fix init servos steering func in locomotion controller and call it in the init of the main logic node.
    ## Test and start implementing init for cameras and IMU as well

class MainLogicNode(Node):
    def __init__(self):
        super().__init__("mainLogic_node")
        
        self.controller = LocomotionController()

        # max_steering_angle = 45
        # self.ackermann_r_min = abs(self.wheel_y) / math.tan(math.radians(max_steering_angle)) + self.wheel_x
        # self.ackermann_r_max = 250

        self.active = False
        self.locomotion_mode = LocomotionModes.CRABBING

        self.create_subscription(String, "/rover/mainMode", self.mode_callback, 10)
        self.create_subscription(String, "/rover/locoMode", self.locomotion_callback, 10)
        self.create_subscription(String, "/rover/command", self.command_callback, 10)
        self.create_subscription(String, "/rover/sensorMsg", self.sensor_callback, 10)
        self.shutdown_pub = self.create_publisher(String, "/rover/system_shutdown",10)

        self.init_roverPi()
        self.get_logger().info("MainLogicNode is running...")

    def init_roverPi(self):
        self.get_logger().info("Initializing roverPi system... ")
    
        #Need to implement initialization logic here ....
        self.wheel_calibration()
        self.camera1_calibration()
        self.camera2_calibration()
        self.imu_calibration()

        self.get_logger().info("Initializing of tibro-roverPi is completed. ")

    def wheel_calibration(self):
            self.get_logger().info("Initializing the steering servos... ")

            self.controller.initialize_steering_servos()
            
            self.get_logger().info("Finished calibrating the steering servos for straight forward motion. ")
            return

    def camera1_calibration(self):
        self.get_logger().info("Starting stereo camera calibraiton sequence. ")
        return

    def camera2_calibration(self):
        self.get_logger().info("Starting rasPi cam module2 calibraiton sequence. ")
        return

    def imu_calibration(self):
        self.get_logger().info("Starting IMU calibraiton sequence. ")
        return
    

    def is_armed(self):
        if not self.active:
            self.get_logger().warn("Rover not armed. Remember to 'arm' first.")
            return False
        return True


    def mode_callback(self, msg):
        if not self.is_armed():
            return
        
        mainMode = msg.data.strip().lower()

        if mainMode == "arm":
            self.active = True
            self.get_logger().info("Rover armed! ")

        elif mainMode == "quit":
            self.active = False
            self.controller.stop()
            self.get_logger().info("Rover stopped and program exiting... ")

            shutdown_msg = String()
            shutdown_msg.data = "shutdown"
            self.shutdown_pub.publish(shutdown_msg)

            #self.controller.shutdown_rover()
            rclpy.shutdown()


        else:
            self.get_logger().warn(f"Invalid mode: {mainMode}")

    def locomotion_callback(self, msg):
        if not self.is_armed():
            self.get_logger().warn("Locomotion not set. Rover need to be armed! ")
            return
        
        locoMode = msg.data.strip().lower()
        parts = locoMode.split()

        if parts[0] == "ackermann": # TEST!!!!
            if len(parts) != 2:
                self.get_logger().warn("Input type required: ackermann 30")
                return

            try:
                steering_angle = int(parts[1])
            except ValueError:
                self.get_logger().warn(f"Invalid steering angle: {parts[1]}")
                return
            except IndexError:
                self.get_logger().warn("Steering angle required for ackermann mode")
                return

            self.locomotion_mode = LocomotionModes.ACKERMANN
            self.controller.ackermann(steering_angle)
            self.get_logger().info(f"Ackermann activated at {steering_angle} degrees")

        elif locoMode == "point_turn":
            self.locomotion_mode = LocomotionModes.POINT_TURN
            self.controller.point_turn()
            self.get_logger().info("Point turn activated")

        elif parts[0] == "crabbing": # TEST!!!!
            if len(parts) != 2:
                self.get_logger().warn("Input type required: crabbing 90")
                return

            try:
                angle = int(parts[1])
            except ValueError:
                self.get_logger().warn(f"Invalid angle: {parts[1]}")
                return
            except IndexError:
                self.get_logger().warn("Steering angle required for crabbing mode")
                return

            self.locomotion_mode = LocomotionModes.CRABBING
            self.controller.crabbing(angle)
            self.get_logger().info(f"Crabbing activated at {angle} degrees")

        else:
            self.get_logger().warn(f"Invalid locomotion mode: {locoMode}")
            return

        self.controller.set_mode(self.locomotion_mode)
        self.get_logger().info(f"Locomotion set to: {self.locomotion_mode.name}") #Test that this one logs correct and not double

    def command_callback(self, msg):
        if not self.is_armed():
            self.get_logger().warn("Ignoring command! ")
            return
        
        command = msg.data.strip().lower()
        parts = command.split()

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

        elif parts[0] == "left_turn": # TEST!!!!
            if len(parts) != 2:
                self.get_logger().warn("Input type required: left_turn 45")
                return

            try:
                turn_angle = int(parts[1])
            except ValueError:
                self.get_logger().warn(f"Invalid angle: {parts[1]}")
                return
            except IndexError:
                self.get_logger().warn("Turn angle required for left_turn")
                return
            
            self.controller.set_all_steering(90 - turn_angle)  # Need to fix stearing for different modes.
            self.get_logger().info("Turning left " + str(turn_angle) + " degrees. ")

        elif parts[0] == "right_turn":  # TEST!!!!
            if len(parts) != 2:
                self.get_logger().warn("Input type required: right_turn 45")
                return

            try:
                turn_angle = int(parts[1])
            except ValueError:
                self.get_logger().warn(f"Invalid angle: {parts[1]}")
                return
            except IndexError:
                self.get_logger().warn("Turn angle required for right_turn")
                return

            self.controller.set_all_steering(90 + turn_angle)  # Example angle, adjust as needed
            self.get_logger().info("Turning right " + str(turn_angle) + " degrees. ")

        elif command == "reset_steering":
            self.controller.set_all_steering(90)
            self.get_logger().info("Resetting steering")

        elif parts[0] == "set_wheel_steering": # TEST
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
        if not self.is_armed():
            self.get_logger().warn("Ignoring command! ")
            return
        
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

    def starting_autonomous_mode(self):
        if not self.is_armed():
            self.get_logger().warn("Autonomous mode did not start. The rover needs to be armed!")
            return
        
        self.get_logger().info("Starting autonomous mode...")

        # Implement autonomous behavior logic here, e.g.:
        # - Use sensor data to navigate
        # - Implement obstacle avoidance
        # - Follow a predefined path or explore randomly

def main(args=None):
    rclpy.init(args=args)

    mainLogic_node = MainLogicNode()
    
    try:
        rclpy.spin(mainLogic_node)
    
    except ExternalShutdownException:
        pass

    finally:
        mainLogic_node.controller.stop()
        mainLogic_node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()