# Main logic for the navigation thread. 
# This file is responsible for controlling the locomotion of the robot, 
# and will use the locomotionController and forwardMotionDriver to achieve this. 
# It will also handle the logic for switching between different locomotion modes, 
# and will be responsible for sending commands to the motors based on the current mode and the desired movement.

print("Starting mainLogic module...")

from forwardMotionDriver import forward_motion, backward_motion, stop_motion
#from locomotionController import set_locomotion_mode, LocomotionModes


# Main loop
while True:
    mode = input("Enter mode (forward_motion_mode/still_motion_mode/quit): ").strip().lower()

    if mode == "forward_motion_mode":
        stop_motion() #forward_motion()

        while True:
            command = input("Forward mode active. Enter command (forward/backward/stop/quit): ").strip().lower()

            if command == "forward":
                forward_motion()

            elif command == "backward":
                backward_motion()

            elif command == "stop":
                stop_motion()

            elif command == "quit":
                stop_motion() #could be we do not want it to stop when quitting forward motion mode, but for safety we will stop it here for now.
                print("Exiting forward motion mode...")
                raise SystemExit

            else:
                print("Error: unknown command!")

    elif mode == "still_motion_mode":
        stop_motion()
        print("Still motion mode activated.")

    elif mode == "quit":
        stop_motion()
        break

    else:
        print("Error: invalid mode!")

    # case "locomotion_mode":
    #     set_locomotion_mode(LocomotionModes.ACKERMANN)