use crate::bitstream::{BitReader, HuffmanDecoder};
use crate::error::{BulkError, BulkResult};
use crate::types::{AT_FRONT, COMPRESSED, FLUSHED, RDP6, TYPE_MASK, VALID_FLAG_MASK};

const HISTORY_SIZE: usize = 65_536;
const SLIDE_OFFSET: usize = 32_768;

const HUFF_LENGTH_LEC: &[u8] = &[
    6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 9, 8, 9, 9, 9, 9, 8, 8, 9, 9, 9, 9, 9, 9,
    8, 9, 9, 10, 9, 9, 9, 9, 9, 9, 9, 10, 9, 10, 10, 10, 9, 9, 10, 9, 10, 9, 10, 9, 9, 9, 10, 10,
    9, 10, 9, 9, 8, 9, 9, 9, 9, 10, 10, 10, 9, 9, 10, 10, 10, 10, 10, 10, 9, 9, 10, 10, 10, 10, 10,
    10, 10, 9, 10, 10, 10, 10, 10, 10, 8, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 9, 10, 10, 10, 10, 10, 10, 10, 9, 10, 10, 10, 10, 10, 10, 9, 7, 9, 9, 10, 9, 10, 10, 10, 9,
    10, 10, 10, 10, 10, 10, 10, 9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 13, 10, 10, 10, 10, 10, 10, 11, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 10, 10, 10, 9, 10, 10, 10, 10, 10, 9, 10, 10, 10, 10, 10, 9, 10, 10, 10, 9, 10,
    10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 9, 10, 10, 10, 10, 10, 10, 10, 10, 10,
    10, 10, 10, 10, 9, 10, 8, 9, 9, 10, 9, 10, 10, 10, 9, 10, 10, 10, 9, 9, 8, 7, 13, 13, 7, 7, 10,
    7, 7, 6, 6, 6, 6, 5, 6, 6, 6, 5, 6, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 8, 5, 6, 7, 7,
];

const HUFF_CODE_LEC: &[u16] = &[
    0x4, 0x24, 0x14, 0x11, 0x51, 0x31, 0x71, 0x9, 0x49, 0x29, 0x69, 0x15, 0x95, 0x55, 0xd5, 0x35,
    0xb5, 0x75, 0x1d, 0xf5, 0x11d, 0x9d, 0x19d, 0x5d, 0xd, 0x8d, 0x15d, 0xdd, 0x1dd, 0x3d, 0x13d,
    0xbd, 0x4d, 0x1bd, 0x7d, 0x6b, 0x17d, 0xfd, 0x1fd, 0x3, 0x103, 0x83, 0x183, 0x26b, 0x43, 0x16b,
    0x36b, 0xeb, 0x143, 0xc3, 0x2eb, 0x1c3, 0x1eb, 0x23, 0x3eb, 0x123, 0xa3, 0x1a3, 0x1b, 0x21b,
    0x63, 0x11b, 0x163, 0xe3, 0xcd, 0x1e3, 0x13, 0x113, 0x93, 0x31b, 0x9b, 0x29b, 0x193, 0x53,
    0x19b, 0x39b, 0x5b, 0x25b, 0x15b, 0x35b, 0x153, 0xd3, 0xdb, 0x2db, 0x1db, 0x3db, 0x3b, 0x23b,
    0x13b, 0x1d3, 0x33b, 0xbb, 0x2bb, 0x1bb, 0x3bb, 0x7b, 0x2d, 0x27b, 0x17b, 0x37b, 0xfb, 0x2fb,
    0x1fb, 0x3fb, 0x7, 0x207, 0x107, 0x307, 0x87, 0x287, 0x187, 0x387, 0x33, 0x47, 0x247, 0x147,
    0x347, 0xc7, 0x2c7, 0x1c7, 0x133, 0x3c7, 0x27, 0x227, 0x127, 0x327, 0xa7, 0xb3, 0x19, 0x1b3,
    0x73, 0x2a7, 0x173, 0x1a7, 0x3a7, 0x67, 0xf3, 0x267, 0x167, 0x367, 0xe7, 0x2e7, 0x1e7, 0x3e7,
    0x1f3, 0x17, 0x217, 0x117, 0x317, 0x97, 0x297, 0x197, 0x397, 0x57, 0x257, 0x157, 0x357, 0xd7,
    0x2d7, 0x1d7, 0x3d7, 0x37, 0x237, 0x137, 0x337, 0xb7, 0x2b7, 0x1b7, 0x3b7, 0x77, 0x277, 0x7ff,
    0x177, 0x377, 0xf7, 0x2f7, 0x1f7, 0x3f7, 0x3ff, 0xf, 0x20f, 0x10f, 0x30f, 0x8f, 0x28f, 0x18f,
    0x38f, 0x4f, 0x24f, 0x14f, 0x34f, 0xcf, 0xb, 0x2cf, 0x1cf, 0x3cf, 0x2f, 0x22f, 0x10b, 0x12f,
    0x32f, 0xaf, 0x2af, 0x1af, 0x8b, 0x3af, 0x6f, 0x26f, 0x18b, 0x16f, 0x36f, 0xef, 0x2ef, 0x1ef,
    0x3ef, 0x1f, 0x21f, 0x11f, 0x31f, 0x9f, 0x29f, 0x19f, 0x39f, 0x5f, 0x4b, 0x25f, 0x15f, 0x35f,
    0xdf, 0x2df, 0x1df, 0x3df, 0x3f, 0x23f, 0x13f, 0x33f, 0xbf, 0x2bf, 0x14b, 0x1bf, 0xad, 0xcb,
    0x1cb, 0x3bf, 0x2b, 0x7f, 0x27f, 0x17f, 0x12b, 0x37f, 0xff, 0x2ff, 0xab, 0x1ab, 0x6d, 0x59,
    0x17ff, 0xfff, 0x39, 0x79, 0x1ff, 0x5, 0x45, 0x34, 0xc, 0x2c, 0x1c, 0x0, 0x3c, 0x2, 0x22, 0x10,
    0x12, 0x8, 0x32, 0xa, 0x2a, 0x1a, 0x3a, 0x6, 0x26, 0x16, 0x36, 0xe, 0x2e, 0x1e, 0x3e, 0x1,
    0xed, 0x18, 0x21, 0x25, 0x65,
];

