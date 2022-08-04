# -*- coding: utf-8 -*-
import struct
import numpy as np
import json


class GlTF(object):

    def __init__(self):
        self.header = {}
        self.body = None

    def to_array(self):  # glb
        scene = json.dumps(self.header, separators=(',', ':'))

        # body must be 4-byte aligned
        scene += ' '*((4 - len(scene) % 4) % 4)

        padding = np.array([0 for i in range(0, (4 - len(self.body) % 4) % 4)],
                           dtype=np.uint8)

        length = 28 + len(self.body) + len(scene) + len(padding)
        binaryHeader = np.array([0x46546C67,  # "glTF" magic
                                 2,  # version
                                 length], dtype=np.uint32)
        jsonChunkHeader = np.array([len(scene),  # JSON chunck length
                                    0x4E4F534A], dtype=np.uint32)  # "JSON"

        binChunkHeader = np.array([len(self.body) + len(padding),
                                   # BIN chunck length
                                   0x004E4942], dtype=np.uint32)  # "BIN"

        return np.concatenate((binaryHeader.view(np.uint8),
                               jsonChunkHeader.view(np.uint8),
                               np.frombuffer(scene.encode('utf-8'), dtype=np.uint8),
                               binChunkHeader.view(np.uint8),
                               self.body,
                               padding))

    @staticmethod
    def from_array(array):
        """
        Parameters
        ----------
        array : numpy.array

        Returns
        -------
        glTF : GlTf
        """

        glTF = GlTF()

        if struct.unpack("4s", array[0:4])[0] != b"glTF":
            raise RuntimeError("Array does not contain a binary glTF")

        if struct.unpack("i", array[4:8])[0] != 1:
            raise RuntimeError("Unsupported glTF version")

        length = struct.unpack("i", array[8:12])[0]
        content_length = struct.unpack("i", array[12:16])[0]

        if struct.unpack("i", array[16:20])[0] != 0:
            raise RuntimeError("Unsupported binary glTF content type")

        header = struct.unpack(str(content_length) + "s",
                               array[20:20+content_length])[0]
        glTF.header = json.loads(header.decode("ascii"))
        glTF.body = array[20+content_length:length]

        return glTF

    @staticmethod
    def from_binary_arrays(arrays, transform=None, binary=True, batched=True,
                           uri=None, textureUri=None):
        """
        Parameters
        ----------
        arrays : array of dictionaries
            Each dictionary has the data for one geometry
            arrays['position']: binary array of vertex positions
            arrays['normal']: binary array of vertex normals
            arrays['uv']: binary array of vertex texture coordinates
                          (Not implemented yet)
            arrays['bbox']: geometry bounding box (numpy.array)

        transform : numpy.array
            World coordinates transformation flattend matrix

        Returns
        -------
        glTF : GlTF
        """

        glTF = GlTF()

        textured = 'uv' in arrays[0]
        binVertices = []
        binNormals = []
        binIds = []
        binUvs = []
        nVertices = []
        nNormals = []
        bb = []
        batchLength = 0
        for i, geometry in enumerate(arrays):
            binVertices.append(geometry['position'])
            binNormals.append(geometry['normal'])
            nV = round(len(geometry['position']) / 12) # 3 32-bit values/vertex
            nN = round(len(geometry['normal']) / 12)   # 3 32-bit values/normal
            nVertices.append(nV)
            nNormals.append(nN)
            bb.append(geometry['bbox'])
            if batched:
                binIds.append(np.full(nV, i, dtype=np.float32))
            if textured:
                binUvs.append(geometry['uv'])

        if batched:
            binVertices = [b''.join(binVertices)]
            binNormals = [b''.join(binNormals)]
            binUvs = [b''.join(binUvs)]
            binIds = [b''.join(binIds)]
            nVertices = [sum(nVertices)]
            batchLength = len(arrays)
            [minx, miny, minz] = bb[0][0]
            [maxx, maxy, maxz] = bb[0][1]
            for box in bb[1:]:
                minx = min(minx, box[0][0])
                miny = min(miny, box[0][1])
                minz = min(minz, box[0][2])
                maxx = max(maxx, box[1][0])
                maxy = max(maxy, box[1][1])
                maxz = max(maxz, box[1][2])
            bb = [[[minx, miny, minz], [maxx, maxy, maxz]]]

        glTF.header = compute_header(binVertices, binNormals, nVertices, nNormals, 
                                    bb, textured, batched, batchLength, uri,
                                    textureUri, transform)
        glTF.body = np.frombuffer(compute_binary(binVertices, binNormals,
                                  binIds, binUvs), dtype=np.uint8)

        return glTF


def compute_binary(binVertices, binNormals, binIds, binUvs):
    bv = b''.join(binVertices)
    bn = b''.join(binNormals)
    bid = b''.join(binIds)
    buv = b''.join(binUvs)
    return bv + bn + buv + bid


