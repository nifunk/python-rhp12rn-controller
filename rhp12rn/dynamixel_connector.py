import struct
from typing import Optional, NamedTuple, Dict, Sequence

from dynamixel_sdk import PortHandler, PacketHandler

Field = NamedTuple("Field", (
    ("address", int), ("data_type", str), ("name", str), ("desc", str), ("writable", bool),
    ("initial_value", Optional[int])))


class DynamixelConnector:
    def __init__(self, fields: Sequence[Field], device: str = "/dev/ttyUSB0", baud_rate: int = 57600,
                 dynamixel_id: int = 1):
        self.__baud_rate = baud_rate
        self.__dynamixel_id = dynamixel_id
        self.__device = device
        self.__port_handler: Optional[PortHandler] = None
        self.__packet_handler = PacketHandler(2.0)
        self.__field_dict = {f.name: f for f in fields}

    def connect(self):
        assert not self.connected, "Already connected."
        self.__port_handler = PortHandler(self.__device)

        if not self.__port_handler.openPort():
            self.__port_handler = None
            raise ValueError("Failed to open port.")

        if not self.__port_handler.setBaudRate(self.__baud_rate):
            self.disconnect()
            raise ValueError("Failed to set baud rate.")

    def disconnect(self):
        if self.connected:
            self.__port_handler.closePort()
            self.__port_handler = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def read_field(self, field_name: str):
        assert self.connected, "Controller is not connected."
        field = self.__field_dict[field_name]
        data_raw, comm_result, error = self.__packet_handler.readTxRx(
            self.__port_handler, self.__dynamixel_id, field.address, struct.calcsize(field.data_type))
        if comm_result != 0:
            raise ValueError(
                "Encountered communication error during reading: {}".format(
                    self.__packet_handler.getTxRxResult(comm_result)))
        elif error != 0:
            raise ValueError(
                "Encountered packet error during reading: {}".format(self.__packet_handler.getRxPacketError(error)))

        return struct.unpack("<{}".format(field.data_type), bytes(data_raw))[0]

    def write_field(self, field_name: str, value: int):
        assert self.connected, "Controller is not connected."
        field = self.__field_dict[field_name]

        data = list(struct.pack("<{}".format(field.data_type), value))

        comm_result, error = self.__packet_handler.writeTxRx(
            self.__port_handler, self.__dynamixel_id, field.address, len(data), data)
        if comm_result != 0:
            raise ValueError(
                "Encountered communication error during writing: {}".format(
                    self.__packet_handler.getTxRxResult(comm_result)))
        elif error != 0:
            raise ValueError(
                "Encountered packet error during writing: {}".format(self.__packet_handler.getRxPacketError(error)))

    @property
    def connected(self):
        return self.__port_handler is not None

    @property
    def fields(self) -> Dict[str, Field]:
        return self.__field_dict
