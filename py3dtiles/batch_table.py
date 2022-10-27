import json

import numpy as np


class BatchTableHeader:

    def __init__(self):
        self.properties = {}

    def add_property_from_array(self, property_name, array):
        self.properties[property_name] = array

    def to_array(self):
        # convert dict to json string
        bt_json = json.dumps(self.properties, separators=(',', ':'))
        # header must be 8-byte aligned (refer to batch table documentation)
        if len(bt_json) % 8 != 0:
            bt_json += ' ' * (8 - len(bt_json) % 8)
        # returns an array of binaries representing the batch table
        return np.frombuffer(bt_json.encode(), dtype=np.uint8)


class BatchTableBody:

    def __init__(self):
        self.properties = {}
        self.header_length = 0

    def sync(self, header):
        self.header_length = len(header.to_array())

    def to_array(self):
        # header must be 4-byte aligned (refer to batch table documentation)
        body = ' '*(4 - self.header_length % 4)
        # Returns a blank space for now for testing
        return np.fromstring(body, dtype=np.uint8)


class BatchTable:
    """
    Only the JSON header has been implemented for now. According to the batch
    table documentation, the binary body is useful for storing long arrays of
    data (better performances)
    """

    def __init__(self):
        self.header = BatchTableHeader()
        self.body = BatchTableBody()

    # returns batch table as binary
    def to_array(self):
        self.body.sync(self.header)
        #return np.fromstring(self.header.to_array(), dtype=np.uint8)
        h_arr = self.header.to_array()
        b_arr = self.body.to_array()
        return np.concatenate((h_arr, b_arr))

    def get_length(self):
        if len(list(self.header.properties.keys())) == 0:
            return 

        # Use the id property as the preferred length, since it should be populated for all features
        if "id" in self.header.properties.keys():
            return len(self.header.properties["id"])
        # Use the first property length
        else:
            return len(self.header.properties[list(self.header.properties.keys())[0]])