const HUFF_LENGTH_LOM: &[u8] = &[
    4, 2, 3, 4, 3, 4, 4, 5, 4, 5, 5, 6, 6, 7, 7, 8, 7, 8, 8, 9, 9, 8, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9,
];

const HUFF_CODE_LOM: &[u16] = &[
    0x1, 0x0, 0x2, 0x9, 0x6, 0x5, 0xd, 0xb, 0x3, 0x1b, 0x7, 0x17, 0x37, 0xf, 0x4f, 0x6f, 0x2f,
    0xef, 0x1f, 0x5f, 0x15f, 0x9f, 0xdf, 0x1df, 0x3f, 0x13f, 0xbf, 0x1bf, 0x7f, 0x17f, 0xff, 0x1ff,
];

const COPY_OFFSET_BITS: &[u8] = &[
    0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13,
    13, 14, 14,
];

const COPY_OFFSET_BASE: &[usize] = &[
    1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537,
    2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577, 32769, 49153,
];

const MATCH_LENGTH_BITS: &[u8] = &[
    0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 6, 6, 8, 8, 14, 14,
];

const MATCH_LENGTH_BASE: &[usize] = &[
    2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 22, 26, 30, 34, 42, 50, 58, 66, 82, 98, 114, 130,
    194, 258, 514, 2, 2,
];

fn error(message: impl Into<String>) -> BulkError {
    BulkError::new(message)
}

pub struct Rdp6Decoder {
    max_output_size: usize,
    history: Vec<u8>,
    history_offset: usize,
    offset_cache: Vec<usize>,
    lec_decoder: HuffmanDecoder,
    lom_decoder: HuffmanDecoder,
}

impl Rdp6Decoder {
    pub fn new(max_output_size: Option<usize>) -> BulkResult<Self> {
        let codec_limit = HISTORY_SIZE
            .checked_sub(1)
            .ok_or_else(|| error("Invalid RDP 6.0 history size"))?;
        let max_output_size = match max_output_size {
            None => codec_limit,
            Some(0) => {
                return Err(error("Maximum decompressed size must be positive"));
            }
            Some(limit) => limit.min(codec_limit),
        };

        Ok(Self {
            max_output_size,
            history: vec![0; HISTORY_SIZE],
            history_offset: 0,
            offset_cache: Vec::new(),
            lec_decoder: HuffmanDecoder::new(HUFF_CODE_LEC, HUFF_LENGTH_LEC, true)?,
            lom_decoder: HuffmanDecoder::new(HUFF_CODE_LOM, HUFF_LENGTH_LOM, true)?,
        })
    }

