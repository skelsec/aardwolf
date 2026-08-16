use crate::error::{BulkError, BulkResult};
use crate::mppc::MppcDecoder;
use crate::rdp6::Rdp6Decoder;
use crate::rdp61::Rdp61Decoder;
use crate::types::{COMPRESSED, RDP4_8K, RDP5_64K, RDP6, RDP61, TYPE_MASK, VALID_FLAG_MASK};

enum Codec {
    Rdp4(MppcDecoder),
    Rdp5(MppcDecoder),
    Rdp6(Rdp6Decoder),
    Rdp61(Rdp61Decoder),
}

impl Codec {
    fn new(compression_type: u8, max_output_size: Option<usize>) -> BulkResult<Self> {
        match compression_type {
            RDP4_8K => Ok(Self::Rdp4(MppcDecoder::new(RDP4_8K, max_output_size)?)),
            RDP5_64K => Ok(Self::Rdp5(MppcDecoder::new(RDP5_64K, max_output_size)?)),
            RDP6 => Ok(Self::Rdp6(Rdp6Decoder::new(max_output_size)?)),
            RDP61 => Ok(Self::Rdp61(Rdp61Decoder::new(max_output_size)?)),
            _ => Err(BulkError::new(format!(
                "Unsupported RDP bulk-compression type {compression_type}"
            ))),
        }
    }

    fn compression_type(&self) -> u8 {
        match self {
            Self::Rdp4(_) => RDP4_8K,
            Self::Rdp5(_) => RDP5_64K,
            Self::Rdp6(_) => RDP6,
            Self::Rdp61(_) => RDP61,
        }
    }

    fn decompress(
        &mut self,
        data: &[u8],
        flags: u8,
        expected_size: Option<usize>,
    ) -> BulkResult<Vec<u8>> {
        match self {
            Self::Rdp4(decoder) | Self::Rdp5(decoder) => {
                decoder.decompress(data, flags, expected_size)
            }
            Self::Rdp6(decoder) => decoder.decompress(data, flags, expected_size),
            Self::Rdp61(decoder) => decoder.decompress(data, flags, expected_size),
        }
    }

    fn history_offset(&self) -> usize {
        match self {
            Self::Rdp4(decoder) | Self::Rdp5(decoder) => decoder.history_offset(),
            Self::Rdp6(decoder) => decoder.history_offset(),
            Self::Rdp61(decoder) => decoder.history_offset(),
        }
    }

    fn history_size(&self) -> usize {
        match self {
            Self::Rdp4(decoder) | Self::Rdp5(decoder) => decoder.history_size(),
            Self::Rdp6(decoder) => decoder.history_size(),
            Self::Rdp61(decoder) => decoder.history_size(),
        }
    }

    fn offset_cache_len(&self) -> Option<usize> {
        match self {
            Self::Rdp6(decoder) => Some(decoder.offset_cache_len()),
            _ => None,
        }
    }

    fn level2_history_offset(&self) -> Option<usize> {
        match self {
            Self::Rdp61(decoder) => Some(decoder.level2_history_offset()),
            _ => None,
        }
    }
}

pub struct BulkDecompressor {
    max_compression_type: u8,
    max_output_size: Option<usize>,
    codec: Option<Codec>,
    packet_count: usize,
    compressed_packet_count: usize,
    compressed_byte_count: usize,
    decompressed_byte_count: usize,
}

impl BulkDecompressor {
    pub fn new(max_compression_type: u8, max_output_size: Option<usize>) -> BulkResult<Self> {
        if !matches!(max_compression_type, RDP4_8K | RDP5_64K | RDP6 | RDP61) {
            return Err(BulkError::new(format!(
                "{max_compression_type} is not a valid BulkCompressionType"
            )));
        }
        if max_output_size == Some(0) {
            return Err(BulkError::new("Maximum decompressed size must be positive"));
        }

        Ok(Self {
            max_compression_type,
            max_output_size,
            codec: None,
            packet_count: 0,
            compressed_packet_count: 0,
            compressed_byte_count: 0,
            decompressed_byte_count: 0,
        })
    }

