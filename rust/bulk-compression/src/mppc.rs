use crate::bitstream::BitReader;
use crate::error::{BulkError, BulkResult};
use crate::types::{AT_FRONT, COMPRESSED, FLUSHED, RDP4_8K, RDP5_64K, TYPE_MASK, VALID_FLAG_MASK};

#[derive(Clone)]
pub struct MppcDecoder {
    compression_type: u8,
    max_output_size: usize,
    history: Vec<u8>,
    history_offset: usize,
}

impl MppcDecoder {
    pub fn new(compression_type: u8, max_output_size: Option<usize>) -> BulkResult<Self> {
        let history_size = match compression_type {
            RDP4_8K => 8192,
            RDP5_64K => 65536,
            _ => {
                return Err(BulkError::new(
                    "MPPC supports only the RDP 4.0 and RDP 5.0 types",
                ));
            }
        };

        let codec_limit = history_size - 1;
        let max_output_size = match max_output_size {
            None => codec_limit,
            Some(0) => {
                return Err(BulkError::new("Maximum decompressed size must be positive"));
            }
            Some(limit) => limit.min(codec_limit),
        };

        Ok(Self {
            compression_type,
            max_output_size,
            history: vec![0; history_size],
            history_offset: 0,
        })
    }

    pub fn history_offset(&self) -> usize {
        self.history_offset
    }

    pub fn history_size(&self) -> usize {
        self.history.len()
    }

    fn validate_flags(&self, flags: u8) -> BulkResult<u8> {
        if flags & !VALID_FLAG_MASK != 0 {
            return Err(BulkError::new("Reserved bulk-compression flag is set"));
        }

        let packet_type = flags & TYPE_MASK;
        if packet_type != self.compression_type {
            return Err(BulkError::new(format!(
                "Bulk-compression type changed from {} to {}",
                self.compression_type, packet_type
            )));
        }

        if flags & AT_FRONT != 0 && flags & COMPRESSED == 0 {
            return Err(BulkError::new("PACKET_AT_FRONT requires PACKET_COMPRESSED"));
        }
        Ok(flags)
    }

    fn decode_copy_offset(&self, reader: &mut BitReader<'_>) -> BulkResult<usize> {
        // The initial "11" copy-tuple prefix has already been consumed.
        if self.compression_type == RDP4_8K {
            if reader.read_bits(1)? == 0 {
                return Ok(320 + reader.read_bits(13)?);
            }
            if reader.read_bits(1)? == 0 {
                return Ok(64 + reader.read_bits(8)?);
            }
            return reader.read_bits(6);
        }

        if reader.read_bits(1)? == 0 {
            return Ok(2368 + reader.read_bits(16)?);
        }
        if reader.read_bits(1)? == 0 {
            return Ok(320 + reader.read_bits(11)?);
        }
        if reader.read_bits(1)? == 0 {
            return Ok(64 + reader.read_bits(8)?);
        }
        reader.read_bits(6)
    }

    fn decode_match_length(&self, reader: &mut BitReader<'_>) -> BulkResult<usize> {
        if reader.read_bits(1)? == 0 {
            return Ok(3);
        }

        let max_extra_bits = if self.compression_type == RDP4_8K {
            12
        } else {
            15
        };
        let mut extra_bits = 2usize;
        loop {
            if reader.read_bits(1)? == 0 {
                break;
            }
            extra_bits += 1;
            if extra_bits > max_extra_bits {
                return Err(BulkError::new("Invalid MPPC length-of-match prefix"));
            }
        }
        Ok((1usize << extra_bits) | reader.read_bits(extra_bits)?)
    }

