from abc import ABC, abstractmethod
from enum import Enum

import numpy as np

import pathlib

class TileContent:
    def __init__(self):
        self.header = None
        self.body = None

    def to_array(self):
        self.sync()
        header_arr = self.header.to_array()
        body_arr = self.body.to_array()
        return np.concatenate((header_arr, body_arr))

    def to_hex_str(self):
        arr = self.to_array()
        return " ".join("{:02X}".format(x) for x in arr)

    def save_as(self, filename):
        tile_arr = self.to_array()

        # create filepath if doesn't exist
        filepath = pathlib.Path(filename)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.touch(exist_ok=True)

        with open(filename, 'bw') as f:
            f.write(bytes(tile_arr))

    def sync(self):
        """
        Allow to synchronize headers with contents.
        """
        self.header.sync(self.body)


class TileContentType(Enum):
    UNKNOWN = 0
    POINT_CLOUD = 1
    BATCHED_3D_MODEL = 2


class TileContentHeader(ABC):
    @abstractmethod
    def from_array(self, array):
        pass

    @abstractmethod
    def to_array(self):
        pass

    @abstractmethod
    def sync(self, body):
        pass


class TileContentBody:
    @abstractmethod
    def to_array(self):
        pass
