use std::collections::HashMap;

use crate::error::{BulkError, BulkResult};

#[derive(Clone, Debug)]
pub struct BitReader<'a> {
    data: &'a [u8],
    bit_position: usize,
    least_significant_bit_first: bool,
}

impl<'a> BitReader<'a> {
    pub fn new(data: &'a [u8], least_significant_bit_first: bool) -> Self {
        Self {
            data,
            bit_position: 0,
            least_significant_bit_first,
        }
    }

    pub fn remaining_bits(&self) -> usize {
        self.data.len() * 8 - self.bit_position
    }

    pub fn read_bits(&mut self, count: usize) -> BulkResult<usize> {
        let remaining = self.remaining_bits();
        if count > remaining {
            return Err(BulkError::new(format!(
                "Truncated bulk-compression bit stream (wanted {count} bits, only {remaining} remain)"
            )));
        }
        if count > usize::BITS as usize {
            return Err(BulkError::new(
                "Bit count exceeds the bulk-compression reader word size",
            ));
        }

        let mut value = 0usize;
        for value_bit in 0..count {
            let byte_index = self.bit_position / 8;
            let bit_index = self.bit_position % 8;
            let shift = if self.least_significant_bit_first {
                bit_index
            } else {
                7 - bit_index
            };
            let bit = usize::from((self.data[byte_index] >> shift) & 1);
            if self.least_significant_bit_first {
                value |= bit << value_bit;
            } else {
                value = (value << 1) | bit;
            }
            self.bit_position += 1;
        }
        Ok(value)
    }

    pub fn padding_is_zero(&self) -> bool {
        let mut reader = self.clone();
        while reader.remaining_bits() != 0 {
            if reader
                .read_bits(1)
                .expect("one remaining bit must be readable")
                != 0
            {
                return false;
            }
        }
        true
    }
}

#[derive(Clone, Debug)]
pub struct HuffmanDecoder {
    codes: HashMap<(usize, usize), usize>,
    max_length: usize,
}

impl HuffmanDecoder {
    pub fn new(
        codes: &[u16],
        lengths: &[u8],
        least_significant_bit_first: bool,
    ) -> BulkResult<Self> {
        if codes.len() != lengths.len() {
            return Err(BulkError::new(
                "Huffman code and length tables differ in size",
            ));
        }

        let mut decoded_codes = HashMap::new();
        let mut max_length = 0usize;
        for (symbol, (&wire_code, &wire_length)) in codes.iter().zip(lengths.iter()).enumerate() {
            let length = usize::from(wire_length);
            if length == 0 {
                return Err(BulkError::new("Huffman code lengths must be positive"));
            }
            if length > usize::BITS as usize {
                return Err(BulkError::new(
                    "Huffman code length exceeds the decoder word size",
                ));
            }

            let mut code = usize::from(wire_code);
            if length < usize::BITS as usize && code >= (1usize << length) {
                return Err(BulkError::new(
                    "Huffman code does not fit its declared length",
                ));
            }
            if least_significant_bit_first {
                let mut reversed_code = 0usize;
                for index in 0..length {
                    let bit = if index < u16::BITS as usize {
                        (code >> index) & 1
                    } else {
                        0
                    };
                    reversed_code = (reversed_code << 1) | bit;
                }
                code = reversed_code;
            }

            if decoded_codes.insert((length, code), symbol).is_some() {
                return Err(BulkError::new("Duplicate Huffman code"));
            }
            max_length = max_length.max(length);
        }

        Ok(Self {
            codes: decoded_codes,
            max_length,
        })
    }

    pub fn decode(&self, reader: &mut BitReader<'_>) -> BulkResult<usize> {
        let mut code = 0usize;
        for length in 1..=self.max_length {
            code = (code << 1) | reader.read_bits(1)?;
            if let Some(&symbol) = self.codes.get(&(length, code)) {
                return Ok(symbol);
            }
        }
        Err(BulkError::new("Invalid bulk-compression Huffman code"))
    }
}

#[cfg(test)]
mod tests {
    use super::{BitReader, HuffmanDecoder};

    #[test]
    fn reads_both_bit_orders_and_preserves_padding_position() {
        let mut most_first = BitReader::new(&[0b1010_0000], false);
        assert_eq!(most_first.read_bits(3).unwrap(), 0b101);
        assert!(most_first.padding_is_zero());
        assert_eq!(most_first.remaining_bits(), 5);

        let mut least_first = BitReader::new(&[0b0000_0101], true);
        assert_eq!(least_first.read_bits(3).unwrap(), 0b101);
        assert!(least_first.padding_is_zero());
        assert_eq!(least_first.remaining_bits(), 5);
    }

    #[test]
    fn decodes_fixed_huffman_codes() {
        let decoder = HuffmanDecoder::new(&[0b0, 0b10, 0b11], &[1, 2, 2], false).unwrap();
        let mut reader = BitReader::new(&[0b1011_0000], false);
        assert_eq!(decoder.decode(&mut reader).unwrap(), 1);
        assert_eq!(decoder.decode(&mut reader).unwrap(), 2);
    }
}
