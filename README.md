# python-rhp12rn-controller

Python controller for the ROBOTIS RH-P12-RN and RH-P12-RN(A) grippers.

## Installation

This package can be installed via pip:
```bash
pip install git+https://github.com/TimSchneider42/python-rhp12rn-controller.git
```

## Latency

Since Ubuntu 16.04 (Xenial Xerus), the kernel's USB serial driver has a default latency of 16ms. 
This can be reduced to 1ms by executing the following command:

```bash
./scripts/reduce_latency.sh
```

## Usage

First, create a `RHP12RNConnector` or `RHP12RNAConnector` instance depending on your gripper model and call the `connect()` function to establish a serial connection to the gripper:

```python
from rhp12rn import RHP12RNAConnector

connector = RHP12RNAConnector(device="/dev/ttyUSB0", baud_rate=57600, dynamixel_id=1)
connector.connect()
...
connector.disconnect()
```

`RHP12RNAConnector` instances can also be used as context managers:
```python
with RHP12RNAConnector(device="/dev/ttyUSB0", baud_rate=57600, dynamixel_id=1) as connector:
    ...
```

The `connector` object allows reading and writing of arbitrary addresses of the gripper's control table:
```python
print(connector.read_field("torque_enable"))
connector.write_field("torque_enable", 1)
print(connector.read_field("torque_enable"))
```
For a comprehensive list of its entries, refer to <https://emanual.robotis.com/docs/en/platform/rh_p12_rna/> or <https://emanual.robotis.com/docs/en/platform/rh_p12_rn/>.
Alternatively, all entries are listed in `rhp12rn_connector.py` and `rhp12rna_connector.py`.
Note that the motors have to be disabled (`"torque_enabled"` has to be set to 0) for EEPROM values to be written, while RAM values can be written at any time.

For convenience, the `RHP12RN` class provides direct access to the most commonly used fields:

```python
import time
from rhp12rn import RHP12RN

rhp12rn = RHP12RN(connector)
rhp12rn.torque_enabled = True
rhp12rn.goal_position = 1.0
time.sleep(3.0)
rhp12rn.torque_enabled = False
```

For a full example of the usage of this package, refer to `example/open_close.py`.

### Finding the correct baud rate and Dynamixel ID
If the baud rate and/or Dynamixel ID is unknown, the `find_grippers` method can be used to find those parameters by performing a full sweep. It can be invoked as follows:
```python
from rhp12rn import find_grippers
found_grippers = find_grippers(device="/dev/ttyUSB0")
```