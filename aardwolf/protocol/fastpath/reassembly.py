from aardwolf.protocol.fastpath import (
	FASTPATH_FRAGMENT,
	TS_FP_UPDATE,
)


class FastPathProtocolError(Exception):
	pass


class FastPathFragmentReassembler:
	def __init__(self, max_request_size):
		if max_request_size <= 0:
			raise ValueError('Fast-path maximum request size must be positive')
		self.max_request_size = max_request_size
		self.reset()

	def reset(self):
		self._update_code = None
		self._compression = None
		self._compression_flags = 0
		self._data = None

	@property
	def has_pending_update(self):
		return self._data is not None

	def _fail(self, message):
		self.reset()
		raise FastPathProtocolError(message)

	def _check_size(self, size):
		if size > self.max_request_size:
			self._fail(
				'Fast-path update exceeds the negotiated maximum request size '
				'(%d > %d)' % (size, self.max_request_size)
			)

	def _check_continuation(self, update):
		if self._data is None:
			self._fail('Fast-path fragment received without a FIRST fragment')
		if update.updateCode != self._update_code:
			self._fail('Fast-path fragment update type changed during reassembly')
		if update.compression != self._compression:
			self._fail('Fast-path compression mode changed during reassembly')
		if update.compressionFlags != self._compression_flags:
			self._fail('Fast-path compression flags changed during reassembly')

	def feed(self, update):
		if update.fragmentation == FASTPATH_FRAGMENT.SINGLE:
			if self._data is not None:
				self._fail('Unfragmented fast-path update interrupted fragment reassembly')
			self._check_size(len(update.updateData))
			return update

		if update.fragmentation == FASTPATH_FRAGMENT.FIRST:
			if self._data is not None:
				self._fail('Fast-path FIRST fragment interrupted fragment reassembly')
			self._check_size(len(update.updateData))
			self._update_code = update.updateCode
			self._compression = update.compression
			self._compression_flags = update.compressionFlags
			self._data = bytearray(update.updateData)
			return None

		if update.fragmentation not in (
			FASTPATH_FRAGMENT.NEXT,
			FASTPATH_FRAGMENT.LAST,
		):
			self._fail('Invalid fast-path fragmentation value')

		self._check_continuation(update)
		self._check_size(len(self._data) + len(update.updateData))
		self._data.extend(update.updateData)
		if update.fragmentation == FASTPATH_FRAGMENT.NEXT:
			return None

		reassembled = TS_FP_UPDATE()
		reassembled.updateCode = self._update_code
		reassembled.fragmentation = FASTPATH_FRAGMENT.SINGLE
		reassembled.compression = self._compression
		reassembled.compressionFlags = self._compression_flags
		reassembled.updateData = bytes(self._data)
		reassembled.size = len(reassembled.updateData)
		self.reset()
		return reassembled
