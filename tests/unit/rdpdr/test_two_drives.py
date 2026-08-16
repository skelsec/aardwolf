"""Two-drive RDPDR multiplexer: Memory MEM and Zip ZIP must not cross-talk."""

import io
import zipfile

import pytest

from aardwolf.commons.iosettings import RDPIOSettings
from aardwolf.extensions.RDPEFS.channel import RDPDRChannel
from aardwolf.extensions.RDPEFS.protocol.announce import DR_CORE_SERVER_ANNOUNCE
from aardwolf.extensions.RDPEFS.protocol.capabilities import DR_CORE_CAPABILITY
from aardwolf.extensions.RDPEFS.protocol.device import DR_CORE_DEVICELIST_ANNOUNCE, RDPDR_DTYP_FILESYSTEM
from aardwolf.extensions.RDPEFS.protocol.header import PAKID, RDPDR_HEADER
from aardwolf.extensions.RDPEFS.protocol.io import (
    DR_CREATE_REQ,
    DR_DEVICE_IOCOMPLETION,
    DR_DEVICE_IOREQUEST,
    DR_QUERY_DIRECTORY_REQ,
    DR_READ_REQ,
    DR_WRITE_REQ,
    IRP_MJ,
    IRP_MN,
)
from aardwolf.extensions.RDPEFS.providers.memory import MemoryDriveProvider
from aardwolf.extensions.RDPEFS.providers.zip import ZipDriveProvider
from aardwolf.extensions.RDPEFS.wintypes.create import CreateDisposition, CreateOptions
from aardwolf.extensions.RDPEFS.wintypes.fileinfoclass import FileInfoClass
from aardwolf.extensions.RDPEFS.wintypes.ntstatus import NTStatus
from aardwolf.protocol.channelpdu import CHANNEL_FLAG, CHANNEL_PDU_HEADER


pytestmark = pytest.mark.unit


class CapturingConnection:
    def __init__(self):
        self.sent = []
        self.cryptolayer = None

    async def handle_out_data(self, dataobj, sec_hdr, datacontrol_hdr, sharecontrol_hdr, channel_id, is_fastpath):
        self.sent.append(dataobj)


def _wrap(message: bytes) -> bytes:
    flags = CHANNEL_FLAG.CHANNEL_FLAG_FIRST | CHANNEL_FLAG.CHANNEL_FLAG_LAST | CHANNEL_FLAG.CHANNEL_FLAG_SHOW_PROTOCOL
    return CHANNEL_PDU_HEADER.serialize_packet(flags, message, length=len(message)).to_bytes()


def _payloads(connection: CapturingConnection):
    messages = []
    for packet in connection.sent:
        raw = packet.to_bytes() if hasattr(packet, "to_bytes") else packet
        header = CHANNEL_PDU_HEADER.from_bytes(raw)
        messages.append(header.data)
    return messages


def _by_packet(connection: CapturingConnection, packet_id: PAKID):
    found = []
    for message in _payloads(connection):
        header = RDPDR_HEADER.from_bytes(message)
        if header.PacketId == packet_id:
            found.append(message)
    return found


def _make_zip():
    blob = io.BytesIO()
    with zipfile.ZipFile(blob, "w") as archive:
        archive.writestr("probe.txt", "from-zip")
        archive.writestr("only-zip.txt", "zip-only")
    blob.seek(0)
    return blob


async def _handshake(channel: RDPDRChannel):
    await channel.process_channel_data(_wrap(DR_CORE_SERVER_ANNOUNCE(1, 13, 42).to_bytes()))
    await channel.process_channel_data(_wrap(DR_CORE_CAPABILITY(client=False).to_bytes()))


def _create_req(path: str, options=CreateOptions.FILE_NON_DIRECTORY_FILE):
    body = DR_CREATE_REQ()
    body.Disposition = CreateDisposition.FILE_OPEN
    body.CreateOptions = options
    body.Path = path
    return body.to_bytes()


async def _io(channel, device_id, completion_id, major, payload, file_id=0, minor=0):
    request = DR_DEVICE_IOREQUEST(device_id, file_id, completion_id, major, minor)
    request.payload = payload
    await channel.process_channel_data(_wrap(request.to_bytes()))
    message = _by_packet(channel.connection, PAKID.CORE_DEVICE_IOCOMPLETION)[-1]
    return DR_DEVICE_IOCOMPLETION.from_bytes(message)


async def _two_drive_channel():
    settings = RDPIOSettings()
    settings.drives = [
        MemoryDriveProvider("MEM", {"probe.txt": b"from-memory", "only-mem.txt": b"mem-only"}),
        ZipDriveProvider("ZIP", _make_zip()),
    ]
    channel = RDPDRChannel(settings)
    channel.connection = CapturingConnection()
    await channel.start()
    await _handshake(channel)
    return channel


def test_duplicate_dos_names_are_rejected():
    settings = RDPIOSettings()
    settings.drives = [
        MemoryDriveProvider("MEM", {"a.txt": b"a"}),
        MemoryDriveProvider("MEM", {"b.txt": b"b"}),
    ]
    with pytest.raises(ValueError, match="unique"):
        RDPDRChannel(settings)


