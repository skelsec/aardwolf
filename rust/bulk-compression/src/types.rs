pub const RDP4_8K: u8 = 0x00;
pub const RDP5_64K: u8 = 0x01;
pub const RDP6: u8 = 0x02;
pub const RDP61: u8 = 0x03;

pub const TYPE_MASK: u8 = 0x0f;
pub const COMPRESSED: u8 = 0x20;
pub const AT_FRONT: u8 = 0x40;
pub const FLUSHED: u8 = 0x80;

pub const VALID_FLAG_MASK: u8 = TYPE_MASK | COMPRESSED | AT_FRONT | FLUSHED;
