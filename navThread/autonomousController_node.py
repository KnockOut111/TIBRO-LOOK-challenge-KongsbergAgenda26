import math
import random
from enum import Enum, auto

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from std_msgs.msg import String
from sensor_msgs.msg import Imu


TICK_PERIOD_S = 0.1

RAMP_PITCH_THRESHOLD_RAD = math.radians(10.0)
SCAN_DURATION_S = 18.0

RECOVERY_STOP_S = 1.0
RECOVERY_BACKUP_S = 3.0
RECOVERY_TURN_MIN_S = 2.0
RECOVERY_TURN_MAX_S = 4.0


class RoverState(Enum):
    IDLE = auto()
    STARTING = auto()
    SCANNING = auto()
    DRIVING = auto()
    OBSTACLE_RECOVERY = auto()
    STOPPED = auto()


class RecoverySubState(Enum):
    STOPPING = auto()
    BACKING_UP = auto() # Maybe delete? - 
    TURNING = auto()
    RESUMING = auto()

#Se på logikken med obstacle detected og metal detected!
class AutonomousController(Node):
    def __init__(self):
        super().__init__("autonomous_controller_node")

        # pubs
        self.mainState_pub = self.create_publisher(String, "/rover/mainMode", 10)
        self.loco_mode_pub = self.create_publisher(String, "/rover/locoMode", 10)
        self.command_pub = self.create_publisher(String, "/rover/command", 10)
        self.fsm_state_pub = self.create_publisher(String, "/rover/fsm_state", 10)

        # subs
        self.create_subscription( String, "/autonomousController_node/start_autonomous_program", self.start_program_callback, 10)
        self.create_subscription(String, "/rover/system_shutdown", self.shutdown_callback, 10)
        self.create_subscription(String, "/rover/mainMode", self.main_mode_callback, 10)
        self.create_subscription(Imu, "/sensors/imu_68", self.imu_callback, 10)
        self.create_subscription(Imu, "/sensors/imu_69", self.imu_callback, 10)
        self.create_subscription(String, "/sensors/obstacle_state", self.obstacle_callback, 10)
        self.create_subscription(String, "metal_sensor/metal_detected", self.metal_callback, 10)

        # FSM
        self.current_state = RoverState.IDLE
        self.recovery_substate = None
        self.state_entered_at = self.get_clock().now()
        self.substate_entered_at = self.get_clock().now()
        self.turn_duration_s = RECOVERY_TURN_MIN_S

        # sensor
        self.is_armed = False
        self.latest_imu = {}
        self.latest_obstacle = "clear_path"
        self.metal_count = 0

        # tick loop
        self.tick_timer = self.create_timer(TICK_PERIOD_S, self.tick)

        self.get_logger().info("AutonomousController (brain) running. Waiting for arm + start.")

        # callbacks
    def imu_callback(self, msg):
        self.latest_imu[msg.header.frame_id] = msg

    def obstacle_callback(self, msg):
        self.latest_obstacle = msg.data.strip().lower()

    def metal_callback(self, msg):
        if msg.data.strip().lower() == "metal_detected":
            self.metal_count += 1
            self.get_logger().info(f"Metal detected (total: {self.metal_count})")

    def main_mode_callback(self, msg):
        mode = msg.data.strip().lower()
        if mode == "arm":
            self.is_armed = True
        elif mode == "quit":
            self.is_armed = False
            self.transition(RoverState.STOPPED)

    def start_program_callback(self, msg):
        if msg == "start_autonomous_system":
            if not self.is_armed:
                self.get_logger().warn("Start trigger ignored: rover not armed.")
                return
            if self.current_state != RoverState.IDLE:
                self.get_logger().warn(f"Start trigger ignored: already in {self.current_state.name}.")
                return
            self.transition(RoverState.STARTING)

    def shutdown_callback(self, msg):
        if msg.data.strip().lower() == "shutdown":
            self.get_logger().info("Shutdown received.")
            rclpy.shutdown()

    # FSM helpers
    def transition(self, new_state):
        self.get_logger().info(f"FSM: {self.current_state.name} -> {new_state.name}")
        self.current_state = new_state
        self.state_entered_at = self.get_clock().now()
        self.recovery_substate = None

        fsm_msg = String()
        fsm_msg.data = new_state.name
        self.fsm_state_pub.publish(fsm_msg)

    def enter_recovery_substate(self, substate):
        self.recovery_substate = substate
        self.substate_entered_at = self.get_clock().now()
        if substate == RecoverySubState.TURNING:
            self.turn_duration_s = random.uniform(RECOVERY_TURN_MIN_S, RECOVERY_TURN_MAX_S) # Fix to work for accurate imu sensor input

    def elapsed_in_state(self):
        return (self.get_clock().now() - self.state_entered_at).nanoseconds / 1e9

    def elapsed_in_substate(self):
        return (self.get_clock().now() - self.substate_entered_at).nanoseconds / 1e9

    # publisher wrappers 

    def set_main_mode(self, mode):
        msg = String()
        msg.data = mode
        self.mainState_pub.publish(msg)

    def set_loco_mode(self, mode):
        msg = String()
        msg.data = mode
        self.loco_mode_pub.publish(msg)

    def set_command(self, cmd):
        msg = String()
        msg.data = cmd
        self.command_pub.publish(msg)

    # tick loop
    def tick(self):
        handler = {
            RoverState.IDLE: self.tick_idle,
            RoverState.STARTING: self.tick_starting,
            RoverState.SCANNING: self.tick_scanning,
            RoverState.DRIVING: self.tick_driving,
            RoverState.OBSTACLE_RECOVERY: self.tick_obstacle_recovery,
            RoverState.STOPPED: self.tick_stopped,
        }[self.current_state]
        handler()

    def tick_idle(self):
        pass

    def tick_starting(self):
        pitch = self.current_pitch()
        if pitch is None:
            # No IMU yet — drive forward cautiously to leave the ramp.
            self.set_command("forward")
            return

        if abs(pitch) > RAMP_PITCH_THRESHOLD_RAD:
            self.set_command("forward")
        else:
            self.set_command("stop")
            self.transition(RoverState.SCANNING)

    def tick_scanning(self):
        if self.elapsed_in_state() < 0.2:
            self.set_loco_mode("point_turn")
            self.set_command("forward")
            return

        if self.elapsed_in_state() >= SCAN_DURATION_S:
            self.set_command("stop")
            self.transition(RoverState.DRIVING)

    def tick_driving(self):
        if self.latest_obstacle == "obstacle_detected":
            self.transition(RoverState.OBSTACLE_RECOVERY)
            self.enter_recovery_substate(RecoverySubState.STOPPING)
            return

        self.set_loco_mode("crabbing")
        self.set_command("forward")

    def tick_obstacle_recovery(self):
        if self.recovery_substate is None:
            self.enter_recovery_substate(RecoverySubState.STOPPING)

        sub = self.recovery_substate
        elapsed = self.elapsed_in_substate()

        if sub == RecoverySubState.STOPPING:
            self.set_command("stop")
            if elapsed >= RECOVERY_STOP_S:
                self.enter_recovery_substate(RecoverySubState.BACKING_UP)

        elif sub == RecoverySubState.BACKING_UP:
            self.set_command("backward")
            if elapsed >= RECOVERY_BACKUP_S:
                self.enter_recovery_substate(RecoverySubState.TURNING)

        elif sub == RecoverySubState.TURNING:
            self.set_loco_mode("point_turn")
            self.set_command("forward")
            if elapsed >= self.turn_duration_s:
                self.enter_recovery_substate(RecoverySubState.RESUMING)

        elif sub == RecoverySubState.RESUMING:
            self.set_command("stop")
            self.transition(RoverState.DRIVING)

    def tick_stopped(self):
        self.set_command("stop")

    # IMU helpers

    def current_pitch(self):
        # Prefer imu_68; fall back to imu_69.
        imu = self.latest_imu.get("imu_68") or self.latest_imu.get("imu_69")
        if imu is None:
            return None
        return self.pitch_from_quaternion(imu.orientation)

    @staticmethod
    def pitch_from_quaternion(q):
        sinp = 2.0 * (q.w * q.y - q.z * q.x)
        if sinp >= 1.0:
            return math.pi / 2.0
        if sinp <= -1.0:
            return -math.pi / 2.0
        return math.asin(sinp)


#### Shutdown sequence ####
    def destroy_node(self):
        if hasattr(self, "i2c") and hasattr(self.i2c, "deinit"):
            self.i2c.deinit()
        super().destroy_node()
    
    def shutdown_callback(self, msg):
        if msg.data.strip().lower() == "shutdown":
            self.get_logger().info("Shutdown signal received. Shutting down AutonomousController node.")
            rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    node = AutonomousController()

    try:
        rclpy.spin(node)
    except ExternalShutdownException:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
