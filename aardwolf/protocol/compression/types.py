import enum


class BulkCompressionType(enum.IntEnum):
	RDP4_8K = 0x00
	RDP5_64K = 0x01
	RDP6 = 0x02
	RDP61 = 0x03


class BulkCompressionFlags(enum.IntFlag):
	TYPE_MASK = 0x0F
	COMPRESSED = 0x20
	AT_FRONT = 0x40
	FLUSHED = 0x80


VALID_FLAG_MASK = (
	BulkCompressionFlags.TYPE_MASK
	| BulkCompressionFlags.COMPRESSED
	| BulkCompressionFlags.AT_FRONT
	| BulkCompressionFlags.FLUSHED
)
