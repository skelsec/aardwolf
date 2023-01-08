import io
import enum

# again, this is so messed up. The same commandid can be request or response as well...
class DYNVC_CMD(enum.Enum):
    CREATE_RSP = 0x01 #The message contained in the optionalFields field is a Create Request PDU (section 2.2.2.1) or a Create Response PDU (section 2.2.2.2).
    DATA_FIRST = 0x02 #The message contained in the optionalFields field is a Data First PDU (section 2.2.3.1).
    DATA = 0x03 #The message contained in the optionalFields field is a Data PDU (section 2.2.3.2).
    CLOSE = 0x04 #The message contained in the optionalFields field is a Close Request PDU (section 2.2.4) or a Close Response PDU (section 2.2.4).
    CAPS_RSP = 0x05 #The message contained in the optionalFields field is a Capability Request PDU (section 2.2.1.1) or a Capabilities Response PDU (section 2.2.1.2).
    DATA_FIRST_COMPRESSED = 0x06 #The message contained in the optionalFields field is a Data First Compressed PDU (section 2.2.3.3).
    DATA_COMPRESSED = 0x07 #The message contained in the optionalFields field is a Data Compressed PDU (section 2.2.3.4).
    SOFT_SYNC_REQUEST = 0x08 #The message contained in the optionalFields field is a Soft-Sync Request PDU (section 2.2.5.1).
    SOFT_SYNC_RESPONSE = 0x09 #The message contained in the optionalFields field is a Soft-Sync Response PDU (section 2.2.5.2).


def dynvc_header_from_bytes(data:bytes, cbid_mod = False, sp_mod = False):
    hdr = data[0]
    cmd = DYNVC_CMD(hdr >> 4)
    sp = (hdr >> 2) & 0b11
    cbid = hdr & 0b11
    if cbid_mod is True:
        if cbid == 0: cbid += 1
        else: cbid = cbid * 2
    if sp_mod is True:
        if sp == 0: sp += 1
        else: sp = sp * 2
    return cbid, sp, cmd

def dynvc_header_from_buff(buffer:io.BytesIO, cbid_mod = False, sp_mod = False):
    return dynvc_header_from_bytes(buffer.read(1), cbid_mod=cbid_mod, sp_mod=sp_mod)

def dynvc_header_to_bytes(cbid:int, sp:int, cmd:DYNVC_CMD, cbid_mod = False, sp_mod = False):
    if cbid_mod is True:
        if cbid == 1: cbid = 0
        elif cbid == 2: cbid = 1
        elif cbid == 4: cbid = 2
    if sp_mod is True:
        if sp == 1: sp = 0
        elif sp == 2: sp = 1
        elif sp == 4: sp = 2
    return bytes([(cmd.value << 4) ^ (sp << 2) ^ cbid]) 

from aardwolf.extensions.RDPEDYC.protocol.softsync import DYNVC_SOFT_SYNC_REQUEST, DYNVC_SOFT_SYNC_RESPONSE
from aardwolf.extensions.RDPEDYC.protocol.close import DYNVC_CLOSE
from aardwolf.extensions.RDPEDYC.protocol.data import DYNVC_DATA_FIRST, DYNVC_DATA
from aardwolf.extensions.RDPEDYC.protocol.create import DYNVC_CREATE_REQ, DYNVC_CREATE_RSP
from aardwolf.extensions.RDPEDYC.protocol.caps import DYNVC_CAPS_REQ

class DYNVC_MESSAGE:
    def __init__(self):
        self.cmd:DYNVC_CMD2MSG = None

    @staticmethod
    def from_bytes(data:bytes):
        return DYNVC_MESSAGE.from_buffer(io.BytesIO(data))
    
    @staticmethod
    def from_buffer(buff:io.BytesIO):
        _, _, cmd = dynvc_header_from_bytes(buff.read(1))
        buff.seek(-1, io.SEEK_CUR)
        if DYNVC_CMD2MSG[cmd] is None:
            raise NotImplementedError()
        return DYNVC_CMD2MSG[cmd].from_buffer(buff)
        

DYNVC_CMD2MSG = {
    DYNVC_CMD.CREATE_RSP : DYNVC_CREATE_REQ,
    DYNVC_CMD.DATA_FIRST : DYNVC_DATA_FIRST,
    DYNVC_CMD.DATA : DYNVC_DATA,
    DYNVC_CMD.CLOSE : DYNVC_CLOSE,
    DYNVC_CMD.CAPS_RSP : DYNVC_CAPS_REQ,
    DYNVC_CMD.DATA_FIRST_COMPRESSED : None, #not supported!
    DYNVC_CMD.DATA_COMPRESSED : None, # not supported!
    DYNVC_CMD.SOFT_SYNC_REQUEST : DYNVC_SOFT_SYNC_REQUEST,
    DYNVC_CMD.SOFT_SYNC_RESPONSE : DYNVC_SOFT_SYNC_RESPONSE,
}