# Main logic for the navigation thread. 
# This file is responsible for controlling the locomotion of the robot, 
# and will use the locomotionController and forwardMotionDriver to achieve this. 
# It will also handle the logic for switching between different locomotion modes, 
# and will be responsible for sending commands to the motors based on the current mode and the desired movement.

print("Starting mainLogic module...")

from forwardMotionDriver import set_forward_motion_mode
#from locomotionController import set_locomotion_mode, LocomotionModes


# Main loop
while True:
    # Here we would have the logic for switching between different locomotion modes, 
    # and for sending commands to the motors based on the current mode and the desired movement.

    command = input("Enter command (forward_motion_mode/still_motion_mode): ").strip().lower()

    match(command):
        case "forward_motion_mode":
            set_forward_motion_mode(True)
            print("Forward motion activated. ")
        case "still_motion_mode":
            set_forward_motion_mode(False)
            print("Forward motion deactivated. ")



    # case "locomotion_mode":
    #     set_locomotion_mode(LocomotionModes.ACKERMANN)