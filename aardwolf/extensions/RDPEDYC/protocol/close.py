import io
from aardwolf.extensions.RDPEDYC.protocol import DYNVC_CMD, dynvc_header_to_bytes, dynvc_header_from_buff


# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpedyc/c02dfd21-ccbc-4254-985b-3ef6dd115dec
class DYNVC_CLOSE:
    def __init__(self):
        self.cbid:int = 3
        self.sp:int   = 0
        self.cmd:DYNVC_CMD = DYNVC_CMD.CLOSE
        self.ChannelId:int = None

    @staticmethod
    def from_bytes(data: bytes):
        return DYNVC_CLOSE.from_buffer(io.BytesIO(data))

    @staticmethod
    def from_buffer(buff: io.BytesIO):
        msg = DYNVC_CLOSE()
        msg.cbid, msg.sp, msg.cmd = dynvc_header_from_buff(buff, cbid_mod=True)
        msg.ChannelId = int.from_bytes(buff.read(msg.cbid), byteorder='little', signed=False)
        return msg

    def to_bytes(self):
        if self.cbid is None:
            self.cbid = 4
        t = b''
        t += dynvc_header_to_bytes(self.cbid, self.sp, self.cmd, cbid_mod=True)
        t += self.ChannelId.to_bytes(self.cbid, byteorder='little', signed=False)
        return t