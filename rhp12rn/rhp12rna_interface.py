"""
MIT License

Copyright (c) 2021 Tim Schneider

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import time
import numpy as np

from rhp12rn import RHP12RN, RHP12RNAConnector

class RHP12RNAInterface:
    # Initialise the gripper
    def __init__(self, mode='position'):
        # Connect to the gripper - in our setup, the baudrate is 2M
        self.connector = RHP12RNAConnector(device="/dev/ttyUSB0", baud_rate=2000000, dynamixel_id=1)
        self.connector.connect()
        self.gripper = RHP12RN(self.connector)

        # Standard gripper setup - must be done when torque is disabled
        self.gripper.torque_enabled = False
        self.gripper.position_limit_high = 660
        self.pos_limit_high = self.gripper.position_limit_high
        self.pos_limit_low = self.gripper.position_limit_low

        # determine operating mode
        self.mode = mode
        if self.mode == 'position':
            self.position_control_setup()
        elif self.mode == 'current':
            self.current_control_setup()
        else:
            raise Exception("Mode not recognised. Please choose position or current.")


        self.gripper.torque_enabled = True
        print("Enabled motor.")

    def position_control_setup(self, gain=50):
        self.gripper.enable_position_control()
        # Set P gain - note the original value was 193
        self.gripper.position_p_gain = gain

    def current_control_setup(self):
        self.gripper.enable_current_control()
        self.gripper.goal_current = 0

    def open(self):
        self.gripper.goal_position_rel = 0.0
        while self.gripper.current_position_rel > 0.05:
            time.sleep(0.01)
        print("Gripper fully opened.")

    def open_constant_current(self):
        while self.gripper.current_position_rel > 0.05:
            self.constant_current(-50)
            time.sleep(0.01)
        # brings the gripper to a stop
        self.constant_current(0)
        print("Gripper fully opened.")

    def close_constant_current_until_stop(self,final_current=0):
        # final current basically specifies the behavior after. If set to 0, the gripper will just stop
        # eventually you want to set it higher to achieve a certain force

        # function terminates when current position and position 100 timesteps ago are the same
        curr_pos_arr = -1 * np.ones(100)
        const_closing_current = 10

        while True:
            read_res = self.read_status()
            curr_pos = read_res['present_position']
            curr_pos_rel = self.gripper.abs_to_rel_pos(curr_pos)
            if (curr_pos_rel<0.01):
                # this means gripper is fully closed -> raise an error
                self.constant_current(0)
                raise Exception("Close constant current until stop function failed. Gripper is fully closed.")
                break
            else:
                self.constant_current(const_closing_current)

            curr_pos_arr = np.roll(curr_pos_arr, 1)
            curr_pos_arr[0] = curr_pos
            if curr_pos_arr[0] == curr_pos_arr[99]:
                print ("Position not changing any longer - end close gripper function.")
                break

        # now linearily increase the closing current to the final current if it is not 0
        if final_current != 0:
            current_current = const_closing_current
            while current_current < final_current:
                # increment in steps of 10 mA
                current_current = min(current_current + 10, final_current)
                self.constant_current(final_current)
        else:
            self.constant_current(0)

    def constant_current(self, value=0):
        # set the current to a constant value in mA - negative is opening, positive is closing, remember to convert before
        self.gripper.goal_current = self.convert_current(value)

    def convert_current(self, value):
        # conversion is needed as the field assumes unsigned value!
        if value < 0:
            value = 65536 + value
        return value

    def read_status(self):
        return self.gripper.read_gripper_status

    def close_w_const_velocity(self, velocity=15):
        # close the gripper by trying to track a velocity through position control.
        # function terminates when current position and position 100 timesteps ago are the same

        curr_pos_arr = -1*np.ones(100)
        # note in general, every read and write takes around 1ms so this whole loop should take around 2 ms
        while True:
            start_iter = time.time()
            read_res = self.read_status()
            # print (read_res['present_velocity'])
            # print (read_res['present_current'])
            # print (self.gripper.current_position)
            curr_pos = read_res['present_position']
            curr_pos_arr = np.roll(curr_pos_arr,1)
            curr_pos_arr[0] = curr_pos
            # print (read_res['real_time_tick'])

            self.gripper.goal_position = np.clip(curr_pos + velocity,self.pos_limit_low,self.pos_limit_high)
            # print (read_res)
            if curr_pos_arr[0] == curr_pos_arr[99]:
                print ("Position not changing any longer - end close gripper function.")
                break
            # print ("Iteration took ", time.time()-start_iter)

    def shutdown(self):
        # reason for while loop: depending on position in code, the port might be busy and the shutdown might fail
        # thus, we try again after some wait (after which the port will be free) until it succeeds
        while True:
            try:
                self.low_level_shutdown()
                break
            except:
                print ("Failed to shutdown gripper, retrying...")
                time.sleep(0.1)

    def low_level_shutdown(self):
        # Disable the gripper and disconnect
        self.gripper.torque_enabled = False
        print("Disabled motor.")
        self.connector.disconnect()


def make_manoeuvre(gripper_handle):
    '''
    This function actually defines the manoeuvre to be performed.
    '''
    gripper_handle.open()
    input ("Press enter to close gripper")
    gripper_handle.close_w_const_velocity(10)


def main():
    robotis_gripper_handle = RHP12RNAInterface()
    try:
        make_manoeuvre(robotis_gripper_handle)
    finally:
        robotis_gripper_handle.shutdown()

if __name__ == '__main__':
    main()