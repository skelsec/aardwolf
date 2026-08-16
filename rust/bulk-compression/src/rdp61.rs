use crate::error::{BulkError, BulkResult};
use crate::mppc::MppcDecoder;
use crate::types::{AT_FRONT, COMPRESSED, FLUSHED, RDP5_64K, RDP61, TYPE_MASK, VALID_FLAG_MASK};

const HISTORY_SIZE: usize = 2_000_000;
const MAX_BLOCK_SIZE: usize = 16_382;
const MATCH_DETAILS_SIZE: usize = 8;

const L1_COMPRESSED: u8 = 0x01;
const L1_NO_COMPRESSION: u8 = 0x02;
const L1_PACKET_AT_FRONT: u8 = 0x04;
const L1_INNER_COMPRESSION: u8 = 0x10;
const L1_VALID_FLAGS: u8 =
    L1_COMPRESSED | L1_NO_COMPRESSION | L1_PACKET_AT_FRONT | L1_INNER_COMPRESSION;

fn error(message: impl Into<String>) -> BulkError {
    BulkError::new(message)
}

pub struct Rdp61Decoder {
    max_output_size: usize,
    history: Vec<u8>,
    history_offset: usize,
    level2: MppcDecoder,
}

impl Rdp61Decoder {
    pub fn new(max_output_size: Option<usize>) -> BulkResult<Self> {
        let max_output_size = match max_output_size {
            None => MAX_BLOCK_SIZE,
            Some(0) => {
                return Err(error("Maximum decompressed size must be positive"));
            }
            Some(limit) => limit.min(MAX_BLOCK_SIZE),
        };

        Ok(Self {
            max_output_size,
            history: vec![0; HISTORY_SIZE],
            history_offset: 0,
            level2: Self::new_level2()?,
        })
    }

    pub fn history_offset(&self) -> usize {
        self.history_offset
    }

    pub fn history_size(&self) -> usize {
        self.history.len()
    }

    pub fn level2_history_offset(&self) -> usize {
        self.level2.history_offset()
    }

    fn new_level2() -> BulkResult<MppcDecoder> {
        MppcDecoder::new(RDP5_64K, Some(65_535))
    }

    fn validate_outer_flags(flags: u8) -> BulkResult<()> {
        if flags & !VALID_FLAG_MASK != 0 {
            return Err(error("Reserved bulk-compression flag is set"));
        }
        if flags & TYPE_MASK != RDP61 {
            return Err(error(format!(
                "RDP 6.1 decoder received compression type {}",
                flags & TYPE_MASK
            )));
        }
        if flags & AT_FRONT != 0 && flags & COMPRESSED == 0 {
            return Err(error("PACKET_AT_FRONT requires PACKET_COMPRESSED"));
        }
        Ok(())
    }

    fn validate_level1_flags(flags: u8) -> BulkResult<()> {
        if flags & !L1_VALID_FLAGS != 0 {
            return Err(error("Reserved RDP 6.1 level-1 compression flag is set"));
        }
        let mode = flags & (L1_COMPRESSED | L1_NO_COMPRESSION);
        if mode != L1_COMPRESSED && mode != L1_NO_COMPRESSION {
            return Err(error("RDP 6.1 packet must select exactly one level-1 mode"));
        }
        Ok(())
    }

    fn history_value(
        history: &[u8],
        start_offset: usize,
        output: &[u8],
        match_offset: usize,
        match_index: usize,
    ) -> BulkResult<u8> {
        let source = match_offset
            .checked_add(match_index)
            .ok_or_else(|| error("RDP 6.1 match source overflow"))?
            % HISTORY_SIZE;
        let output_end = start_offset
            .checked_add(output.len())
            .ok_or_else(|| error("RDP 6.1 history offset overflow"))?;

        if source >= start_offset && source < output_end {
            let output_index = source
                .checked_sub(start_offset)
                .ok_or_else(|| error("RDP 6.1 match source overflow"))?;
            return output
                .get(output_index)
                .copied()
                .ok_or_else(|| error("RDP 6.1 match source is outside the output buffer"));
        }

        history
            .get(source)
            .copied()
            .ok_or_else(|| error("RDP 6.1 match source is outside the history buffer"))
    }

