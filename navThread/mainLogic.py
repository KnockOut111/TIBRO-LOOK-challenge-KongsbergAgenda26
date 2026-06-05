import rclpy

from typing import Callable
from rclpy.timer import Timer
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.executors import ExternalShutdownException

from locomotionController import LocomotionController, LocomotionModes, SteeringServos


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
        self.active = False
        self.locomotion_mode = LocomotionModes.CRABBING
        self.steering_neutral = {
            SteeringServos.FL: 90,
            SteeringServos.FR: 90,
            SteeringServos.CL: 90,
            SteeringServos.CR: 90,
            SteeringServos.RL: 90,
            SteeringServos.RR: 90,
        }

        # Timer setup
        self.active_timers: dict[str, Timer] = {}

        # Subscriptions
        self.create_subscription(String, "/rover/mainMode", self.mode_callback, 10)
        self.create_subscription(String, "/rover/locoMode", self.locomotion_callback, 10)
        self.create_subscription(String, "/rover/command", self.command_callback, 10)
        self.create_subscription(String, "/rover/sensorMsg", self.sensor_callback, 10)
        
        # Publishers
        self.shutdown_pub = self.create_publisher(String, "/rover/system_shutdown",10)


        self.init_roverPi()
        self.get_logger().info("MainLogicNode is now running...")


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

    def wheel_calibration(self):
        self.get_logger().info("Initializing the steering servos...")

        self.controller.load_neutral_positions(self.steering_neutral)
        self.controller.initialize_steering_state(self.steering_neutral)

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
            self.locomotion_mode = LocomotionModes.POINT_TURN
            self.controller.point_turn()
            self.get_logger().info("Point turn activated")

        elif loco_cmd == "crabbing": # TEST!!!!
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

        # Implement missing command handling logic here, e.g.:
        if cmd == "forward":
            self.controller.forward()
            self.get_logger().info("Moving forward")

        elif cmd == "backward":
            self.controller.backward()
            self.get_logger().info("Moving backward")

        elif cmd == "stop":
            self.controller.stop()
            self.get_logger().info("Stopping rover")

        elif cmd == "left_turn": # TEST!!!!
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

        elif cmd == "right_turn":  # TEST!!!!
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

        elif cmd == "reset_steering": # Out of date!
            self.controller.set_all_steering(90)
            self.get_logger().info("Resetting steering")

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

        elif cmd == "update_steering": # TEST!!! - not done - work here
            for wheel, angle in self.controller.current_steering_angles.items():
                self.controller.update_steering_neutral_positions(wheel, angle, self.steering_neutral)

            self.controller.save_neutral_positions(self.steering_neutral)
            self.get_logger().info("Updated steering neutral positions to current angles and saved to file ")

        else:
            self.get_logger().warn(f"Unknown command: {command}")


    ### Autonomy response functions ###
    def autonomous_mode(self, msg):
        if not self.is_armed():
            self.get_logger().warn("Autonomous mode did not start. The rover needs to be armed!")
            return
        
        self.get_logger().info("Starting autonomous mode...")
        
        sensorMsg = msg.data.strip().lower()
        self.get_logger().info(f"Received sensor data: {sensorMsg}")
        
        if sensorMsg == "obstacle_detected":
            self.get_logger().info("Obstacle detected! Stopping rover.")
            self.start_timer("stop_delay",1.0, self.controller.stop())  # Pause briefly before moving backward
            
            self.get_logger().info("Moving backward and making a stop.")
            self.start_timer(3.0, self.controller.backward())  # Move backward for a short duration
            self.controller.stop()

        elif sensorMsg == "clear_path":
            self.controller.forward()
            self.get_logger().info("Path is clear. Moving forward.")

        elif sensorMsg == "metal_detected":
            # self.controller.logMetal() # Need to implement this function in the locomotion controller, to log the detection and maybe trigger some specific behavior, e.g. stopping and moving backward for a closer investigation of the metal object with the cameras, and then publish the findings to a topic for further analysis.
            
            ### Thinking about dropping this and making a simpler solution ###
            # self.controller.stop()  
            # self.start_one_shot_timer(1.0, lambda: None)  # Pause briefly before moving backward
            # self.controller.backward()
            # self.start_one_shot_timer(2.0, lambda: None)  # Move backward for a short duration
            # #Run piCam AI image recognition for more detailed investigation of the metal object or similar, 
            # # and publish findings to a topic for further analysis.
            # self.controller.stop()  
            self.get_logger().info("Metal detected! Stopping rover and moving backward for more detailed investigation.")

        # Implement autonomous behavior logic here, e.g.:
        # - Use sensor data to navigate
        # - Implement obstacle avoidance
        # - Follow a predefined path or explore randomly

        else:
            self.get_logger().warn(f"Unknown sensor message: {sensorMsg}")

def main(args=None):
    rclpy.init(args=args)
    mainLogic_node = MainLogicNode()
    
    try:
        rclpy.spin(mainLogic_node)
    
    except ExternalShutdownException:
        pass

    finally:
        mainLogic_node.cancel_recovery_sequence()
        mainLogic_node.controller.stop()
        mainLogic_node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()