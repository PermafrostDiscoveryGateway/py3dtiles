import json
import struct

import numpy as np

from py3dtiles.tileset.batch_table import BatchTable
from py3dtiles.tileset.tile_content import TileContent, TileContentBody, TileContentHeader, TileContentType
from .gltf import GlTF

# 1008 - Lauren - importing FeatureTable
from py3dtiles.tileset.feature_table import FeatureTable


class B3dm(TileContent):

    @staticmethod
    def from_glTF(gltf, bt=None):
        """
        Parameters
        ----------
        gltf : GlTF
            glTF object representing a set of objects

        bt : Batch Table (optional)
            BatchTable object containing per-feature metadata

        Returns
        -------
        tile : TileContent
        """

        tb = B3dmBody()
        tb.glTF = gltf

        if bt==None:
            bt = BatchTable()
        
        print("pdg version")

        tb.batch_table = bt

        th = B3dmHeader()
        th.sync(tb)

        t = TileContent()
        t.body = tb
        t.header = th

        return t

    @staticmethod
    def from_array(array):
        """
        Parameters
        ----------
        array : numpy.array

        Returns
        -------
        t : TileContent
        """

        # build tile header
        h_arr = array[0:B3dmHeader.BYTELENGTH]
        h = B3dmHeader.from_array(h_arr)

        if h.tile_byte_length != len(array):
            raise RuntimeError("Invalid byte length in header")

        # build tile body
        b_arr = array[B3dmHeader.BYTELENGTH:h.tile_byte_length]
        b = B3dmBody.from_array(h, b_arr)

        # build TileContent with header and body
        t = TileContent()
        t.header = h
        t.body = b

        return t


class B3dmHeader(TileContentHeader):
    BYTELENGTH = 28

    def __init__(self):
        self.type = TileContentType.BATCHED_3D_MODEL
        self.magic_value = b"b3dm"
        self.version = 1
        self.tile_byte_length = 0
        self.ft_json_byte_length = 0
        self.ft_bin_byte_length = 0
        self.bt_json_byte_length = 0
        self.bt_bin_byte_length = 0
        self.bt_length = 0  # number of models in the batch

    def to_array(self):
        header_arr = np.frombuffer(self.magic_value, np.uint8)

        header_arr2 = np.array([self.version,
                                self.tile_byte_length,
                                self.ft_json_byte_length,
                                self.ft_bin_byte_length,
                                self.bt_json_byte_length,
                                self.bt_bin_byte_length], dtype=np.uint32)

        return np.concatenate((header_arr, header_arr2.view(np.uint8)))

    def sync(self, body):
        """
        Allow to synchronize headers with contents.
        """

        # extract array
        glTF_arr = body.glTF.to_array()

        # sync the batch table and the feature table
        body.feature_table.header.batch_length = body.batch_table.get_length()

        # sync the tile header with feature table contents
        self.tile_byte_length = B3dmHeader.BYTELENGTH + len(body.feature_table.to_array()) + len(glTF_arr)
        self.bt_json_byte_length = 0
        self.bt_bin_byte_length = 0
        self.ft_json_byte_length = 0
        self.ft_bin_byte_length = 0

        if body.batch_table is not None:
            bt_arr = body.batch_table.to_array()
            self.tile_byte_length += len(bt_arr)

            bth_arr = body.batch_table.header.to_array()
            btb_arr = body.batch_table.body.to_array()
            self.bt_json_byte_length = len(bth_arr)
            self.bt_bin_byte_length = len(btb_arr)

        # Changes by Lauren below
        #Uncommented out these lines that converts FT to array
        fth_arr = body.feature_table.header.to_array()
        ftb_arr = body.feature_table.body.to_array()

        #Set the byte length headers
        self.ft_json_byte_length = len(fth_arr)
        self.ft_bin_byte_length = len(ftb_arr)

    @staticmethod
    def from_array(array):
        """
        Parameters
        ----------
        array : numpy.array

        Returns
        -------
        h : TileContentHeader
        """

        h = B3dmHeader()

        if len(array) != B3dmHeader.BYTELENGTH:
            raise RuntimeError("Invalid header length")

        h.magic_value = b"b3dm"
        h.version = struct.unpack("i", array[4:8])[0]
        h.tile_byte_length = struct.unpack("i", array[8:12])[0]
        h.ft_json_byte_length = struct.unpack("i", array[12:16])[0]
        h.ft_bin_byte_length = struct.unpack("i", array[16:20])[0]
        h.bt_json_byte_length = struct.unpack("i", array[20:24])[0]
        h.bt_bin_byte_length = struct.unpack("i", array[24:28])[0]

        h.type = TileContentType.BATCHED_3D_MODEL

        return h


class B3dmBody(TileContentBody):
    def __init__(self):
        self.batch_table = BatchTable()
        self.glTF = GlTF()

        # 10082021 - Lauren - Uncommenting out this line that creates FeatureTable obj
        self.feature_table = FeatureTable()
        

    def to_array(self):
        # TODO : export feature table
        array = self.glTF.to_array()

        if self.batch_table is not None:
            array = np.concatenate((self.batch_table.to_array(), array))

        # Concatenate the Feature Table
        array = np.concatenate((self.feature_table.to_array(), array))

        return array

    @staticmethod
    def from_glTF(glTF):
        """
        Parameters
        ----------
        th : TileContentHeader

        glTF : GlTF

        Returns
        -------
        b : TileContentBody
        """

        # build tile body
        b = B3dmBody()
        b.glTF = glTF

        return b

    @staticmethod
    def from_array(th, array):
        """
        Parameters
        ----------
        th : TileContentHeader

        array : numpy.array

        Returns
        -------
        b : TileContentBody
        """

        # build feature table
        ft_len = th.ft_json_byte_length + th.ft_bin_byte_length

        # build batch table
        bt_len = th.bt_json_byte_length + th.bt_bin_byte_length

        # build glTF
        glTF_len = (th.tile_byte_length - ft_len - bt_len
                    - B3dmHeader.BYTELENGTH)
        glTF_arr = array[ft_len + bt_len:ft_len + bt_len + glTF_len]
        glTF = GlTF.from_array(glTF_arr)

        # build tile body with batch table
        b = B3dmBody()
        b.glTF = glTF
        if th.bt_json_byte_length > 0:
            b.batch_table.header = json.loads(array[0:th.bt_json_byte_length].tobytes().decode('utf-8'))

        return b