    fn decode_level1_compressed(
        &self,
        data: &[u8],
        history: &[u8],
        start_offset: usize,
    ) -> BulkResult<Vec<u8>> {
        let match_count_bytes = data
            .get(..2)
            .ok_or_else(|| error("Truncated RDP 6.1 match-count field"))?;
        let match_count = usize::from(u16::from_le_bytes([
            match_count_bytes[0],
            match_count_bytes[1],
        ]));
        if match_count == 0 {
            return Err(error("RDP 6.1 compressed packet contains no matches"));
        }

        let details_size = match_count
            .checked_mul(MATCH_DETAILS_SIZE)
            .ok_or_else(|| error("RDP 6.1 match-details size overflow"))?;
        let details_end = 2usize
            .checked_add(details_size)
            .ok_or_else(|| error("RDP 6.1 match-details size overflow"))?;
        if details_end > data.len() {
            return Err(error("Truncated RDP 6.1 match-details array"));
        }

        let mut details = Vec::with_capacity(match_count);
        let mut detail_offset = 2usize;
        for _ in 0..match_count {
            let detail_end = detail_offset
                .checked_add(MATCH_DETAILS_SIZE)
                .ok_or_else(|| error("RDP 6.1 match-details offset overflow"))?;
            let detail = data
                .get(detail_offset..detail_end)
                .ok_or_else(|| error("Truncated RDP 6.1 match-details array"))?;

            let match_length = usize::from(u16::from_le_bytes([detail[0], detail[1]]));
            let output_offset = usize::from(u16::from_le_bytes([detail[2], detail[3]]));
            let history_offset = usize::try_from(u32::from_le_bytes([
                detail[4], detail[5], detail[6], detail[7],
            ]))
            .map_err(|_| error("RDP 6.1 match source does not fit the platform word size"))?;

            if match_length == 0 || match_length > MAX_BLOCK_SIZE {
                return Err(error("Invalid RDP 6.1 match length"));
            }
            if history_offset >= HISTORY_SIZE {
                return Err(error("RDP 6.1 match source is outside the history buffer"));
            }

            details.push((match_length, output_offset, history_offset));
            detail_offset = detail_end;
        }

        let literals = data
            .get(details_end..)
            .ok_or_else(|| error("RDP 6.1 literal-data offset overflow"))?;
        let mut literals_offset = 0usize;
        let mut output = Vec::new();

        for (match_length, output_offset, history_offset) in details {
            if output_offset < output.len() {
                return Err(error("RDP 6.1 matches are not in stream order"));
            }

            let literal_count = output_offset
                .checked_sub(output.len())
                .ok_or_else(|| error("RDP 6.1 literal count underflow"))?;
            let literals_end = literals_offset
                .checked_add(literal_count)
                .ok_or_else(|| error("RDP 6.1 literal-data offset overflow"))?;
            if literals_end > literals.len() {
                return Err(error("RDP 6.1 match output offset exceeds literal data"));
            }
            let output_after_literals = output
                .len()
                .checked_add(literal_count)
                .ok_or_else(|| error("RDP 6.1 output size overflow"))?;
            if output_after_literals > self.max_output_size {
                return Err(error(
                    "RDP 6.1 output exceeds the configured decompression limit",
                ));
            }
            output.extend_from_slice(&literals[literals_offset..literals_end]);
            literals_offset = literals_end;

            let output_after_match = output
                .len()
                .checked_add(match_length)
                .ok_or_else(|| error("RDP 6.1 output size overflow"))?;
            if output_after_match > self.max_output_size {
                return Err(error(
                    "RDP 6.1 output exceeds the configured decompression limit",
                ));
            }
            for match_index in 0..match_length {
                let value = Self::history_value(
                    history,
                    start_offset,
                    &output,
                    history_offset,
                    match_index,
                )?;
                output.push(value);
            }
        }

        let remaining_literals = literals
            .get(literals_offset..)
            .ok_or_else(|| error("RDP 6.1 literal-data offset overflow"))?;
        let final_output_size = output
            .len()
            .checked_add(remaining_literals.len())
            .ok_or_else(|| error("RDP 6.1 output size overflow"))?;
        if final_output_size > self.max_output_size {
            return Err(error(
                "RDP 6.1 output exceeds the configured decompression limit",
            ));
        }
        output.extend_from_slice(remaining_literals);
        Ok(output)
    }

    fn decode_level1(
        &self,
        data: &[u8],
        flags: u8,
        history: &[u8],
        start_offset: usize,
    ) -> BulkResult<Vec<u8>> {
        if flags & L1_NO_COMPRESSION != 0 {
            if data.len() > self.max_output_size {
                return Err(error(
                    "RDP 6.1 output exceeds the configured decompression limit",
                ));
            }
            return Ok(data.to_vec());
        }

        self.decode_level1_compressed(data, history, start_offset)
    }