    fn append_copy(
        &self,
        output: &mut Vec<u8>,
        history: &[u8],
        start_offset: usize,
        copy_offset: usize,
        length: usize,
    ) -> BulkResult<()> {
        let history_size = self.history_size();
        if copy_offset == 0 || copy_offset >= history_size {
            return Err(BulkError::new(
                "MPPC copy offset is outside the history window",
            ));
        }
        if length < 3 {
            return Err(BulkError::new("MPPC match is shorter than three bytes"));
        }
        if output.len() + length > self.max_output_size {
            return Err(BulkError::new(
                "MPPC output exceeds the configured decompression limit",
            ));
        }
        if start_offset + output.len() + length > history_size {
            return Err(BulkError::new("MPPC output overruns the history buffer"));
        }

        for _ in 0..length {
            let source = (start_offset + output.len() + history_size - copy_offset) % history_size;
            let output_end = start_offset + output.len();
            let value = if start_offset <= source && source < output_end {
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
    ) -> BulkResult<Vec<u8>> {
        let mut reader = BitReader::new(data, false);
        let mut output = Vec::new();

        while reader.remaining_bits() >= 8 {
            if reader.read_bits(1)? == 0 {
                output.push(reader.read_bits(7)? as u8);
            } else if reader.read_bits(1)? == 0 {
                output.push(0x80 | reader.read_bits(7)? as u8);
            } else {
                let copy_offset = self.decode_copy_offset(&mut reader)?;
                let match_length = self.decode_match_length(&mut reader)?;
                self.append_copy(
                    &mut output,
                    history,
                    start_offset,
                    copy_offset,
                    match_length,
                )?;
            }

            if output.len() > self.max_output_size {
                return Err(BulkError::new(
                    "MPPC output exceeds the configured decompression limit",
                ));
            }
            if start_offset + output.len() > self.history_size() {
                return Err(BulkError::new("MPPC output overruns the history buffer"));
            }
        }

        if !reader.padding_is_zero() {
            return Err(BulkError::new("Nonzero MPPC padding bits"));
        }
        Ok(output)
    }

    pub fn decompress(
        &mut self,
        data: &[u8],
        flags: u8,
        expected_size: Option<usize>,
    ) -> BulkResult<Vec<u8>> {
        let flags = self.validate_flags(flags)?;
        let flushed = flags & FLUSHED != 0;
        let mut working_history = if flushed {
            vec![0; self.history_size()]
        } else {
            self.history.clone()
        };
        let mut start_offset = if flushed { 0 } else { self.history_offset };

        if flags & COMPRESSED == 0 {
            if expected_size.is_some_and(|size| data.len() != size) {
                return Err(BulkError::new(
                    "Uncompressed packet length does not match its declaration",
                ));
            }
            if flushed {
                self.history = working_history;
                self.history_offset = 0;
            }
            return Ok(data.to_vec());
        }

        if flags & AT_FRONT != 0 {
            start_offset = 0;
        }

        let output = self.decode_stream(data, &working_history, start_offset)?;
        if let Some(expected_size) = expected_size {
            if output.len() != expected_size {
                return Err(BulkError::new(format!(
                    "Decompressed packet length does not match its declaration ({} != {})",
                    output.len(),
                    expected_size
                )));
            }
        }

        let end_offset = start_offset + output.len();
        working_history[start_offset..end_offset].copy_from_slice(&output);
        self.history = working_history;
        self.history_offset = end_offset;
        Ok(output)
    }
}

#[cfg(test)]
mod tests {
    use super::MppcDecoder;
    use crate::types::{AT_FRONT, COMPRESSED, RDP4_8K};

    struct BitWriter {
        bits: Vec<bool>,
    }

    impl BitWriter {
        fn new() -> Self {
            Self { bits: Vec::new() }
        }

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

    fn add_literal(writer: &mut BitWriter, value: u8) {
        if value < 0x80 {
            writer.add(usize::from(value), 8);
        } else {
            writer.add_text("10");
            writer.add(usize::from(value & 0x7f), 7);
        }
    }

    fn add_rdp4_copy(writer: &mut BitWriter, copy_offset: usize, match_length: usize) {
        if copy_offset < 64 {
            writer.add_text("1111");
            writer.add(copy_offset, 6);
        } else if copy_offset < 320 {
            writer.add_text("1110");
            writer.add(copy_offset - 64, 8);
        } else {
            writer.add_text("110");
            writer.add(copy_offset - 320, 13);
        }

        if match_length == 3 {
            writer.add_text("0");
        } else {
            let extra_bits = usize::BITS as usize - match_length.leading_zeros() as usize - 1;
            for _ in 0..extra_bits - 1 {
                writer.add_text("1");
            }
            writer.add_text("0");
            writer.add(match_length & ((1 << extra_bits) - 1), extra_bits);
        }
    }

    #[test]
    fn decodes_literals_and_overlapping_copy() {
        let mut writer = BitWriter::new();
        for value in b"abc" {
            add_literal(&mut writer, *value);
        }
        add_rdp4_copy(&mut writer, 3, 6);

        let mut decoder = MppcDecoder::new(RDP4_8K, None).unwrap();
        let output = decoder
            .decompress(&writer.into_bytes(), RDP4_8K | COMPRESSED | AT_FRONT, None)
            .unwrap();
        assert_eq!(output, b"abcabcabc");
        assert_eq!(decoder.history_offset(), 9);
    }

    #[test]
    fn copy_offset_wraps_across_history_front() {
        let mut decoder = MppcDecoder::new(RDP4_8K, None).unwrap();
        let history_size = decoder.history_size();
        decoder.history[history_size - 3..].copy_from_slice(b"abc");

        let mut writer = BitWriter::new();
        add_rdp4_copy(&mut writer, 3, 3);
        let output = decoder
            .decompress(&writer.into_bytes(), RDP4_8K | COMPRESSED | AT_FRONT, None)
            .unwrap();
        assert_eq!(output, b"abc");
    }

    #[test]
    fn malformed_stream_does_not_mutate_history() {
        let mut decoder = MppcDecoder::new(RDP4_8K, None).unwrap();
        decoder.history[..4].copy_from_slice(b"seed");
        decoder.history_offset = 4;
        let history_before = decoder.history.clone();

        let error = decoder
            .decompress(&[0xff], RDP4_8K | COMPRESSED, None)
            .unwrap_err();

        assert!(error.to_string().contains("Truncated bulk-compression"));
        assert_eq!(decoder.history_offset(), 4);
        assert_eq!(decoder.history, history_before);
    }
}