    fn select_codec(&mut self, flags: u8) -> BulkResult<&mut Codec> {
        if flags & !VALID_FLAG_MASK != 0 {
            return Err(BulkError::new("Reserved bulk-compression flag is set"));
        }

        let compression_type = flags & TYPE_MASK;
        if !matches!(compression_type, RDP4_8K | RDP5_64K | RDP6 | RDP61) {
            return Err(BulkError::new("Unsupported RDP bulk-compression type"));
        }
        if compression_type > self.max_compression_type {
            return Err(BulkError::new(format!(
                "Server selected bulk-compression type {compression_type} above negotiated {}",
                self.max_compression_type
            )));
        }

        if let Some(codec) = self.codec.as_ref() {
            let selected_type = codec.compression_type();
            if compression_type != selected_type {
                return Err(BulkError::new(format!(
                    "Server changed bulk-compression type from {selected_type} to {compression_type}"
                )));
            }
        } else {
            self.codec = Some(Codec::new(compression_type, self.max_output_size)?);
        }

        Ok(self
            .codec
            .as_mut()
            .expect("a codec was selected or already existed"))
    }

    pub fn decompress(
        &mut self,
        data: &[u8],
        flags: u8,
        expected_size: Option<usize>,
    ) -> BulkResult<Vec<u8>> {
        if flags == 0 {
            if expected_size.is_some_and(|size| data.len() != size) {
                return Err(BulkError::new(
                    "Uncompressed packet length does not match its declaration",
                ));
            }
            self.packet_count += 1;
            return Ok(data.to_vec());
        }

        let output = self
            .select_codec(flags)?
            .decompress(data, flags, expected_size)?;
        self.packet_count += 1;
        if flags & COMPRESSED != 0 {
            self.compressed_packet_count += 1;
            self.compressed_byte_count += data.len();
            self.decompressed_byte_count += output.len();
        }
        Ok(output)
    }

    pub fn max_compression_type(&self) -> u8 {
        self.max_compression_type
    }

    pub fn selected_type(&self) -> Option<u8> {
        self.codec.as_ref().map(Codec::compression_type)
    }

    pub fn packet_count(&self) -> usize {
        self.packet_count
    }

    pub fn compressed_packet_count(&self) -> usize {
        self.compressed_packet_count
    }

    pub fn compressed_byte_count(&self) -> usize {
        self.compressed_byte_count
    }

    pub fn decompressed_byte_count(&self) -> usize {
        self.decompressed_byte_count
    }

    pub fn history_offset(&self) -> Option<usize> {
        self.codec.as_ref().map(Codec::history_offset)
    }

    pub fn history_size(&self) -> Option<usize> {
        self.codec.as_ref().map(Codec::history_size)
    }

    pub fn offset_cache_len(&self) -> Option<usize> {
        self.codec.as_ref().and_then(Codec::offset_cache_len)
    }

    pub fn level2_history_offset(&self) -> Option<usize> {
        self.codec.as_ref().and_then(Codec::level2_history_offset)
    }
}

#[cfg(test)]
mod tests {
    use super::BulkDecompressor;
    use crate::types::{COMPRESSED, FLUSHED, RDP4_8K, RDP5_64K, RDP6, RDP61};

    #[test]
    fn zero_flags_pass_through_without_selecting_a_codec() {
        let mut dispatcher = BulkDecompressor::new(RDP61, None).unwrap();

        assert_eq!(dispatcher.decompress(b"raw", 0, Some(3)).unwrap(), b"raw");
        assert_eq!(dispatcher.selected_type(), None);
        assert_eq!(dispatcher.packet_count(), 1);
        assert_eq!(dispatcher.compressed_packet_count(), 0);
        assert_eq!(dispatcher.history_offset(), None);

        let error = dispatcher.decompress(b"raw", 0, Some(4)).unwrap_err();
        assert_eq!(
            error.to_string(),
            "Uncompressed packet length does not match its declaration"
        );
        assert_eq!(dispatcher.packet_count(), 1);
        assert_eq!(dispatcher.selected_type(), None);
    }

