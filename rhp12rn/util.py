from typing import Sequence, Tuple, List

from .dynamixel_connector import DynamixelConnector, Field


def find_grippers(device: str = "/dev/ttyUSB0",
                  baud_rates: Sequence[int] = (9600, 57600, 115200, 1000000, 2000000, 3000000, 4000000, 4500000)) \
        -> List[Tuple[str, int, int]]:
    """
    Sweeps the specified baud rates and all possible dynamixel ids to find connected RH-P12-RN[(A)] grippers.
    :param baud_rates: Baud rates to test
    :return: List of tuples containing the model name, baud rate and Dynamixel id of each identified gripper.
    """
    found_devices = []
    for r in baud_rates:
        print("Testing baud rate {}...".format(r))
        for i in range(1, 254):
            try:
                with DynamixelConnector(
                        device=device, fields=[Field(0, "H", "model_number", "Model Number", False, 0)], baud_rate=r,
                        dynamixel_id=i) as connector:
                    model_number = connector.read_field("model_number")
                    if model_number in [35073, 35074]:
                        model_name = "RH-P12-RN" if model_number == 35073 else "RH-P12-RN(A)"
                        found_devices.append((model_name, r, i))
                        print("Found {} with ID {} at baud rate {}".format(model_name, i, r))
            except ValueError:
                pass
    return found_devices
