import time

from rhp12rn import RHP12RN, RHP12RNAConnector

with RHP12RNAConnector(device="/dev/ttyUSB0", baud_rate=57600, dynamixel_id=1) as connector:
    rhp12rn = RHP12RN(connector)

    # Make sure torque is disabled before writing EEPROM values
    rhp12rn.torque_enabled = False
    rhp12rn.position_limit_high = 660

    rhp12rn.torque_enabled = True
    print("Enabled motor.")

    print("Opening gripper...")
    rhp12rn.goal_position_rel = 0.0
    while rhp12rn.current_position_rel > 0.01:
        time.sleep(0.1)
        print("\rCurrent position: {}".format(rhp12rn.current_position_rel), end="")
    print("\rCurrent position: {}".format(rhp12rn.current_position_rel))
    print("Gripper fully opened.")

    time.sleep(1.0)

    print("Closing gripper...")
    rhp12rn.goal_position_rel = 1.0
    while rhp12rn.current_position_rel < 0.99:
        time.sleep(0.1)
        print("\rCurrent position: {}".format(rhp12rn.current_position_rel), end="")
    print("\rCurrent position: {}".format(rhp12rn.current_position_rel))
    print("Gripper fully closed.")

    rhp12rn.torque_enabled = False
    print("Disabled motor.")
