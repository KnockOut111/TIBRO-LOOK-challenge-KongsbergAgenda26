# Main logic for the navigation thread. 
# This file is responsible for controlling the locomotion of the robot, 
# and will use the locomotionController and forwardMotionDriver to achieve this. 
# It will also handle the logic for switching between different locomotion modes, 
# and will be responsible for sending commands to the motors based on the current mode and the desired movement.

# Need to adapt to Ros2 yazzy and using nodes. 
# Fix locomotion modes to work as it should, wheels are never set back to 90 degrees after turning, and point turn and crab steering are not implemented propperly.

print("Starting mainLogic module...")

#from forwardMotionDriver import forward_motion, backward_motion, stop_motion
from localTesting.locomotionControllerLocal import LocomotionController, LocomotionModes

controller = LocomotionController()

def set_locomotion_mode():
    mode = input("Enter locomotion mode (ackermann/point_turn/crabbing): ").strip().lower()

    if mode == "ackermann":
        controller.set_mode(LocomotionModes.ACKERMANN)
        print("Ackermann mode activated.")
            
    elif mode == "point_turn":
        controller.set_mode(LocomotionModes.POINT_TURN)
        print("Point turn mode activated.")

    elif mode == "crabbing":
        controller.set_mode(LocomotionModes.CRABBING)
        print("Crabbing mode activated.")

    else:
        print("Error: invalid locomotion mode!")
        return False

    return True

# Main loop
def main():

    while True:
        mode = input("Enter mode (launch/quit): ").strip().lower()

        if mode == "launch":
            if not set_locomotion_mode():
                continue
            controller.stop() #forward_motion() #remove later????
            print("Rover launched. Awaiting commands...")

            while True:
                command = input("The roverPi is launched and in active state with locomotion mode: " + str(controller.get_mode()) + ". Enter command (forward/backward/stop/left_turn/right_turn/change_locomotion/quit): ").strip().lower()

                if command == "forward":
                    controller.forward()
                    print("Moving forward...")

                elif command == "backward":
                    controller.backward()
                    print("Moving backward...")

                elif command == "stop":
                    controller.stop()
                    print("Rover stopped.")

                elif command == "left_turn":
                    controller.set_all_steering(90 - 45)  # Example angle, adjust as needed
                    print("Turning left...")

                elif command == "right_turn":
                    controller.set_all_steering(90 + 45)  # Example angle, adjust as needed
                    print("Turning right...")

                elif command == "change_locomotion":
                    set_locomotion_mode()
                    print("Locomotion mode changed.")
                    continue

                elif command == "quit":
                    controller.stop()
                    print("Exiting program...")
                    raise SystemExit

                else:
                    print("Error: unknown command!")

        elif mode == "quit":
            controller.stop()
            print("Exiting program...")
            raise SystemExit

        else:
            print("Error: invalid mode!")

if __name__ == "__main__":
    main()