@pytest.mark.asyncio
async def test_announce_lists_two_distinct_filesystem_devices():
    two_drive_channel = await _two_drive_channel()
    announced = DR_CORE_DEVICELIST_ANNOUNCE.from_bytes(
        _by_packet(two_drive_channel.connection, PAKID.CORE_DEVICELIST_ANNOUNCE)[0]
    )
    assert len(announced.devices) == 2
    names = {device.PreferredDosName for device in announced.devices}
    ids = {device.DeviceId for device in announced.devices}
    types = {device.DeviceType for device in announced.devices}
    assert names == {"MEM", "ZIP"}
    assert len(ids) == 2
    assert types == {RDPDR_DTYP_FILESYSTEM}


@pytest.mark.asyncio
async def test_same_path_reads_do_not_cross_devices():
    two_drive_channel = await _two_drive_channel()
    mem_id = 1
    zip_id = 2
    mem_create = await _io(two_drive_channel, mem_id, 1, IRP_MJ.CREATE, _create_req("\\probe.txt"))
    zip_create = await _io(two_drive_channel, zip_id, 2, IRP_MJ.CREATE, _create_req("\\probe.txt"))
    assert mem_create.IoStatus == NTStatus.SUCCESS
    assert zip_create.IoStatus == NTStatus.SUCCESS
    mem_file = int.from_bytes(mem_create.payload[:4], "little")
    zip_file = int.from_bytes(zip_create.payload[:4], "little")
    assert mem_file != zip_file

    mem_read = await _io(two_drive_channel, mem_id, 3, IRP_MJ.READ, DR_READ_REQ(32, 0).to_bytes(), file_id=mem_file)
    zip_read = await _io(two_drive_channel, zip_id, 4, IRP_MJ.READ, DR_READ_REQ(32, 0).to_bytes(), file_id=zip_file)
    assert mem_read.payload[4:] == b"from-memory"
    assert zip_read.payload[4:] == b"from-zip"


@pytest.mark.asyncio
async def test_write_persists_on_memory_and_fails_on_zip():
    two_drive_channel = await _two_drive_channel()
    mem_create = await _io(two_drive_channel, 1, 10, IRP_MJ.CREATE, _create_req("\\probe.txt"))
    zip_create = await _io(two_drive_channel, 2, 11, IRP_MJ.CREATE, _create_req("\\probe.txt"))
    mem_file = int.from_bytes(mem_create.payload[:4], "little")
    zip_file = int.from_bytes(zip_create.payload[:4], "little")

    mem_write = await _io(two_drive_channel, 1, 12, IRP_MJ.WRITE, DR_WRITE_REQ(0, b"patched").to_bytes(), file_id=mem_file)
    zip_write = await _io(two_drive_channel, 2, 13, IRP_MJ.WRITE, DR_WRITE_REQ(0, b"patched").to_bytes(), file_id=zip_file)
    assert mem_write.IoStatus == NTStatus.SUCCESS
    assert zip_write.IoStatus == NTStatus.MEDIA_WRITE_PROTECTED

    mem_read = await _io(two_drive_channel, 1, 14, IRP_MJ.READ, DR_READ_REQ(7, 0).to_bytes(), file_id=mem_file)
    assert mem_read.payload[4:] == b"patched"


@pytest.mark.asyncio
async def test_root_listings_are_isolated():
    two_drive_channel = await _two_drive_channel()
    mem_root = await _io(
        two_drive_channel,
        1,
        20,
        IRP_MJ.CREATE,
        _create_req("\\", CreateOptions.FILE_DIRECTORY_FILE),
    )
    zip_root = await _io(
        two_drive_channel,
        2,
        21,
        IRP_MJ.CREATE,
        _create_req("\\", CreateOptions.FILE_DIRECTORY_FILE),
    )
    mem_file = int.from_bytes(mem_root.payload[:4], "little")
    zip_file = int.from_bytes(zip_root.payload[:4], "little")
    query = DR_QUERY_DIRECTORY_REQ(FileInfoClass.FileBothDirectoryInformation, True, "*").to_bytes()
    mem_list = await _io(
        two_drive_channel, 1, 22, IRP_MJ.DIRECTORY_CONTROL, query, file_id=mem_file, minor=IRP_MN.QUERY_DIRECTORY
    )
    zip_list = await _io(
        two_drive_channel, 2, 23, IRP_MJ.DIRECTORY_CONTROL, query, file_id=zip_file, minor=IRP_MN.QUERY_DIRECTORY
    )
    mem_names = mem_list.payload.decode("utf-16-le", errors="ignore")
    zip_names = zip_list.payload.decode("utf-16-le", errors="ignore")
    assert "only-mem.txt" in mem_names
    assert "only-zip.txt" not in mem_names
    assert "only-zip.txt" in zip_names
    assert "only-mem.txt" not in zip_names
