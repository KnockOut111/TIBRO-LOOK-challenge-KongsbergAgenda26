import rclpy

from typing import Callable
from rclpy.timer import Timer
from rclpy.node import Node
from std_msgs.msg import String
from rclpy.executors import ExternalShutdownException

from locomotionController import LocomotionController, LocomotionModes, SteeringServos

#0x68 - imu1
#0x69 - imu2

# point turn need adjustments and crab steering are not implemented propperly.
# Front Right wheel is still not working as intended. Need to find solution.
## Test and start implementing init for cameras and IMU as well

## Continue with steering servo initialization and calibration, and then implement the different locomotion modes propperly.
## Test it!!

class MainLogicNode(Node):
    def __init__(self):
        super().__init__("mainLogic_node")
        
        self.controller = LocomotionController()

        self.active = False
        self.locomotion_mode = LocomotionModes.CRABBING

        # Timer setup
        self.active_timers: dict[str, Timer] = {}

        # Subscriptions
        self.create_subscription(String, "/rover/mainMode", self.mode_callback, 10)
        self.create_subscription(String, "/rover/locoMode", self.locomotion_callback, 10)
        self.create_subscription(String, "/rover/command", self.command_callback, 10)

        # Publishers
        self.shutdown_pub = self.create_publisher(String, "/rover/system_shutdown", 10)


        self.init_roverPi()
        self.get_logger().info("MainLogicNode is now running...")



#### Callback functions ####

########### Time functions ################################################################
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


########### Main init function ################################################################
    ### Initialization and calibration functions ###
    def init_roverPi(self):
        self.get_logger().info("Initializing roverPi system...")
    
        #Need to implement initialization logic here ....
        self.wheel_calibration()
        self.camera1_calibration()
        self.camera2_calibration()
        self.imu_calibration()
        self.get_logger().info("Initializing of tibro-roverPi is completed")


########### Calibration functions ################################################################
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


########### Helper functions ################################################################
    def is_armed(self):
        if not self.active:
            self.get_logger().warn("Rover not armed. Remember to 'arm' first.")
            return False
        return True
    
    def destroy_node(self):
        super().destroy_node()


############## Main modes (arm and quit) #############################################################
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

############## LocoMode topics (ackermann, point_turn, crabbing) #############################################################
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


############## Command topics (forward, backward, stop, forward_turn, backward_turn, left_turn, right_turn, reset_steering, set_wheel_steering, update_steering) #############################################################
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
            if self.locomotion_mode == LocomotionModes.CRABBING:
                self.controller.crab_straight()

            self.controller.forward()
            self.get_logger().info("Moving forward")

        elif cmd == "backward":
            if self.locomotion_mode == LocomotionModes.CRABBING:
                self.controller.crab_straight()

                self.controller.backward()
                self.get_logger().info("Moving backward")

        elif cmd == "stop":
            self.controller.stop()
            self.get_logger().info("Stopping rover")

        elif cmd == "left_turn":
            if self.locomotion_mode == LocomotionModes.CRABBING:
                self.controller.crab_sideways()
                self.controller.backward()
<<<<<<< Updated upstream
            elif self.locomotion_mode == LocomotionModes.POINT_TURN:
                self.controller.point_turn_left()
=======
                self.get_logger().info("Crabbing left")
            elif self.locomotion_mode == LocomotionModes.POINT_TURN:
                self.controller.forward_pointTurn_left
                self.get_logger().info("Turning right")
>>>>>>> Stashed changes
            else:
                self.controller.left_turn()
            # try:
            #     turn_angle = int(parts[1])
            # except ValueError:
            #     self.get_logger().warn(f"Invalid angle: {parts[1]}")
            #     return
            # except IndexError:
            #     self.get_logger().warn("Turn angle required for left_turn")
            #     return
            
            # Need to fix stearing for different modes.

            # self.get_logger().info("Turning left " + str(turn_angle) + " degrees. ")

        elif cmd == "right_turn":
            if self.locomotion_mode == LocomotionModes.CRABBING:
                self.controller.crab_sideways()
                self.controller.forward()
<<<<<<< Updated upstream
            elif self.locomotion_mode == LocomotionModes.POINT_TURN:
                self.controller.point_turn_right()
=======
                self.get_logger().info("Crabbing right")
            elif self.locomotion_mode == LocomotionModes.POINT_TURN:
                self.controller.forward_pointTurn_right
                self.get_logger().info("Turning left in point_mode")
>>>>>>> Stashed changes
            else:
                self.controller.right_turn()
                
            # try:
            #     turn_angle = int(parts[1])
            # except ValueError:
            #     self.get_logger().warn(f"Invalid angle: {parts[1]}")
            #     return
            # except IndexError:
            #     self.get_logger().warn("Turn angle required for right_turn")
            #     return

            # Example angle, adjust as needed
            #self.controller.right_turn()
            #self.get_logger().info("Turning right")
            #self.get_logger().info("Turning right " + str(turn_angle) + " degrees. ")



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
