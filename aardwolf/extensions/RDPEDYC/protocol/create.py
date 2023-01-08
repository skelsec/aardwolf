import io
from aardwolf.extensions.RDPEDYC.protocol import DYNVC_CMD, dynvc_header_to_bytes, dynvc_header_from_buff

# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpedyc/4448ba4d-9a72-429f-8b65-6f4ec44f2985
class DYNVC_CREATE_REQ:
    def __init__(self):
        self.cbid:int = None
        self.pri:int   = 0
        self.cmd:DYNVC_CMD = DYNVC_CMD.CREATE_RSP
        self.ChannelId:int   = 0
        self.ChannelName:str = None

    @staticmethod
    def from_bytes(data: bytes):
        return DYNVC_CREATE_REQ.from_buffer(io.BytesIO(data))

    @staticmethod
    def from_buffer(buff: io.BytesIO):
        msg = DYNVC_CREATE_REQ()
        msg.cbid, msg.pri, msg.cmd = dynvc_header_from_buff(buff, cbid_mod=True)
        msg.ChannelId = int.from_bytes(buff.read(msg.cbid), byteorder='little', signed=False)
        msg.ChannelName = ''
        for _ in range(255):
            t = buff.read(1)
            if t == b'\x00':
                break
            msg.ChannelName += chr(ord(t))
        return msg

    def to_bytes(self):
        if self.cbid is None:
            self.cbid = 2
        if self.ChannelName[:-1] != '\x00':
            self.ChannelName += '\x00'
        
        t = b''
        t += dynvc_header_to_bytes(self.cbid, self.pri, self.cmd, cbid_mod=True)
        t += self.ChannelId.to_bytes(self.cbid, byteorder='little', signed=False)
        t += self.ChannelName.encode()
        return t
    
    def __str__(self):
        t = ''
        for k in self.__dict__:
            t += '%s: %s\r\n' % (k, self.__dict__[k])
        return t


# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpedyc/8f284ea3-54f3-4c24-8168-8a001c63b581
class DYNVC_CREATE_RSP:
    def __init__(self):
        self.cbid:int = None
        self.sp:int   = 0
        self.cmd:DYNVC_CMD = DYNVC_CMD.CREATE_RSP
        self.ChannelId:int   = 0
        self.CreationStatus:int = None # actually a HRESULT

    @staticmethod
    def from_bytes(data: bytes):
        return DYNVC_CREATE_RSP.from_buffer(io.BytesIO(data))

    @staticmethod
    def from_buffer(buff: io.BytesIO):
        msg = DYNVC_CREATE_RSP()
        msg.cbid, msg.sp, msg.cmd = dynvc_header_from_buff(buff, cbid_mod=True)
        msg.ChannelId = int.from_bytes(buff.read(msg.cbid), byteorder='little', signed=False)
        msg.CreationStatus = int.from_bytes(buff.read(4), byteorder='little', signed=False)
        return msg

    def to_bytes(self):
        if self.cbid is None:
            self.cbid = 1
        
        t = b''
        t += dynvc_header_to_bytes(self.cbid, self.sp, self.cmd, cbid_mod=True)
        t += self.ChannelId.to_bytes(self.cbid, byteorder='little', signed=False)
        t += self.CreationStatus.to_bytes(4, byteorder='little', signed=False)
        return t

    def __str__(self):
        t = ''
        for k in self.__dict__:
            t += '%s: %s\r\n' % (k, self.__dict__[k])
        return t