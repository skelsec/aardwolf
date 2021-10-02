
from aardwolf.extensions.RDPECLIP.protocol import *
from aardwolf.extensions.RDPECLIP.protocol.clipboardcapabilities import CLIPRDR_GENERAL_CAPABILITY, CB_GENERAL_FALGS
from aardwolf.protocol.channelpdu import CHANNEL_PDU_HEADER, CHANNEL_FLAG
from aardwolf.extensions.RDPECLIP.protocol.formatlist import CLIPBRD_FORMAT

temp = bytes.fromhex('0f000000000000000000000000000000000000000000000000000000000000000000000006c00000460069006c0065004e0061006d0065000000000000000000000000000000000007c00000460069006c0065004e0061006d00650057000000000000000000000000000000')
fmtl = CLIPRDR_FORMAT_LIST.from_bytes(temp, longnames = False, encoding='utf-16-le')
print(fmtl)