    pub fn history_offset(&self) -> usize {
        self.history_offset
    }

    pub fn history_size(&self) -> usize {
        self.history.len()
    }

    pub fn offset_cache_len(&self) -> usize {
        self.offset_cache.len()
    }

    fn validate_flags(flags: u8) -> BulkResult<()> {
        if flags & !VALID_FLAG_MASK != 0 {
            return Err(error("Reserved bulk-compression flag is set"));
        }
        if flags & TYPE_MASK != RDP6 {
            return Err(error(format!(
                "RDP 6.0 decoder received compression type {}",
                flags & TYPE_MASK
            )));
        }
        if flags & AT_FRONT != 0 && flags & COMPRESSED == 0 {
            return Err(error("PACKET_AT_FRONT requires PACKET_COMPRESSED"));
        }
        Ok(())
    }

    fn cache_new_offset(cache: &mut Vec<usize>, copy_offset: usize) {
        if let Some(index) = cache.iter().position(|cached| *cached == copy_offset) {
            cache.remove(index);
        }
        cache.insert(0, copy_offset);
        cache.truncate(4);
    }

    fn cache_offset(cache: &mut [usize], index: usize) -> BulkResult<usize> {
        if index >= cache.len() {
            return Err(error("RDP 6.0 offset-cache reference is not initialized"));
        }
        let copy_offset = cache[index];
        cache.swap(0, index);
        Ok(copy_offset)
    }

    fn append_copy(
        &self,
        output: &mut Vec<u8>,
        history: &[u8],
        start_offset: usize,
        copy_offset: usize,
        match_length: usize,
    ) -> BulkResult<()> {
        if copy_offset == 0 || copy_offset >= HISTORY_SIZE {
            return Err(error("RDP 6.0 copy offset is outside the history window"));
        }
        if match_length < 2 {
            return Err(error("RDP 6.0 match is shorter than two bytes"));
        }

        let final_output_len = output
            .len()
            .checked_add(match_length)
            .ok_or_else(|| error("RDP 6.0 output size overflow"))?;
        if final_output_len > self.max_output_size {
            return Err(error(
                "RDP 6.0 output exceeds the configured decompression limit",
            ));
        }
        let history_end = start_offset
            .checked_add(final_output_len)
            .ok_or_else(|| error("RDP 6.0 history offset overflow"))?;
        if history_end > HISTORY_SIZE {
            return Err(error("RDP 6.0 output overruns the history buffer"));
        }

        for _ in 0..match_length {
            let current_position = start_offset
                .checked_add(output.len())
                .ok_or_else(|| error("RDP 6.0 history offset overflow"))?;
            let source = current_position
                .checked_add(HISTORY_SIZE)
                .and_then(|value| value.checked_sub(copy_offset))
                .ok_or_else(|| error("RDP 6.0 copy source overflow"))?
                % HISTORY_SIZE;
            let current_end = start_offset
                .checked_add(output.len())
                .ok_or_else(|| error("RDP 6.0 history offset overflow"))?;
            let value = if source >= start_offset && source < current_end {
                output[source - start_offset]
            } else {
                history[source]
            };
            output.push(value);
        }
        Ok(())
    }

    fn decode_stream(
        &self,
        data: &[u8],
        history: &[u8],
        start_offset: usize,
        cache: &mut Vec<usize>,
    ) -> BulkResult<Vec<u8>> {
        let mut reader = BitReader::new(data, true);
        let mut output = Vec::new();
        let mut saw_eos = false;

        while reader.remaining_bits() != 0 {
            let symbol = self.lec_decoder.decode(&mut reader)?;
            if symbol < 256 {
                if output.len() >= self.max_output_size {
                    return Err(error(
                        "RDP 6.0 output exceeds the configured decompression limit",
                    ));
                }
                let history_position = start_offset
                    .checked_add(output.len())
                    .ok_or_else(|| error("RDP 6.0 history offset overflow"))?;
                if history_position >= HISTORY_SIZE {
                    return Err(error("RDP 6.0 output overruns the history buffer"));
                }
                output.push(symbol as u8);
                continue;
            }
            if symbol == 256 {
                saw_eos = true;
                break;
            }

            let copy_offset = if (257..=288).contains(&symbol) {
                let index = symbol - 257;
                let extra = reader.read_bits(COPY_OFFSET_BITS[index] as usize)?;
                let copy_offset = COPY_OFFSET_BASE[index]
                    .checked_add(extra)
                    .and_then(|value| value.checked_sub(1))
                    .ok_or_else(|| error("RDP 6.0 copy offset overflow"))?;
                Self::cache_new_offset(cache, copy_offset);
                copy_offset
            } else if (289..=292).contains(&symbol) {
                Self::cache_offset(cache, symbol - 289)?
            } else {
                return Err(error("Invalid RDP 6.0 literal/copy symbol"));
            };

            let length_index = self.lom_decoder.decode(&mut reader)?;
            if length_index >= MATCH_LENGTH_BITS.len() {
                return Err(error("Reserved RDP 6.0 length-of-match symbol"));
            }
            let extra = reader.read_bits(MATCH_LENGTH_BITS[length_index] as usize)?;
            let match_length = MATCH_LENGTH_BASE[length_index]
                .checked_add(extra)
                .ok_or_else(|| error("RDP 6.0 match length overflow"))?;
            self.append_copy(
                &mut output,
                history,
                start_offset,
                copy_offset,
                match_length,
            )?;
        }

        if !saw_eos {
            return Err(error("RDP 6.0 stream has no EOS marker"));
        }
        Ok(output)
    }

