"""RDPDR / MS-RDPEFS PDU and FSCC serializer round-trips."""

import datetime

import pytest

from aardwolf.extensions.RDPEFS.protocol.announce import (
    DR_CORE_CLIENT_NAME,
    DR_CORE_CLIENTID_CONFIRM,
    DR_CORE_SERVER_ANNOUNCE,
)
from aardwolf.extensions.RDPEFS.protocol.capabilities import default_client_capabilities
from aardwolf.extensions.RDPEFS.protocol.device import (
    DEVICE_ANNOUNCE,
    DR_CORE_DEVICE_REPLY,
    DR_CORE_DEVICELIST_ANNOUNCE,
    RDPDR_DTYP_FILESYSTEM,
)
from aardwolf.extensions.RDPEFS.protocol.header import PAKID
from aardwolf.extensions.RDPEFS.protocol.io import (
    DR_CREATE_REQ,
    DR_DEVICE_IOCOMPLETION,
    DR_DEVICE_IOREQUEST,
    DR_QUERY_DIRECTORY_REQ,
    DR_READ_REQ,
    DR_WRITE_REQ,
    IRP_MJ,
)
from aardwolf.extensions.RDPEFS.wintypes.create import CreateDisposition, CreateOptions
from aardwolf.extensions.RDPEFS.wintypes.fileinfo import (
    DirectoryEntry,
    FileBasicInformation,
    FileStandardInformation,
    pack_directory_entries,
)
from aardwolf.extensions.RDPEFS.wintypes.fileinfoclass import FileInfoClass
from aardwolf.extensions.RDPEFS.wintypes.filetime import FILETIME
from aardwolf.extensions.RDPEFS.wintypes.ntstatus import NTStatus


pytestmark = pytest.mark.unit


def test_server_announce_round_trip():
    original = DR_CORE_SERVER_ANNOUNCE(1, 13, 0x11223344)
    parsed = DR_CORE_SERVER_ANNOUNCE.from_bytes(original.to_bytes())
    assert parsed.VersionMajor == 1
    assert parsed.VersionMinor == 13
    assert parsed.ClientId == 0x11223344
    assert parsed.header.PacketId == PAKID.CORE_SERVER_ANNOUNCE


def test_clientid_confirm_and_client_name_round_trip():
    confirm = DR_CORE_CLIENTID_CONFIRM.from_bytes(DR_CORE_CLIENTID_CONFIRM(1, 12, 7).to_bytes())
    assert confirm.ClientId == 7
    name = DR_CORE_CLIENT_NAME.from_bytes(DR_CORE_CLIENT_NAME("BOX").to_bytes())
    assert name.ComputerName == "BOX"


def test_device_list_announce_two_drives():
    listing = DR_CORE_DEVICELIST_ANNOUNCE([
        DEVICE_ANNOUNCE(RDPDR_DTYP_FILESYSTEM, 1, "MEM", "memory"),
        DEVICE_ANNOUNCE(RDPDR_DTYP_FILESYSTEM, 2, "ZIP", "archive"),
    ])
    parsed = DR_CORE_DEVICELIST_ANNOUNCE.from_bytes(listing.to_bytes())
    assert len(parsed.devices) == 2
    assert parsed.devices[0].PreferredDosName == "MEM"
    assert parsed.devices[1].DeviceId == 2
    assert parsed.devices[1].DeviceName == "archive"


def test_device_reply_and_capability_round_trip():
    reply = DR_CORE_DEVICE_REPLY.from_bytes(DR_CORE_DEVICE_REPLY(1, 0).to_bytes())
    assert reply.DeviceId == 1
    caps = default_client_capabilities()
    parsed = type(caps).from_bytes(caps.to_bytes())
    assert len(parsed.capabilities) == 2


def test_io_request_create_read_write_round_trip():
    create = DR_CREATE_REQ()
    create.Disposition = CreateDisposition.FILE_OPEN
    create.CreateOptions = CreateOptions.FILE_NON_DIRECTORY_FILE
    create.Path = "\\probe.txt"
    request = DR_DEVICE_IOREQUEST(1, 0, 9, IRP_MJ.CREATE)
    request.payload = create.to_bytes()
    parsed = DR_DEVICE_IOREQUEST.from_bytes(request.to_bytes())
    body = DR_CREATE_REQ.from_bytes(parsed.payload)
    assert body.Path == "\\probe.txt"
    assert parsed.CompletionId == 9

    read = DR_READ_REQ.from_bytes(DR_READ_REQ(16, 4).to_bytes())
    assert read.Length == 16
    assert read.Offset == 4
    write = DR_WRITE_REQ.from_bytes(DR_WRITE_REQ(2, b"abc").to_bytes())
    assert write.WriteData == b"abc"
    assert write.Offset == 2


def test_io_completion_and_directory_query_round_trip():
    completion = DR_DEVICE_IOCOMPLETION.from_bytes(
        DR_DEVICE_IOCOMPLETION(1, 3, NTStatus.SUCCESS, b"\x01\x00\x00\x00").to_bytes()
    )
    assert completion.DeviceId == 1
    assert completion.IoStatus == NTStatus.SUCCESS
    query = DR_QUERY_DIRECTORY_REQ.from_bytes(
        DR_QUERY_DIRECTORY_REQ(FileInfoClass.FileBothDirectoryInformation, True, "*").to_bytes()
    )
    assert query.Path == "*"
    assert query.InitialQuery == 1


def test_filetime_and_fileinfo_serializers():
    moment = datetime.datetime(2020, 1, 2, 3, 4, 5)
    encoded = FILETIME.from_datetime(moment).to_bytes()
    assert FILETIME.from_bytes(encoded).to_datetime() == moment
    basic = FileBasicInformation(moment, moment, moment, moment)
    assert len(basic.to_bytes()) == 40
    standard = FileStandardInformation(10, 10, 1, False, False)
    assert len(standard.to_bytes()) == 24
    entry = DirectoryEntry("probe.txt", False, size=4)
    packed = pack_directory_entries([entry], FileInfoClass.FileBothDirectoryInformation)
    assert packed.startswith(b"\x00\x00\x00\x00")
    assert "probe.txt".encode("utf-16-le") in packed