    #[test]
    fn enforces_negotiation_cap_and_one_type_per_connection() {
        let mut capped = BulkDecompressor::new(RDP4_8K, None).unwrap();
        let error = capped
            .decompress(b"", RDP5_64K | COMPRESSED, None)
            .unwrap_err();
        assert_eq!(
            error.to_string(),
            "Server selected bulk-compression type 1 above negotiated 0"
        );
        assert_eq!(capped.selected_type(), None);
        assert_eq!(capped.packet_count(), 0);

        let mut dispatcher = BulkDecompressor::new(RDP61, None).unwrap();
        assert_eq!(dispatcher.decompress(b"", FLUSHED, None).unwrap(), b"");
        let error = dispatcher.decompress(b"raw", RDP5_64K, None).unwrap_err();
        assert_eq!(
            error.to_string(),
            "Server changed bulk-compression type from 0 to 1"
        );
        assert_eq!(dispatcher.selected_type(), Some(RDP4_8K));
        assert_eq!(dispatcher.packet_count(), 1);
    }

    #[test]
    fn dispatches_to_all_four_codecs() {
        for (compression_type, flags, history_size) in [
            (RDP4_8K, FLUSHED, 8_192),
            (RDP5_64K, RDP5_64K, 65_536),
            (RDP6, RDP6, 65_536),
            (RDP61, RDP61, 2_000_000),
        ] {
            let mut dispatcher = BulkDecompressor::new(RDP61, None).unwrap();
            assert_eq!(dispatcher.decompress(b"raw", flags, None).unwrap(), b"raw");
            assert_eq!(dispatcher.selected_type(), Some(compression_type));
            assert_eq!(dispatcher.history_size(), Some(history_size));
        }
    }

    #[test]
    fn tracks_only_successful_compressed_packets() {
        let mut dispatcher = BulkDecompressor::new(RDP61, None).unwrap();

        assert_eq!(
            dispatcher
                .decompress(b"\x06\x00data", RDP61 | COMPRESSED, Some(4))
                .unwrap(),
            b"data"
        );
        assert_eq!(dispatcher.packet_count(), 1);
        assert_eq!(dispatcher.compressed_packet_count(), 1);
        assert_eq!(dispatcher.compressed_byte_count(), 6);
        assert_eq!(dispatcher.decompressed_byte_count(), 4);
        assert_eq!(dispatcher.history_offset(), Some(4));
        assert_eq!(dispatcher.history_size(), Some(2_000_000));
        assert_eq!(dispatcher.offset_cache_len(), None);
        assert_eq!(dispatcher.level2_history_offset(), Some(0));
    }

    #[test]
    fn malformed_packets_do_not_change_history_or_metrics() {
        let mut dispatcher = BulkDecompressor::new(RDP4_8K, None).unwrap();
        assert_eq!(
            dispatcher
                .decompress(b"seed", RDP4_8K | COMPRESSED, Some(4))
                .unwrap(),
            b"seed"
        );

        let history_offset = dispatcher.history_offset();
        let packet_count = dispatcher.packet_count();
        let compressed_packet_count = dispatcher.compressed_packet_count();
        let compressed_byte_count = dispatcher.compressed_byte_count();
        let decompressed_byte_count = dispatcher.decompressed_byte_count();

        assert!(dispatcher
            .decompress(&[0xff], RDP4_8K | COMPRESSED, None)
            .is_err());
        assert_eq!(dispatcher.selected_type(), Some(RDP4_8K));
        assert_eq!(dispatcher.history_offset(), history_offset);
        assert_eq!(dispatcher.packet_count(), packet_count);
        assert_eq!(
            dispatcher.compressed_packet_count(),
            compressed_packet_count
        );
        assert_eq!(dispatcher.compressed_byte_count(), compressed_byte_count);
        assert_eq!(
            dispatcher.decompressed_byte_count(),
            decompressed_byte_count
        );
    }
}