    pub fn decompress(
        &mut self,
        data: &[u8],
        flags: u8,
        expected_size: Option<usize>,
    ) -> BulkResult<Vec<u8>> {
        Self::validate_flags(flags)?;

        if flags & COMPRESSED == 0 {
            if let Some(expected) = expected_size {
                if data.len() != expected {
                    return Err(error(
                        "Uncompressed packet length does not match its declaration",
                    ));
                }
            }
            if flags & FLUSHED != 0 {
                self.history.fill(0);
                self.history_offset = 0;
                self.offset_cache.clear();
            }
            return Ok(data.to_vec());
        }

        let mut working_history = if flags & FLUSHED != 0 {
            vec![0; HISTORY_SIZE]
        } else {
            self.history.clone()
        };
        let mut start_offset = if flags & FLUSHED != 0 {
            0
        } else {
            self.history_offset
        };
        let mut working_cache = if flags & FLUSHED != 0 {
            Vec::new()
        } else {
            self.offset_cache.clone()
        };

        if flags & AT_FRONT != 0 {
            let normalized_offset = start_offset % HISTORY_SIZE;
            let recent_start = normalized_offset
                .checked_add(HISTORY_SIZE)
                .and_then(|value| value.checked_sub(SLIDE_OFFSET))
                .ok_or_else(|| error("RDP 6.0 slide-back offset overflow"))?
                % HISTORY_SIZE;
            let mut recent_history = Vec::with_capacity(SLIDE_OFFSET);
            for index in 0..SLIDE_OFFSET {
                let source = recent_start
                    .checked_add(index)
                    .ok_or_else(|| error("RDP 6.0 slide-back offset overflow"))?
                    % HISTORY_SIZE;
                recent_history.push(working_history[source]);
            }
            working_history[..SLIDE_OFFSET].copy_from_slice(&recent_history);
            start_offset = SLIDE_OFFSET;
        }

        let output =
            self.decode_stream(data, &working_history, start_offset, &mut working_cache)?;
        if let Some(expected) = expected_size {
            if output.len() != expected {
                return Err(error(format!(
                    "Decompressed packet length does not match its declaration ({} != {})",
                    output.len(),
                    expected
                )));
            }
        }

        let history_end = start_offset
            .checked_add(output.len())
            .ok_or_else(|| error("RDP 6.0 history offset overflow"))?;
        if history_end > HISTORY_SIZE {
            return Err(error("RDP 6.0 output overruns the history buffer"));
        }
        working_history[start_offset..history_end].copy_from_slice(&output);

        self.history = working_history;
        self.history_offset = history_end;
        self.offset_cache = working_cache;
        Ok(output)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Default)]
    struct BitWriter {
        bits: Vec<u8>,
    }

    impl BitWriter {
        fn add_lsb(&mut self, value: usize, width: usize) {
            for bit in 0..width {
                self.bits.push(((value >> bit) & 1) as u8);
            }
        }

        fn symbol(&mut self, symbol: usize) {
            self.add_lsb(
                HUFF_CODE_LEC[symbol] as usize,
                HUFF_LENGTH_LEC[symbol] as usize,
            );
        }

        fn offset(&mut self, copy_offset: usize) {
            let index = COPY_OFFSET_BASE
                .iter()
                .rposition(|base| *base <= copy_offset + 1)
                .unwrap();
            self.symbol(index + 257);
            self.add_lsb(
                copy_offset + 1 - COPY_OFFSET_BASE[index],
                COPY_OFFSET_BITS[index] as usize,
            );
        }

        fn length(&mut self, length: usize) {
            let index = if length >= 770 {
                28
            } else {
                MATCH_LENGTH_BASE[..28]
                    .iter()
                    .rposition(|base| *base <= length)
                    .unwrap()
            };
            self.add_lsb(
                HUFF_CODE_LOM[index] as usize,
                HUFF_LENGTH_LOM[index] as usize,
            );
            self.add_lsb(
                length - MATCH_LENGTH_BASE[index],
                MATCH_LENGTH_BITS[index] as usize,
            );
        }

        fn finish(mut self) -> Vec<u8> {
            self.symbol(256);
            let byte_len = self.bits.len().div_ceil(8);
            let mut output = vec![0u8; byte_len];
            for (position, bit) in self.bits.into_iter().enumerate() {
                output[position / 8] |= bit << (position % 8);
            }
            output
        }
    }

    #[test]
    fn literals_copy_and_offset_cache() {
        let mut writer = BitWriter::default();
        writer.symbol(b'a' as usize);
        writer.offset(1);
        writer.length(2);
        writer.symbol(289);
        writer.length(2);

        let mut decoder = Rdp6Decoder::new(None).unwrap();
        let mut stream = writer.finish();
        stream.extend_from_slice(&[0xff, 0xff]);
        let output = decoder.decompress(&stream, 0x62, None).unwrap();
        assert_eq!(output, b"aaaaa");
        assert_eq!(decoder.offset_cache, vec![1]);
    }

    #[test]
    fn slide_back_uses_current_wrapped_history_offset() {
        for (history_offset, recent_start) in [(50_000, 17_232), (1_000, 33_768)] {
            let mut decoder = Rdp6Decoder::new(None).unwrap();
            decoder.history[recent_start..recent_start + 4].copy_from_slice(b"abcd");
            decoder.history_offset = history_offset;

            let mut writer = BitWriter::default();
            writer.symbol(b'x' as usize);
            let output = decoder.decompress(&writer.finish(), 0x62, None).unwrap();

            assert_eq!(output, b"x");
            assert_eq!(&decoder.history[..4], b"abcd");
            assert_eq!(decoder.history_offset(), 32_769);
            assert_eq!(decoder.history[32_768], b'x');
        }
    }

    #[test]
    fn wrapped_copy_reads_the_history_tail() {
        let mut decoder = Rdp6Decoder::new(None).unwrap();
        decoder.history[HISTORY_SIZE - 3..].copy_from_slice(b"abc");

        let mut writer = BitWriter::default();
        writer.offset(3);
        writer.length(3);
        let output = decoder.decompress(&writer.finish(), 0x22, None).unwrap();
        assert_eq!(output, b"abc");
    }

    #[test]
    fn offset_cache_is_limited_and_swaps_references() {
        let mut cache = Vec::new();
        for offset in 1..=5 {
            Rdp6Decoder::cache_new_offset(&mut cache, offset);
        }
        assert_eq!(cache, vec![5, 4, 3, 2]);
        assert_eq!(Rdp6Decoder::cache_offset(&mut cache, 2).unwrap(), 3);
        assert_eq!(cache, vec![3, 4, 5, 2]);
        Rdp6Decoder::cache_new_offset(&mut cache, 4);
        assert_eq!(cache, vec![4, 3, 5, 2]);
    }

    #[test]
    fn malformed_stream_and_size_mismatch_are_transactional() {
        let mut decoder = Rdp6Decoder::new(None).unwrap();
        decoder.history[0] = b'q';
        decoder.history_offset = 1;
        let original_history = decoder.history.clone();

        let mut writer = BitWriter::default();
        writer.offset(1);
        writer.length(2);
        assert!(decoder.decompress(&writer.finish(), 0x22, Some(3)).is_err());
        assert_eq!(decoder.history, original_history);
        assert_eq!(decoder.history_offset(), 1);
        assert_eq!(decoder.offset_cache_len(), 0);

        let mut writer = BitWriter::default();
        writer.symbol(292);
        writer.length(2);
        assert!(decoder.decompress(&writer.finish(), 0x62, None).is_err());
        assert_eq!(decoder.history, original_history);
        assert_eq!(decoder.history_offset(), 1);
        assert_eq!(decoder.offset_cache_len(), 0);
    }
}
