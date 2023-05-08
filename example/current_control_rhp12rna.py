"""
MIT License

Copyright (c) 2023 Niklas Funk

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

from rhp12rn import RHP12RNAInterface

def make_manoeuvre(gripper_handle):
    '''
    This function actually defines the manoeuvre to be performed.
    '''
    gripper_handle.open_constant_current()
    input ("Press enter to close gripper")
    gripper_handle.close_constant_current_until_stop(final_current=0)
    # gripper_handle.close_constant_current_until_stop(final_current=100)
    print ("Gripper closed")
    time.sleep(2)

def main():
    robotis_gripper_handle = RHP12RNAInterface(mode="current")
    try:
        make_manoeuvre(robotis_gripper_handle)
    finally:
        robotis_gripper_handle.shutdown()

if __name__ == '__main__':
    main()