import enum


class FileInfoClass(enum.IntEnum):
	NONE = 0
	FileDirectoryInformation = 1
	FileFullDirectoryInformation = 2
	FileBothDirectoryInformation = 3
	FileBasicInformation = 4
	FileStandardInformation = 5
	FileInternalInformation = 6
	FileEaInformation = 7
	FileAccessInformation = 8
	FileNameInformation = 9
	FileRenameInformation = 10
	FileLinkInformation = 11
	FileNamesInformation = 12
	FileDispositionInformation = 13
	FilePositionInformation = 14
	FileFullEaInformation = 15
	FileModeInformation = 16
	FileAlignmentInformation = 17
	FileAllInformation = 18
	FileAllocationInformation = 19
	FileEndOfFileInformation = 20
	FileAlternateNameInformation = 21
	FileStreamInformation = 22
	FileNetworkOpenInformation = 34
	FileAttributeTagInformation = 35
	FileIdBothDirectoryInformation = 37
	FileIdFullDirectoryInformation = 38


class FsInformationClass(enum.IntEnum):
	FileFsVolumeInformation = 1
	FileFsLabelInformation = 2
	FileFsSizeInformation = 3
	FileFsDeviceInformation = 4
	FileFsAttributeInformation = 5
	FileFsControlInformation = 6
	FileFsFullSizeInformation = 7
	FileFsObjectIdInformation = 8
