from aardwolf.extensions.RDPEFS.wintypes.filetime import FILETIME


FILE_DEVICE_DISK = 0x00000007
FILE_CASE_SENSITIVE_SEARCH = 0x00000001
FILE_CASE_PRESERVED_NAMES = 0x00000002
FILE_UNICODE_ON_DISK = 0x00000004


class FileFsVolumeInformation:
	def __init__(self, label='', serial=0, creation_time=None, supports_objects=False):
		self.label = label
		self.serial = serial
		self.creation_time = creation_time
		self.supports_objects = supports_objects

	def to_bytes(self) -> bytes:
		label = self.label.encode('utf-16-le')
		t = FILETIME.from_datetime(self.creation_time).to_bytes() if self.creation_time else b'\x00' * 8
		t += int(self.serial).to_bytes(4, 'little', signed=False)
		t += len(label).to_bytes(4, 'little', signed=False)
		t += bytes([1 if self.supports_objects else 0, 0])
		t += label
		return t


class FileFsSizeInformation:
	def __init__(self, total_units=0, available_units=0, sectors_per_unit=1, bytes_per_sector=512):
		self.total_units = total_units
		self.available_units = available_units
		self.sectors_per_unit = sectors_per_unit
		self.bytes_per_sector = bytes_per_sector

	def to_bytes(self) -> bytes:
		t = int(self.total_units).to_bytes(8, 'little', signed=True)
		t += int(self.available_units).to_bytes(8, 'little', signed=True)
		t += int(self.sectors_per_unit).to_bytes(4, 'little', signed=False)
		t += int(self.bytes_per_sector).to_bytes(4, 'little', signed=False)
		return t


class FileFsFullSizeInformation:
	def __init__(self, total_units=0, available_units=0, sectors_per_unit=1, bytes_per_sector=512):
		self.total_units = total_units
		self.available_units = available_units
		self.sectors_per_unit = sectors_per_unit
		self.bytes_per_sector = bytes_per_sector

	def to_bytes(self) -> bytes:
		t = int(self.total_units).to_bytes(8, 'little', signed=True)
		t += int(self.available_units).to_bytes(8, 'little', signed=True)
		t += int(self.available_units).to_bytes(8, 'little', signed=True)
		t += int(self.sectors_per_unit).to_bytes(4, 'little', signed=False)
		t += int(self.bytes_per_sector).to_bytes(4, 'little', signed=False)
		return t


class FileFsAttributeInformation:
	def __init__(self, fs_name='FAT32', max_component=255, attributes=FILE_CASE_PRESERVED_NAMES | FILE_UNICODE_ON_DISK):
		self.fs_name = fs_name
		self.max_component = max_component
		self.attributes = attributes

	def to_bytes(self) -> bytes:
		name = self.fs_name.encode('utf-16-le')
		t = int(self.attributes).to_bytes(4, 'little', signed=False)
		t += int(self.max_component).to_bytes(4, 'little', signed=False)
		t += len(name).to_bytes(4, 'little', signed=False)
		t += name
		return t


class FileFsDeviceInformation:
	def __init__(self, device_type=FILE_DEVICE_DISK, characteristics=0):
		self.device_type = device_type
		self.characteristics = characteristics

	def to_bytes(self) -> bytes:
		return int(self.device_type).to_bytes(4, 'little', signed=False) + int(self.characteristics).to_bytes(4, 'little', signed=False)
