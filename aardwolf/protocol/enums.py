import enum


class UnknownValueEnum(enum.Enum):
	"""Enum for wire-level type fields: integer values without a defined member
	resolve to a cached UNKNOWN_0xNNNN pseudo-member that keeps the raw value,
	instead of raising ValueError. Pseudo-members are not listed by iteration
	or __members__."""

	@classmethod
	def _missing_(cls, value):
		if not isinstance(value, int) or isinstance(value, bool):
			return None
		member = cls._value2member_map_.get(value)
		if member is None:
			member = object.__new__(cls)
			member._name_ = 'UNKNOWN_0x%04X' % value
			member._value_ = value
			member = cls._value2member_map_.setdefault(value, member)
		return member
