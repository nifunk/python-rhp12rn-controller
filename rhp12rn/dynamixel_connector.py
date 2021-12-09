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

import struct
import time
from abc import abstractmethod
from queue import Queue
from typing import Optional, NamedTuple, Dict, Sequence

from dynamixel_sdk import PortHandler, PacketHandler, COMM_SUCCESS, PKT_ID, PKT_ERROR

Field = NamedTuple("Field", (
    ("address", int), ("data_type", str), ("name", str), ("desc", str), ("writable", bool),
    ("initial_value", Optional[int])))


# TODO: properly implement bulk reading


class DynamixelFuture:
    def __init__(self, connector: "DynamixelConnector", packet_handler: PacketHandler, port_handler: PortHandler):
        self._connector = connector
        self._packet_handler = packet_handler
        self._port_handler = port_handler

    @abstractmethod
    def _read(self):
        pass

    @abstractmethod
    def result(self):
        pass


class FieldReadFuture(DynamixelFuture):
    def __init__(self, field: Field, connector: "DynamixelConnector", packet_handler: PacketHandler,
                 port_handler: PortHandler):
        super(FieldReadFuture, self).__init__(connector, packet_handler, port_handler)
        self.__field = field
        self.__data = self.__comm_result = self.__error = None
        self.__read = False

    def _read(self):
        self.__read = True
        self._port_handler.setPacketTimeoutMillis(100)
        data_raw, self.__comm_result, self.__error = self._packet_handler.readRx(
            self._port_handler, self._connector.dynamixel_id, struct.calcsize(self.__field.data_type))
        if self.__comm_result == 0 and self.__error == 0:
            self.__data = struct.unpack("<{}".format(self.__field.data_type), bytes(data_raw))[0]

    def result(self):
        if not self.__read:
            self._connector.process_futures(stop_on=self)
        if self.__comm_result != 0:
            raise ValueError(
                "Encountered communication error during reading (rx): {}".format(
                    self._packet_handler.getTxRxResult(self.__comm_result)))
        elif self.__error != 0:
            raise ValueError(
                "Encountered packet error during reading: {}".format(
                    self._packet_handler.getRxPacketError(self.__error)))
        return self.__data


class FieldWriteFuture(DynamixelFuture):
    def __init__(self, connector: "DynamixelConnector", packet_handler: PacketHandler, port_handler: PortHandler):
        super(FieldWriteFuture, self).__init__(connector, packet_handler, port_handler)
        self.__comm_result = self.__error = None
        self.__read = False

    def _read(self):
        self.__read = True
        self._port_handler.setPacketTimeoutMillis(100)
        while True:
            rxpacket, result = self._packet_handler.rxPacket(self._port_handler)
            if result != COMM_SUCCESS or self._connector.dynamixel_id == rxpacket[PKT_ID]:
                break

        self.__comm_result = result
        if result == COMM_SUCCESS:
            self.__error = rxpacket[PKT_ERROR]
        else:
            self.__error = 0

    def result(self):
        if not self.__read:
            self._connector.process_futures(stop_on=self)
        if self.__comm_result != 0:
            raise ValueError(
                "Encountered communication error during writing: {}".format(
                    self._packet_handler.getTxRxResult(self.__comm_result)))
        elif self.__error != 0:
            raise ValueError(
                "Encountered packet error during writing: {}".format(
                    self._packet_handler.getRxPacketError(self.__error)))


class DynamixelConnector:
    def __init__(self, fields: Sequence[Field], device: str = "/dev/ttyUSB0", baud_rate: int = 57600,
                 dynamixel_id: int = 1):
        self.__baud_rate = baud_rate
        self.__dynamixel_id = dynamixel_id
        self.__device = device
        self.__port_handler: Optional[PortHandler] = None
        self.__packet_handler = PacketHandler(2.0)
        self.__field_dict = {f.name: f for f in fields}
        self.__future_queue = Queue()
        self.__last_tx = 0
        self.__tx_wait_time = 0.001

    def connect(self):
        assert not self.connected, "Already connected."
        self.__port_handler = PortHandler(self.__device)
        try:
            if not self.__port_handler.openPort():
                self.__port_handler = None
                raise ValueError("Failed to open port.")

            if not self.__port_handler.setBaudRate(self.__baud_rate):
                self.disconnect()
                raise ValueError("Failed to set baud rate.")
        except:
            self.__port_handler = None
            raise

    def disconnect(self):
        if self.connected:
            self.__port_handler.closePort()
            self.__port_handler = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def read_field_async(self, field_name: str):
        assert self.connected, "Controller is not connected."
        field = self.__field_dict[field_name]
        # Not waiting between two transmissions causes the controller to not reply
        now = time.time()
        time.sleep(max(0.0, self.__tx_wait_time - (now - self.__last_tx)))
        comm_result = self.__packet_handler.readTx(
            self.__port_handler, self.__dynamixel_id, field.address, struct.calcsize(field.data_type))
        self.__last_tx = time.time()
        self.__port_handler.is_using = False
        if comm_result != 0:
            raise ValueError(
                "Encountered communication error during reading (tx): {}".format(
                    self.__packet_handler.getTxRxResult(comm_result)))
        future = FieldReadFuture(field, self, self.__packet_handler, self.__port_handler)
        self.__future_queue.put(future)
        return future

    def write_field_async(self, field_name: str, value: int):
        assert self.connected, "Controller is not connected."
        field = self.__field_dict[field_name]
        data = list(struct.pack("<{}".format(field.data_type), value))
        # Not waiting between two transmissions causes the controller to not reply
        now = time.time()
        time.sleep(max(0.0, self.__tx_wait_time - (now - self.__last_tx)))
        comm_result = self.__packet_handler.writeTxOnly(
            self.__port_handler, self.__dynamixel_id, field.address, len(data), data)
        self.__last_tx = time.time()
        self.__port_handler.is_using = False
        if comm_result != 0:
            raise ValueError(
                "Encountered communication error during writing: {}".format(
                    self.__packet_handler.getTxRxResult(comm_result)))
        future = FieldWriteFuture(self, self.__packet_handler, self.__port_handler)
        self.__future_queue.put(future)
        return future

    def read_field(self, field_name: str):
        return self.read_field_async(field_name).result()

    def write_field(self, field_name: str, value: int):
        return self.write_field_async(field_name, value).result()

    def process_futures(self, stop_on: Optional[DynamixelFuture] = None):
        while not self.__future_queue.empty():
            future = self.__future_queue.get()
            future._read()
            if future == stop_on:
                break

    @property
    def connected(self):
        return self.__port_handler is not None

    @property
    def fields(self) -> Dict[str, Field]:
        return self.__field_dict

    @property
    def dynamixel_id(self) -> int:
        return self.__dynamixel_id