    pub fn decompress(
        &mut self,
        data: &[u8],
        flags: u8,
        expected_size: Option<usize>,
    ) -> BulkResult<Vec<u8>> {
        Self::validate_outer_flags(flags)?;
        let outer_flushed = flags & FLUSHED != 0;

        if flags & COMPRESSED == 0 {
            if expected_size.is_some_and(|expected| data.len() != expected) {
                return Err(error(
                    "Uncompressed packet length does not match its declaration",
                ));
            }
            if outer_flushed {
                let working_level2 = Self::new_level2()?;
                self.history = vec![0; HISTORY_SIZE];
                self.history_offset = 0;
                self.level2 = working_level2;
            }
            return Ok(data.to_vec());
        }

        if data.len() < 2 {
            return Err(error("Truncated RDP 6.1 compression header"));
        }
        let level1_flags = data[0];
        let level2_flags = data[1];
        Self::validate_level1_flags(level1_flags)?;

        let mut working_history = if outer_flushed {
            vec![0; HISTORY_SIZE]
        } else {
            self.history.clone()
        };
        let mut start_offset = if outer_flushed {
            0
        } else {
            self.history_offset
        };
        let mut working_level2 = if outer_flushed {
            Self::new_level2()?
        } else {
            self.level2.clone()
        };

        if level1_flags & L1_PACKET_AT_FRONT != 0 {
            working_history.fill(0);
            start_offset = 0;
        } else if flags & AT_FRONT != 0 {
            return Err(error(
                "RDP 6.1 PACKET_AT_FRONT is missing its level-1 equivalent",
            ));
        }

        let mut level1_data = data
            .get(2..)
            .ok_or_else(|| error("Truncated RDP 6.1 compression header"))?
            .to_vec();
        if level1_flags & L1_INNER_COMPRESSION != 0 {
            let level2_type = level2_flags & TYPE_MASK;
            if level2_type != RDP5_64K && (level2_type != 0 || level2_flags & COMPRESSED != 0) {
                return Err(error("RDP 6.1 level-2 compressor is not RDP 5.0"));
            }

            let effective_level2_flags = (level2_flags & !TYPE_MASK) | RDP5_64K;
            level1_data = working_level2.decompress(&level1_data, effective_level2_flags, None)?;
        }

        let output =
            self.decode_level1(&level1_data, level1_flags, &working_history, start_offset)?;
        let history_end = start_offset
            .checked_add(output.len())
            .ok_or_else(|| error("RDP 6.1 history offset overflow"))?;
        if history_end > HISTORY_SIZE {
            return Err(error("RDP 6.1 output overruns the history buffer"));
        }
        if let Some(expected) = expected_size {
            if output.len() != expected {
                return Err(error(format!(
                    "Decompressed packet length does not match its declaration ({} != {})",
                    output.len(),
                    expected
                )));
            }
        }

        working_history[start_offset..history_end].copy_from_slice(&output);
        self.history = working_history;
        self.history_offset = history_end;
        if level1_flags & L1_INNER_COMPRESSION != 0 || outer_flushed {
            self.level2 = working_level2;
        }
        Ok(output)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Default)]
    struct BitWriter {
        bits: Vec<bool>,
    }

    impl BitWriter {
        fn add(&mut self, value: usize, width: usize) {
            for shift in (0..width).rev() {
                self.bits.push((value >> shift) & 1 != 0);
            }
        }

        fn add_text(&mut self, bits: &str) {
            self.bits.extend(bits.bytes().map(|bit| bit == b'1'));
        }

        fn into_bytes(mut self) -> Vec<u8> {
            while !self.bits.len().is_multiple_of(8) {
                self.bits.push(false);
            }
            self.bits
                .chunks(8)
                .map(|chunk| {
                    chunk
                        .iter()
                        .fold(0u8, |byte, &bit| (byte << 1) | u8::from(bit))
                })
                .collect()
        }
    }

    fn add_mppc_literal(writer: &mut BitWriter, value: u8) {
        if value < 0x80 {
            writer.add(usize::from(value), 8);
        } else {
            writer.add_text("10");
            writer.add(usize::from(value & 0x7f), 7);
        }
    }

    fn add_mppc_64k_copy(writer: &mut BitWriter, copy_offset: usize, match_length: usize) {
        if copy_offset < 64 {
            writer.add_text("11111");
            writer.add(copy_offset, 6);
        } else if copy_offset < 320 {
            writer.add_text("11110");
            writer.add(copy_offset - 64, 8);
        } else if copy_offset < 2368 {
            writer.add_text("1110");
            writer.add(copy_offset - 320, 11);
        } else {
            writer.add_text("110");
            writer.add(copy_offset - 2368, 16);
        }

        if match_length == 3 {
            writer.add_text("0");
        } else {
            let extra_bits = usize::BITS as usize - match_length.leading_zeros() as usize - 1;
            for _ in 0..extra_bits - 1 {
                writer.add_text("1");
            }
            writer.add_text("0");
            writer.add(match_length & ((1usize << extra_bits) - 1), extra_bits);
        }
    }

    #[test]
    fn decodes_official_raw_and_match_examples() {
        let mut decoder = Rdp61Decoder::new(None).unwrap();
        let first = b"\x16\x80abcdefghij";
        assert_eq!(
            decoder.decompress(first, RDP61 | COMPRESSED, None).unwrap(),
            b"abcdefghij"
        );

        let second = [
            0x01, 0x00, 0x02, 0x00, 0x09, 0x00, 0x05, 0x00, 0x03, 0x00, 0x00, 0x00, 0x04, 0x00,
            0x0e, 0x00, 0x00, 0x00, 0x00, 0x00, b'k', b'l', b'm', b'n', b'o', b'u',
        ];
        assert_eq!(
            decoder
                .decompress(&second, RDP61 | COMPRESSED, None)
                .unwrap(),
            b"klmnodefghijklabcdu"
        );
        assert_eq!(decoder.history_offset(), 29);
        assert_eq!(decoder.history_size(), HISTORY_SIZE);
    }

    #[test]
    fn chains_level2_mppc_history() {
        let level1_bytes = b"chain me";
        let mut literals = BitWriter::default();
        for value in level1_bytes {
            add_mppc_literal(&mut literals, *value);
        }
        let mut first = vec![
            L1_NO_COMPRESSION | L1_PACKET_AT_FRONT | L1_INNER_COMPRESSION,
            RDP5_64K | COMPRESSED | AT_FRONT | FLUSHED,
        ];
        first.extend_from_slice(&literals.into_bytes());

        let mut decoder = Rdp61Decoder::new(None).unwrap();
        assert_eq!(
            decoder
                .decompress(&first, RDP61 | COMPRESSED, None)
                .unwrap(),
            level1_bytes
        );
        assert_eq!(decoder.level2_history_offset(), level1_bytes.len());

        let mut copy = BitWriter::default();
        add_mppc_64k_copy(&mut copy, level1_bytes.len(), level1_bytes.len());
        let mut second = vec![
            L1_NO_COMPRESSION | L1_INNER_COMPRESSION,
            RDP5_64K | COMPRESSED,
        ];
        second.extend_from_slice(&copy.into_bytes());
        assert_eq!(
            decoder
                .decompress(&second, RDP61 | COMPRESSED, None)
                .unwrap(),
            level1_bytes
        );
        assert_eq!(decoder.level2_history_offset(), level1_bytes.len() * 2);
    }

    #[test]
    fn invalid_match_order_is_transactional() {
        let mut decoder = Rdp61Decoder::new(None).unwrap();
        decoder
            .decompress(b"\x06\x00seed", RDP61 | COMPRESSED, None)
            .unwrap();
        let history_before = decoder.history.clone();
        let history_offset_before = decoder.history_offset();
        let level2_offset_before = decoder.level2_history_offset();

        let packet = [
            0x01, 0x00, 0x02, 0x00, 0x03, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00,
            0x01, 0x00, 0x00, 0x00, 0x00, 0x00, b'a', b'b',
        ];
        let failure = decoder
            .decompress(&packet, RDP61 | COMPRESSED, None)
            .unwrap_err();

        assert!(failure.to_string().contains("stream order"));
        assert_eq!(decoder.history_offset(), history_offset_before);
        assert_eq!(decoder.history, history_before);
        assert_eq!(decoder.level2_history_offset(), level2_offset_before);
    }

    #[test]
    fn match_reads_wrap_across_history_end() {
        let mut decoder = Rdp61Decoder::new(None).unwrap();
        decoder.history[HISTORY_SIZE - 2..].copy_from_slice(b"xy");

        let source = u32::try_from(HISTORY_SIZE - 2).unwrap().to_le_bytes();
        let packet = [
            L1_COMPRESSED,
            0,
            1,
            0,
            4,
            0,
            0,
            0,
            source[0],
            source[1],
            source[2],
            source[3],
        ];
        assert_eq!(
            decoder
                .decompress(&packet, RDP61 | COMPRESSED, None)
                .unwrap(),
            b"xyxy"
        );
    }

    #[test]
    fn level2_and_outer_state_remain_transactional_on_size_failure() {
        let mut writer = BitWriter::default();
        for value in b"unchanged" {
            add_mppc_literal(&mut writer, *value);
        }
        let mut packet = vec![
            L1_NO_COMPRESSION | L1_INNER_COMPRESSION,
            RDP5_64K | COMPRESSED | AT_FRONT,
        ];
        packet.extend_from_slice(&writer.into_bytes());

        let mut decoder = Rdp61Decoder::new(None).unwrap();
        let history_before = decoder.history.clone();
        assert!(decoder
            .decompress(&packet, RDP61 | COMPRESSED, Some(1))
            .is_err());
        assert_eq!(decoder.history, history_before);
        assert_eq!(decoder.history_offset(), 0);
        assert_eq!(decoder.level2_history_offset(), 0);
    }
}