def compute_header(binVertices, binNormals, nVertices, nNormals, bb,
                   textured, batched, batchLength, uri, textureUri, transform=None):
    # Buffer
    numberOfMeshes = len(binVertices)
    sizeVrtces = []
    sizeNrmls = []
    for i in range(0, numberOfMeshes):
        sizeVrtces.append(len(binVertices[i]))
        sizeNrmls.append(len(binNormals[i]))

    byteLength = sum(sizeVrtces) + sum(sizeNrmls)
    if textured:
        byteLength += int(round(2 * sum(sizeVrtces) / 3))
    if batched:
        byteLength += int(round(sum(sizeVrtces) / 3))
    buffers = [{
        'byteLength': byteLength
    }]
    if uri is not None:
        buffers["binary_glTF"]["uri"] = uri

    # Buffer view
    bufferViews = []
    # vertex positions
    bufferViews.append({
        'buffer': 0,
        'byteLength': sum(sizeVrtces),
        'byteOffset': 0,
        'target': 34962
    })
    # vertex normals
    bufferViews.append({
        'buffer': 0,
        'byteLength': sum(sizeNrmls),
        'byteOffset': sum(sizeVrtces),
        'target': 34962
    })
    if textured:
        bufferViews.append({
            'buffer': 0,
            'byteLength': int(round(2 * sum(sizeVrtces) / 3)),
            'byteOffset': 2 * sum(sizeVrtces),
            'target': 34962
        })
    if batched:
        bufferViews.append({
            'buffer': 0,
            'byteLength': int(round(sum(sizeVrtces) / 3)),
            'byteOffset': int(round(8 / 3 * sum(sizeVrtces))) if textured
            else 2 * sum(sizeVrtces),
            'target': 34962
        })

    # Accessor
    accessors = []
    for i in range(0, numberOfMeshes):
        # vertices
        accessors.append({
            'bufferView': 0,
            'byteOffset': sum(sizeVrtces[0:i]),
            'componentType': 5126,
            'count': nVertices[i],
            # CSJ changed to XYZ not YZX
            'max': [bb[i][0][0], bb[i][0][1], bb[i][0][2]],
            'min': [bb[i][1][0], bb[i][1][1], bb[i][1][2]],
            'type': "VEC3"
        })
        # normals
        accessors.append({
            'bufferView': 1,
            'byteOffset': sum(sizeNrmls[0:i]),
            'componentType': 5126,
            'count': nNormals[i],
            #'max': [1, 1, 1],
            #'min': [-1, -1, -1],
            'type': "VEC3"
        })
        if textured:
            accessors.append({
                'bufferView': 2,
                'byteOffset': int(round(2 / 3 * sum(sizeVrtces[0:i]))),
                'componentType': 5126,
                'count': sum(nVertices),
                'max': [1, 1],
                'min': [0, 0],
                'type': "VEC2"
            })
    if batched:
        accessors.append({
            'bufferView': 3 if textured else 2,
            'byteOffset': 0,
            'componentType': 5126,
            'count': nVertices[0],
            'max': [batchLength],
            'min': [0],
            'type': "SCALAR"
        })

    # Meshes
    meshes = []
    nAttributes = 3 if textured else 2
    for i in range(0, numberOfMeshes):
        meshes.append({
            'primitives': [{
                'attributes': {
                    "POSITION": nAttributes * i,
                    "NORMAL": nAttributes * i + 1
                },
                "material": 0,
                "mode": 4
            }]
        })
        if textured:
            meshes[i]['primitives'][0]['attributes']['TEXCOORD_0'] = (
                nAttributes * i + 2)
    if batched:
        meshes[0]['primitives'][0]['attributes']['_BATCHID'] = nAttributes

    # Nodes
    nodes = []
    for i in range(0, numberOfMeshes):
        if transform is not None:
            nodes.append({
                'matrix': [float(e) for e in transform],
                'mesh': i
            })
        else:
            nodes.append({
                'mesh': i
            })

    # Materials
    materials = [{
        'pbrMetallicRoughness': {
            'metallicFactor': 0
        },
        'name': 'Material',
    }]

    # Final glTF
    header = {
        'asset': {
            "generator": "py3dtiles",
            "version": "2.0"
        },
        'scene': 0,
       # 'extensionsUsed': ['CESIUM_RTC'],
       # 'extensionsRequired': ['CESIUM_RTC'],
       # 'extensions': {
       #     'CESIUM_RTC': {
       #         'center': [
       #             -762889.9791526495,
       #             -1335791.8689435967,
       #             6169085.401505229
       #         ]
       #     }
       # },
        'scenes': [{
            'nodes': [i for i in range(0, len(nodes))]
        }],
        'nodes': nodes,
        'meshes': meshes,
        'materials': materials,
        'accessors': accessors,
        'bufferViews': bufferViews,
        'buffers': buffers
    }

    # Texture data
    if textured:
        header['textures'] = [{
            'sampler': 0,
            'source': 0
        }]
        header['images'] = [{
            'uri': textureUri
        }]
        header['samplers'] = [{
            "magFilter": 9729,
            "minFilter": 9987,
            "wrapS": 10497,
            "wrapT": 10497
        }]
        header['materials'][0]['pbrMetallicRoughness']['baseColorTexture'] = {
            'index': 0
        }

    return header
