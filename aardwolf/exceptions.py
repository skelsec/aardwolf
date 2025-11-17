"""
Custom exceptions for RDP connection abort testing framework
"""

class RDPAbortException(Exception):
	"""
	Exception raised when an RDP connection is intentionally aborted at a specific protocol stage.

	This is used for surgical disconnect testing to identify protocol state-based failures.
	"""
	def __init__(self, stage: str, message: str = None):
		self.stage = stage
		if message is None:
			message = f"RDP connection aborted at stage: {stage}"
		super().__init__(message)

	def __str__(self):
		return f"RDPAbortException(stage={self.stage})"

	def __repr__(self):
		return self.__str__()
