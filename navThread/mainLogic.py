import rclpy

from typing import Callable
from rclpy.timer import Timer
from rclpy.node import Node
from std_msgs.msg import String
from sensor_msgs.msg import Imu, LaserScan, Bool
from rclpy.executors import ExternalShutdownException

from locomotionController import LocomotionController, LocomotionModes, SteeringServos, MetelDetectionController


# Fix locomotion modes to work as it should, wheels are never set back to 90 degrees after turning, and point turn and crab steering are not implemented propperly.
# Front Right wheel is still not working as intended. Need to find solution.
# Need to make a function for calibrating the servos, maybe as an itialization step in the beginning of the program, to ensure that 90 degrees is actually straight for all wheels.
    ## Fix init servos steering func in locomotion controller and call it in the init of the main logic node.
    ## Test and start implementing init for cameras and IMU as well

## Continue with steering servo initialization and calibration, and then implement the different locomotion modes propperly.
## Test it!!

class MainLogicNode(Node):
    def __init__(self):
        super().__init__("mainLogic_node")
        
        self.controller = LocomotionController()
        self.metalSensorController = MetelDetectionController()
        
        self.active = False
        self.locomotion_mode = LocomotionModes.CRABBING
        self.latest_imu = {}
        self.latest_depth_scan = None
        self.latest_center_depth = None
        self.obstacle_stop_distance = 0.8

        self.gpio17_state = False
        self.gpio22_state = False
        self.gpio27_state = False
        

        # Timer setup
        self.active_timers: dict[str, Timer] = {}

        # Subscriptions
        self.create_subscription(String, "/rover/mainMode", self.mode_callback, 10)
        self.create_subscription(String, "/rover/locoMode", self.locomotion_callback, 10)
        self.create_subscription(String, "/rover/command", self.command_callback, 10)
        self.create_subscription(String, "/rover/sensorMsg", self.autonomous_callback, 10)
        
        self.create_subscription(Imu, "/sensors/imu_68", self.imu_callback, 10)
        self.create_subscription(Imu, "/sensors/imu_69", self.imu_callback, 10)
        
        self.create_subscription(LaserScan, "/sensors/depth_scan", self.depth_scan_callback, 10)

        self.create_subscription(Bool, "metal_sensor/gpio17", self.gpio17_callback, 10)
        self.create_subscription(Bool, "metal_sensor/gpio22", self.gpio22_callback, 10)
        self.create_subscription(Bool, "metal_sensor/gpio27", self.gpio27_callback, 10)
        self.create_subscription(String, "metal_sensor/metal_detected", self.autonomous_callback, 10)

    
        # Publishers
        self.shutdown_pub = self.create_publisher(String, "/rover/system_shutdown",10)


        self.init_roverPi()
        self.get_logger().info("MainLogicNode is now running...")

    #### Callback functions ####
    ### Timer management functions ###
    def start_timer(self, name: str, delay_seconds: float, callback: Callable[[], None]) -> None:
        self.cancel_timer(name)

        def timer_wrapper() -> None:
            self.cancel_timer(name)
            callback()

        self.active_timers[name] = self.create_timer(delay_seconds, timer_wrapper)

    def cancel_timer(self, name: str) -> None:
        timer = self.active_timers.pop(name, None)
        if timer is not None:
            timer.cancel()

    def cancel_all_timers(self) -> None:
        for timer in self.active_timers.values():
            timer.cancel()
        self.active_timers.clear()


    ### Initialization and calibration functions ###
    def init_roverPi(self):
        self.get_logger().info("Initializing roverPi system...")
    
        #Need to implement initialization logic here ....
        self.wheel_calibration()
        self.camera1_calibration()
        self.camera2_calibration()
        self.imu_calibration()
        self.get_logger().info("Initializing of tibro-roverPi is completed")

    def destroy_node(self):
        super().destroy_node()

    def wheel_calibration(self):
        self.get_logger().info("Initializing the steering servos...")
        self.controller.load_neutral_positions()
        self.controller.setting_neutral_steering_states()

        self.get_logger().info("Finished calibrating the steering servos")
    
    def camera1_calibration(self):
        self.get_logger().info("Starting stereo camera calibraiton sequence")
    
    def camera2_calibration(self):
        self.get_logger().info("Starting rasPi cam module2 calibraiton sequence")
    
    def imu_calibration(self):
        self.get_logger().info("Starting IMU calibraiton sequence")
    
    def is_armed(self):
        if not self.active:
            self.get_logger().warn("Rover not armed. Remember to 'arm' first.")
            return False
        return True


    ### Callback functions for IMU sensors ###
    def imu_callback(self, msg):
        self.latest_imu[msg.header.frame_id] = msg


    ### Callback functions for stereo camera (D421) ###
    def depth_scan_callback(self, msg):
        self.latest_depth_scan = msg

        center_ranges = []
        angle = msg.angle_min
        for distance in msg.ranges:
            if abs(angle) <= 0.17 and distance >= msg.range_min and distance <= msg.range_max:
                center_ranges.append(distance)
            angle += msg.angle_increment

        if not center_ranges:
            return

        self.latest_center_depth = min(center_ranges)


    ### Callback functions for metal sensor topics ###
    def metal_sensor_callback(self, msg, pin):

        if pin == 17:
            self.gpio17_state = msg.data                

        elif pin == 22:
            self.gpio22_state = msg.data

        elif pin == 27:
            self.gpio27_state = msg.data

        self.get_logger().info(
            f"Pin {pin}: {'HIGH' if msg.data else 'LOW'}"
        )



    ### Need to set autonomous mode up with subscribers for metal_sensor data
    ######## Main functionality - Autonomy response functions #######
    def autonomous_callback(self, msg):
        if not self.is_armed():
            self.get_logger().warn("Autonomous mode did not start. The rover needs to be armed!")
            return
        
        self.get_logger().info("Starting autonomous mode...")
        
        sensorMsg = msg.data.strip().lower()
        self.get_logger().info(f"Received sensor data: {sensorMsg}")
        
        ### State machine ###
        if sensorMsg == "obstacle_detected":
            self.get_logger().info("Obstacle detected! Stopping rover.")
            self.controller.stop()
            self.start_timer("stop_delay", 1.0, self.controller.backward) 
            
            self.get_logger().info("Moving backward and making a stop.")
            self.start_timer("backwards_delay", 3.0, self.controller.stop) 

        elif sensorMsg == "clear_path":
            self.controller.forward()
            self.get_logger().info("Path is clear. Moving forward.")

        elif sensorMsg == "metal_detected":            
            # Alternatively make it stop and use cameras for better recognision with AI
            self.metalSensorController.metal_detected(True)
            self.get_logger().info(f"Metal detected! Number of total detections: {self.metalSensorController.numberOfTimes_MetalDetected} ") # Test
            #Log number of times metal is detected to file. 
        
            #0x68 - imu1
            #0x69 - imu2

        # Implement autonomous behavior logic here, e.g.:
        # - Use sensor data to navigate - IMU at start, turning using point turn etc.
        # - Implement obstacle avoidance
        # - Follow a predefined path or explore randomly

        if self.locomotion_mode == LocomotionModes.ACKERMANN:
            self.controller.ackermann()
            self.get_logger().warn("ACKERMANN modus enabled")
        elif self.locomotion_mode == LocomotionModes.POINT_TURN:
            self.controller.point_turn()
            self.get_logger().warn("POINT_TURN modus enabled")
        elif self.locomotion_mode == LocomotionModes.CRABBING:
            self.controller.crabbing()
            self.get_logger().warn("CRABBING modus enabled")


        else:
            self.get_logger().warn(f"Unknown sensor message: {sensorMsg}")



    ### Callback functions for mainMode topics ###
    def mode_callback(self, msg):
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

            self.cancel_all_timers()
            rclpy.shutdown()

        else:
            self.get_logger().warn(f"Invalid mode: {mainMode}")


    ### Callback functions for locoMode topics ###
    def locomotion_callback(self, msg):
        if not self.is_armed():
            self.get_logger().warn("Locomotion not set. Rover need to be armed! ")
            return
        
        locoMode = msg.data.strip().lower()
        parts = locoMode.split()

        if not parts:
            self.get_logger().warn("Empty locomotion command received")
            return
        
        loco_cmd = parts[0]

        if loco_cmd == "ackermann": # TEST!!!!
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

        elif loco_cmd == "point_turn":
            if len(parts) != 1:
                self.get_logger().warn("Input type required: point_turn")
                return
            self.locomotion_mode = LocomotionModes.POINT_TURN
            self.controller.point_turn()
            self.get_logger().info("point_turn activated")

        elif loco_cmd == "crabbing": # TEST!!!!
            if len(parts) != 1:
                self.get_logger().warn("Input type required: crabbing")
                return
            self.locomotion_mode = LocomotionModes.CRABBING
            self.controller.crabbing()
            self.get_logger().info("crabbing activated")

        else:
            self.get_logger().warn(f"Invalid locomotion mode: {locoMode}")
            return

        self.controller.set_mode(self.locomotion_mode)
        self.get_logger().info(f"Locomotion set to: {self.locomotion_mode.name}") #Test that this one logs correct and not double


    ### Callback functions for command topics ###
    def command_callback(self, msg):
        if not self.is_armed():
            self.get_logger().warn("Ignoring command! The rover is not armed.")
            return
        
        command = msg.data.strip().lower()
        parts = command.split()

        if not parts:
            self.get_logger().warn("Empty command received")
            return
        
        cmd = parts[0]

        ### Main commands for moving the rover
        if cmd == "forward":
            self.controller.forward()
            self.get_logger().info("Moving forward")

        elif cmd == "backward":
            self.controller.backward()
            self.get_logger().info("Moving backward")

        elif cmd == "stop":
            self.controller.stop()
            self.get_logger().info("Stopping rover")

        elif cmd == "forward_turn":
            self.controller.forward_turn()
            self.get_logger().info("Setting forward motion")

        elif cmd == "backward_turn":
            self.controller.backward_turn()
            self.get_logger().info("Setting backward motion")

        

        elif cmd == "left_turn": 
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
            
            # Need to fix stearing for different modes.
            self.controller.left_turn()
            self.get_logger().info("Turning left " + str(turn_angle) + " degrees. ")

        elif cmd == "right_turn":  
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

            # Example angle, adjust as needed
            self.controller.right_turn()
            self.get_logger().info("Turning right " + str(turn_angle) + " degrees. ")

        # Setts all wheels to degrees given in steering_neatural 
        elif cmd == "reset_steering": 
            self.controller.reset_to_neutral()
            self.get_logger().info("Resetting steering servos")

        # Sets a specific wheel at a given degree
        elif cmd == "set_wheel_steering": # TEST
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

        #Updates neutral steering parameters with current_steering_angles - straight motion default
        elif cmd == "update_steering": 
            for wheel, angle in self.controller.current_steering_angles.items():
                self.controller.update_steering_neutral_positions(wheel, angle)

            self.controller.save_neutral_positions()
            self.get_logger().info("Updated steering neutral positions to current angles and saved to file ")

        else:
            self.get_logger().warn(f"Unknown command: {command}")


def main(args=None):
    rclpy.init(args=args)
    mainLogic_node = MainLogicNode()
    
    try:
        rclpy.spin(mainLogic_node)
    
    except ExternalShutdownException:
        pass

    finally:
        mainLogic_node.cancel_all_timers()
        mainLogic_node.controller.stop()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
