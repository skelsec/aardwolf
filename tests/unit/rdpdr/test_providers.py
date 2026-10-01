"""Memory, zip, and jailed filesystem drive providers."""

import io
import zipfile
from pathlib import Path

import pytest

from aardwolf.extensions.RDPEFS.provider import DriveError, split_rdp_path
from aardwolf.extensions.RDPEFS.providers.filesystem import FilesystemDriveProvider
from aardwolf.extensions.RDPEFS.providers.memory import MemoryDriveProvider
from aardwolf.extensions.RDPEFS.providers.zip import ZipDriveProvider
from aardwolf.extensions.RDPEFS.wintypes.create import CreateDisposition, CreateOptions
from aardwolf.extensions.RDPEFS.wintypes.ntstatus import NTStatus


pytestmark = pytest.mark.unit


async def _open(provider, path, disposition=CreateDisposition.FILE_OPEN, options=CreateOptions.FILE_NON_DIRECTORY_FILE):
    return await provider.create(path, 0, disposition, options)


@pytest.mark.asyncio
async def test_memory_read_write_and_list():
    drive = MemoryDriveProvider("MEM", {"probe.txt": b"from-memory", "sub/a.bin": b"\x00\x01"})
    handle = await _open(drive, "\\probe.txt")
    assert await drive.read(handle, 0, 32) == b"from-memory"
    await drive.write(handle, 0, b"rewritten")
    assert await drive.read(handle, 0, 9) == b"rewritten"
    root = await drive.create("\\", 0, CreateDisposition.FILE_OPEN, CreateOptions.FILE_DIRECTORY_FILE)
    names = [entry.name for entry in (await drive.query_directory(root, "*")).next()]
    assert "probe.txt" in names
    assert "sub" in names


@pytest.mark.asyncio
async def test_zip_read_and_write_protected():
    blob = io.BytesIO()
    with zipfile.ZipFile(blob, "w") as archive:
        archive.writestr("probe.txt", "from-zip")
        archive.writestr("nested/item.bin", b"zz")
    blob.seek(0)
    drive = ZipDriveProvider("ZIP", blob)
    handle = await _open(drive, "\\probe.txt")
    assert await drive.read(handle, 0, 32) == b"from-zip"
    with pytest.raises(DriveError) as exc:
        await drive.write(handle, 0, b"nope")
    assert exc.value.status == NTStatus.MEDIA_WRITE_PROTECTED
    root = await drive.create("\\", 0, CreateDisposition.FILE_OPEN, CreateOptions.FILE_DIRECTORY_FILE)
    names = [entry.name for entry in (await drive.query_directory(root, "*")).next()]
    assert names == ["nested", "probe.txt"]


@pytest.mark.asyncio
async def test_filesystem_jail_rejects_dotdot_and_outbound_symlink(tmp_path: Path):
    root = tmp_path / "share"
    outside = tmp_path / "secret.txt"
    root.mkdir()
    (root / "inside.txt").write_bytes(b"ok")
    outside.write_bytes(b"secret")
    (root / "escape").symlink_to(outside)

    drive = FilesystemDriveProvider("HOME", root)
    with pytest.raises(DriveError) as exc:
        split_rdp_path("\\..\\secret.txt")
    assert exc.value.status == NTStatus.OBJECT_NAME_INVALID

    with pytest.raises(DriveError) as denied:
        await _open(drive, "\\escape")
    assert denied.value.status == NTStatus.ACCESS_DENIED

    handle = await _open(drive, "\\inside.txt")
    assert await drive.read(handle, 0, 8) == b"ok"
    root_handle = await drive.create("\\", 0, CreateDisposition.FILE_OPEN, CreateOptions.FILE_DIRECTORY_FILE)
    names = [entry.name for entry in (await drive.query_directory(root_handle, "*")).next()]
    assert names == ["inside.txt"]
