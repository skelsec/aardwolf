import io
from aardwolf.extensions.RDPEDYC.protocol import DYNVC_CMD, dynvc_header_to_bytes, dynvc_header_from_buff

class DYNVC_CAPS_REQ:
    def __init__(self):
        self.cbid:int = 0
        self.sp:int   = 0
        self.cmd:DYNVC_CMD = DYNVC_CMD.CAPS_RSP
        self.pad:int     = 0
        self.version:int = 1
        self.PriorityCharge0:int = None
        self.PriorityCharge1:int = None
        self.PriorityCharge2:int = None
        self.PriorityCharge3:int = None

    @staticmethod
    def from_bytes(data: bytes):
        return DYNVC_CAPS_REQ.from_buffer(io.BytesIO(data))

    @staticmethod
    def from_buffer(buff: io.BytesIO):
        msg = DYNVC_CAPS_REQ()
        msg.cbid, msg.sp, msg.cmd = dynvc_header_from_buff(buff)
        msg.pad = buff.read(1)[0]
        msg.version = int.from_bytes(buff.read(2), byteorder='little', signed=False)
        if msg.version > 1:
            msg.PriorityCharge0 = int.from_bytes(buff.read(2), byteorder='little', signed=False)
            msg.PriorityCharge1 = int.from_bytes(buff.read(2), byteorder='little', signed=False)
            msg.PriorityCharge2 = int.from_bytes(buff.read(2), byteorder='little', signed=False)
            msg.PriorityCharge3 = int.from_bytes(buff.read(2), byteorder='little', signed=False)
        return msg

    def to_bytes(self):
        t = b''
        t += dynvc_header_to_bytes(self.cbid, self.sp, self.cmd)
        t += bytes([self.pad])
        t += self.version.to_bytes(2, byteorder='little', signed=False)
        if self.version > 1:
            t += self.PriorityCharge0.to_bytes(2, byteorder='little', signed=False)
            t += self.PriorityCharge1.to_bytes(2, byteorder='little', signed=False)
            t += self.PriorityCharge2.to_bytes(2, byteorder='little', signed=False)
            t += self.PriorityCharge3.to_bytes(2, byteorder='little', signed=False)
        return t
    
    def __str__(self):
        t = ''
        for k in self.__dict__:
            t += '%s: %s\r\n' % (k, self.__dict__[k])
        return t


class DYNVC_CAPS_RSP:
    def __init__(self):
        self.cbid:int = 0
        self.sp:int   = 0
        self.cmd:DYNVC_CMD = DYNVC_CMD.CAPS_RSP
        self.pad:int     = 0
        self.version:int = 1

    @staticmethod
    def from_bytes(data: bytes):
        return DYNVC_CAPS_RSP.from_buffer(io.BytesIO(data))

    @staticmethod
    def from_buffer(buff: io.BytesIO):
        msg = DYNVC_CAPS_RSP()
        msg.cbid, msg.sp, msg.cmd = dynvc_header_from_buff(buff)
        msg.pad = buff.read(1)[0]
        msg.version = int.from_bytes(buff.read(2), byteorder='little', signed=False)
        return msg

    def to_bytes(self):
        t = b''
        t += dynvc_header_to_bytes(self.cbid, self.sp, self.cmd)
        t += bytes([self.pad])
        t += self.version.to_bytes(2, byteorder='little', signed=False)
        return t
    
    def __str__(self):
        t = ''
        for k in self.__dict__:
            t += '%s: %s\r\n' % (k, self.__dict__[k])
        return t