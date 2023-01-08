import enum
import io
from aardwolf.extensions.RDPEDYC.protocol import DYNVC_CMD, dynvc_header_to_bytes, dynvc_header_from_buff

# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpedyc/f82105dd-0abd-4126-a61b-41a7909e974f

class DYNVC_SOFT_SYNC_FLAG(enum.IntFlag):
    TCP_FLUSHED = 0x01
    CHANNEL_LIST_PRESENT = 0x02

class DYNVC_SOFT_SYNC_REQUEST:
    def __init__(self):
        self.cbid:int = None
        self.sp:int   = 0
        self.cmd:DYNVC_CMD = DYNVC_CMD.SOFT_SYNC_REQUEST
        self.Pad:int   = 0
        self.Length:int   = None
        self.Flags:DYNVC_SOFT_SYNC_FLAG = None
        self.NumberOfTunnels:int = None
        self.SoftSyncChannelLists:List[DYNVC_SOFT_SYNC_CHANNEL_LIST] = []

    @staticmethod
    def from_bytes(data: bytes):
        return DYNVC_SOFT_SYNC_REQUEST.from_buffer(io.BytesIO(data))

    @staticmethod
    def from_buffer(buff: io.BytesIO):
        msg = DYNVC_SOFT_SYNC_REQUEST()
        msg.cbid, msg.sp, msg.cmd = dynvc_header_from_buff(buff)
        msg.Pad = buff.read(1)[0]
        msg.Length = int.from_bytes(buff.read(4), byteorder='little', signed=False)
        msg.Flags = DYNVC_SOFT_SYNC_FLAG(int.from_bytes(buff.read(2), byteorder='little', signed=False))
        msg.NumberOfTunnels = int.from_bytes(buff.read(2), byteorder='little', signed=False)
        for _ in range(msg.NumberOfTunnels):
            msg.SoftSyncChannelLists.append(DYNVC_SOFT_SYNC_CHANNEL_LIST.from_buffer(buff))
        return msg

    def to_bytes(self):
        t = b''
        t += dynvc_header_to_bytes(self.cbid, self.sp, self.cmd)
        t += self.Pad.to_bytes(1, byteorder='little', signed=False)
        t += self.Length.to_bytes(4, byteorder='little', signed=False)
        t += self.Flags.to_bytes(2, byteorder='little', signed=False)
        t += len(self.SoftSyncChannelLists).to_bytes(2, byteorder='little', signed=False)
        for ch in self.SoftSyncChannelLists:
            t += ch.to_bytes()
        return t

# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpedyc/f82105dd-0abd-4126-a61b-41a7909e974f

from typing import List

class DYNVC_TUNNELTYPE(enum.Enum):
    UDPFECR = 0x00000001 #RDP-UDP Forward Error Correction (FEC) multitransport tunnel ([MS-RDPEMT] section 1.3).
    UDPFECL = 0x00000003 #RDP-UDP FEC lossy multitransport tunnel ([MS-RDPEMT] section 1.3).


class DYNVC_SOFT_SYNC_CHANNEL_LIST:
    def __init__(self):
        self.TunnelType:DYNVC_TUNNELTYPE = None
        self.NumberOfDVCs:int   = None
        self.ListOfDVCIds:List[int] = []

    @staticmethod
    def from_bytes(data: bytes):
        return DYNVC_SOFT_SYNC_CHANNEL_LIST.from_buffer(io.BytesIO(data))

    @staticmethod
    def from_buffer(buff: io.BytesIO):
        msg = DYNVC_SOFT_SYNC_CHANNEL_LIST()
        msg.TunnelType = DYNVC_TUNNELTYPE(int.from_bytes(buff.read(4), byteorder='little', signed=False))
        msg.NumberOfDVCs = int.from_bytes(buff.read(2), byteorder='little', signed=False)
        for _ in range(msg.NumberOfDVCs):
            msg.ListOfDVCIds.append(int.from_bytes(buff.read(4), byteorder='little', signed=False))
        return msg

    def to_bytes(self):
        t = b''
        t += self.TunnelType.value.to_bytes(4, byteorder='little', signed=False)
        t += len(self.ListOfDVCIds).to_bytes(2, byteorder='little', signed=False)
        for channelid in self.ListOfDVCIds:
            t += channelid.to_bytes(4, byteorder='little', signed=False)
        return t

# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-rdpedyc/7d120558-b35d-4b78-81e8-bac2cf081bd7
class DYNVC_SOFT_SYNC_RESPONSE:
    def __init__(self):
        self.cbid:int = None
        self.sp:int   = 0
        self.cmd:DYNVC_CMD = DYNVC_CMD.SOFT_SYNC_RESPONSE
        self.Pad:int  = 0
        self.NumberOfTunnels:int = None
        self.TunnelsToSwitch:List[DYNVC_TUNNELTYPE] = []

    @staticmethod
    def from_bytes(data: bytes):
        return DYNVC_SOFT_SYNC_RESPONSE.from_buffer(io.BytesIO(data))

    @staticmethod
    def from_buffer(buff: io.BytesIO):
        msg = DYNVC_SOFT_SYNC_RESPONSE()
        msg.cbid, msg.sp, msg.cmd = dynvc_header_from_buff(buff)
        msg.Pad = buff.read(1)[0]
        msg.NumberOfTunnels = int.from_bytes(buff.read(2), byteorder='little', signed=False)
        for _ in range(msg.NumberOfTunnels):
            msg.TunnelsToSwitch.append(DYNVC_TUNNELTYPE(int.from_bytes(buff.read(4), byteorder='little', signed=False)))
        return msg

    def to_bytes(self):
        t = b''
        t += dynvc_header_to_bytes(self.cbid, self.sp, self.cmd)
        t += self.Pad.to_bytes(1, byteorder='little', signed=False)
        t += len(self.NumberOfTunnels).to_bytes(2, byteorder='little', signed=False)
        for ch in self.TunnelsToSwitch:
            t += ch.value.to_bytes(4, byteorder='little', signed=False)
        return t