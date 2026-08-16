import datetime
import io


_EPOCH_DIFF = 116444736000000000


class FILETIME:
	def __init__(self, dwLowDateTime=0, dwHighDateTime=0):
		self.dwLowDateTime = dwLowDateTime
		self.dwHighDateTime = dwHighDateTime

	@staticmethod
	def from_datetime(dt: datetime.datetime) -> 'FILETIME':
		if dt.tzinfo is not None:
			dt = dt.replace(tzinfo=None)
		stamp = (dt - datetime.datetime(1970, 1, 1)).total_seconds()
		ft = int(stamp * 10000000) + _EPOCH_DIFF
		return FILETIME(ft & 0xFFFFFFFF, (ft >> 32) & 0xFFFFFFFF)

	@staticmethod
	def from_bytes(data: bytes) -> 'FILETIME':
		return FILETIME.from_buffer(io.BytesIO(data))

	@staticmethod
	def from_buffer(buff: io.BytesIO) -> 'FILETIME':
		low = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		high = int.from_bytes(buff.read(4), byteorder='little', signed=False)
		return FILETIME(low, high)

	def to_bytes(self) -> bytes:
		return self.dwLowDateTime.to_bytes(4, 'little', signed=False) + self.dwHighDateTime.to_bytes(4, 'little', signed=False)

	def to_datetime(self) -> datetime.datetime:
		if self.dwHighDateTime == 0xFFFFFFFF and self.dwLowDateTime == 0xFFFFFFFF:
			return datetime.datetime(3000, 1, 1)
		ft = (self.dwHighDateTime << 32) + self.dwLowDateTime
		if ft == 0:
			return datetime.datetime(1970, 1, 1)
		return datetime.datetime.fromtimestamp((ft - _EPOCH_DIFF) / 10000000, datetime.timezone.utc).replace(tzinfo=None)
