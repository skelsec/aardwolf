/*
most of the code is taken from https://github.com/citronneur/rdp-rs
the rest is written by me :)

MIT License

Copyright (c) 2019 Sylvain Peyrefitte

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

use std::io::{Cursor, Read};
use byteorder::{ReadBytesExt, LittleEndian};
use std::io::Error as IoError;
use std::string::String;
use num_enum::{TryFromPrimitive, TryFromPrimitiveError};

use pyo3::prelude::*;
use pyo3::exceptions::PyTypeError;
use pyo3::types::PyByteArray;

use pyo3::ffi::{Py_buffer, PyArg_ParseTuple, PyErr_SetString, PyExc_TypeError, Py_None, PyObject, PyExc_OverflowError};
use pyo3::{exceptions, pyfunction, pymodule, PyResult, Python, wrap_pyfunction};
use pyo3::exceptions::PyValueError;
use pyo3::buffer::PyBuffer;
use pyo3::types::PyModule; 

#[derive(Debug, Copy, Clone, Eq, PartialEq)]
pub enum RdpErrorKind {
    /// Unexpected data
    InvalidData,
    /// Respond from server or client is not valid
    InvalidRespond,
    /// Features not implemented
    NotImplemented,
    /// During connection sequence
    /// A security level is negotiated
    /// If no level can be defined a ProtocolNegFailure is emitted
    ProtocolNegFailure,
    /// Protocol automata transition is not expected
    InvalidAutomata,
    /// A security protocol
    /// selected was not handled by rdp-rs
    InvalidProtocol,
    /// All messages in rdp-rs
    /// are based on Message trait
    /// To retrieve the original data we used
    /// a visitor pattern. If the expected
    /// type is not found an InvalidCast error is emited
    InvalidCast,
    /// If an expected value is not equal
    InvalidConst,
    /// During security exchange some
    /// checksum are computed
    InvalidChecksum,
    InvalidOptionalField,
    InvalidSize,
    /// A possible Man In The Middle attack
    /// detected during NLA Authentication
    PossibleMITM,
    /// Some channel or user can be rejected
    /// by server during connection step
    RejectedByServer,
    /// Disconnect receive from server
    Disconnect,
    /// Indicate an unknown field
    Unknown,
    UnexpectedType
}

#[derive(Debug)]
pub struct RdpError {
    /// Kind of error
    kind: RdpErrorKind,
    /// Associated message of the context
    message: String
}

impl RdpError {
    /// create a new RDP error
    /// # Example
    /// ```
    /// use rdp::model::error::{RdpError, RdpErrorKind};
    /// let error = RdpError::new(RdpErrorKind::Disconnect, "disconnected");
    /// ```
    pub fn new (kind: RdpErrorKind, message: &str) -> Self {
        RdpError {
            kind,
            message: String::from(message)
        }
    }

    /// Return the kind of error
    ///
    /// # Example
    /// ```
    /// use rdp::model::error::{RdpError, RdpErrorKind};
    /// let error = RdpError::new(RdpErrorKind::Disconnect, "disconnected");
    /// assert_eq!(error.kind(), RdpErrorKind::Disconnect)
    /// ```
    pub fn kind(&self) -> RdpErrorKind {
        self.kind
    }
}

#[derive(Debug)]
pub enum Error {
    /// RDP error
    RdpError(RdpError),
    /// All kind of IO error
    Io(IoError),
    /// try error
    TryError(String)
}

/// From IO Error
impl From<IoError> for Error {
    fn from(e: IoError) -> Self {
        Error::Io(e)
    }
}

impl<T: TryFromPrimitive> From<TryFromPrimitiveError<T>> for Error {
    fn from(_: TryFromPrimitiveError<T>) -> Self {
        Error::RdpError(RdpError::new(RdpErrorKind::InvalidCast, "Invalid enum conversion"))
    }
}

pub type RdpResult<T> = Result<T, Error>;

/// Try options is waiting try trait for the next rust
#[macro_export]
macro_rules! try_option {
    ($val: expr, $expr: expr) => {
         if let Some(x) = $val {
            Ok(x)
         } else {
            Err(Error::RdpError(RdpError::new(RdpErrorKind::InvalidOptionalField, $expr)))
         }
    }
}

#[macro_export]
macro_rules! try_let {
    ($ident: path, $val: expr) => {
         if let $ident(x) = $val {
            Ok(x)
         } else {
            Err(Error::RdpError(RdpError::new(RdpErrorKind::InvalidCast, "Invalid Cast")))
         }
    }
}



/// All this uncompress code
/// Are directly inspired from the source code
/// of rdesktop and diretly port to rust
/// Need a little bit of refactoring for rust

fn process_plane(input: &mut dyn Read, width: u32, height: u32, output: &mut [u8]) -> RdpResult<()> {
    let mut indexw;
	let mut indexh= 0;
	let mut code ;
	let mut collen;
	let mut replen;
	let mut color:i8;
	let mut x;
	let mut revcode;

    let mut this_line: u32;
    let mut last_line: u32 = 0;

	while indexh < height {
		let mut out = (width * height * 4) - ((indexh + 1) * width * 4);
		color = 0;
		this_line = out;
		indexw = 0;
		if last_line == 0 {
			while indexw < width {
				code = input.read_u8()?;
				replen = code & 0xf;
				collen = (code >> 4) & 0xf;
				revcode = (replen << 4) | collen;
				if (revcode <= 47) && (revcode >= 16) {
					replen = revcode;
					collen = 0;
				}
				while collen > 0 {
					color = input.read_u8()? as i8;
					output[out as usize] = color as u8;
					out += 4;
					indexw += 1;
					collen -= 1;
				}
				while replen > 0 {
					output[out as usize] = color as u8;
					out += 4;
					indexw += 1;
					replen -= 1;
				}
			}
		}
		else
		{
			while indexw < width {
				code = input.read_u8()?;
				replen = code & 0xf;
				collen = (code >> 4) & 0xf;
				revcode = (replen << 4) | collen;
				if (revcode <= 47) && (revcode >= 16) {
					replen = revcode;
					collen = 0;
				}
				while collen > 0 {
					x = input.read_u8()?;
					if x & 1 != 0{
						x = x >> 1;
						x = x + 1;
						color = -(x as i32) as i8;
					}
					else
					{
						x = x >> 1;
						color = x as i8;
					}
					x = (output[(last_line + (indexw * 4)) as usize] as i32 + color as i32) as u8;
					output[out as usize] = x;
					out += 4;
					indexw += 1;
					collen -= 1;
				}
				while replen > 0 {
					x = (output[(last_line + (indexw * 4)) as usize] as i32 + color as i32) as u8;
					output[out as usize] = x;
					out += 4;
					indexw += 1;
					replen -= 1;
				}
			}
		}
		indexh += 1;
		last_line = this_line;
	}
    Ok(())
}

/// Run length encoding decoding function for 32 bpp
pub fn rle_32_decompress(input: &[u8], width: u32, height: u32, output: &mut [u8]) -> RdpResult<()> {
    let mut input_cursor = Cursor::new(input);

	if input_cursor.read_u8()? != 0x10 {
		return Err(Error::RdpError(RdpError::new(RdpErrorKind::UnexpectedType, "Bad header")))
	}

	process_plane(&mut input_cursor, width, height, &mut output[3..])?;
	process_plane(&mut input_cursor, width, height, &mut output[2..])?;
	process_plane(&mut input_cursor, width, height, &mut output[1..])?;
	process_plane(&mut input_cursor, width, height, &mut output[0..])?;

	Ok(())
}

macro_rules! repeat {
    ($expr:expr, $count:expr, $x:expr, $width:expr) => {
    	while (($count & !0x7) != 0) && ($x + 8) < $width {
    		$expr; $count -= 1; $x += 1;
    		$expr; $count -= 1; $x += 1;
    		$expr; $count -= 1; $x += 1;
    		$expr; $count -= 1; $x += 1;
    		$expr; $count -= 1; $x += 1;
    		$expr; $count -= 1; $x += 1;
    		$expr; $count -= 1; $x += 1;
    		$expr; $count -= 1; $x += 1;
		}
		while $count > 0 && $x < $width {
			$expr;
			$count -= 1;
			$x += 1;
		}
    };
}

pub fn rle_16_decompress(input: &[u8], width: usize, mut height: usize, output: &mut [u16]) -> RdpResult<()> {
	let mut input_cursor = Cursor::new(input);

	let mut code: u8;
	let mut opcode: u8;
	let mut lastopcode: u8 = 0xFF;
	let mut count: u16;
	let mut offset: u16;
	let mut isfillormix;
	let mut insertmix = false;
	let mut x: usize = width;
	let mut prevline : Option<usize> = None;
	let mut line : Option<usize> = None;
	let mut colour1= 0;
	let mut colour2 = 0;
	let mut mix = 0xffff;
	let mut mask:u8 = 0;
	let mut fom_mask : u8;
	let mut mixmask:u8;
	let mut bicolour = false;

	while (input_cursor.position() as usize) < input.len() {
		fom_mask = 0;
		code = input_cursor.read_u8()?;
		opcode = code >> 4;

		match opcode {
			0xC | 0xD | 0xE => {
				opcode -= 6;
				count = (code & 0xf) as u16;
				offset = 16;
			}
			0xF => {
				opcode = code & 0xf;
				if opcode < 9 {
					count = input_cursor.read_u16::<LittleEndian>()?
				} else if opcode < 0xb {
					count = 8
				} else {
					count = 1
				}
				offset = 0;
			}
			_ => {
				opcode >>= 1;
				count = (code & 0x1f) as u16;
				offset = 32;
			}
		}

		if offset != 0 {
			isfillormix = (opcode == 2) || (opcode == 7);
			if count == 0 {
				if isfillormix {
					count = input_cursor.read_u8()? as u16 + 1;
				} else {
					count = input_cursor.read_u8()? as u16 + offset;
				}
			} else if isfillormix {
				count <<= 3;
			}
		}

		match opcode {
			0 => {
				if lastopcode == opcode && !(x == width && prevline == None) {
					insertmix = true;
				}
			},
			8 => {
				colour1 = input_cursor.read_u16::<LittleEndian>()?;
				colour2 = input_cursor.read_u16::<LittleEndian>()?;
			},
			3 => {
				colour2 = input_cursor.read_u16::<LittleEndian>()?;
			},
			6 | 7 => {
				mix = input_cursor.read_u16::<LittleEndian>()?;
				opcode -= 5;
			}
			9 => {
				mask = 0x03;
				opcode = 0x02;
				fom_mask = 3;
			},
			0xa => {
				mask = 0x05;
				opcode = 0x02;
				fom_mask = 5;
			}
			_ => ()
		}
		lastopcode = opcode;
		mixmask = 0;

		while count > 0 {
			if x >= width {
				if height <= 0 {
					return Err(Error::RdpError(RdpError::new(RdpErrorKind::InvalidData, "error during decompress")))
				}
				x = 0;
				height -= 1;
				prevline = line;
				line = Some(height * width);
			}

			match opcode {
				0 => {
					if insertmix {
						if let Some(e) = prevline {
							output[line.unwrap() + x] = output[e + x] ^ mix;
						}
						else {
							output[line.unwrap() + x] = mix;
						}
						insertmix = false;
						count -= 1;
						x += 1;
					}

					if let Some(e) = prevline {
						repeat!(output[line.unwrap() + x] = output[e + x], count, x, width);
					}
					else {
						repeat!(output[line.unwrap() + x] = 0, count, x, width);
					}
				},
				1 => {
					if let Some(e) = prevline {
						repeat!(output[line.unwrap() + x] = output[e + x] ^ mix, count, x, width);
					}
					else {
						repeat!(output[line.unwrap() + x] = mix, count, x, width);
					}
				},
				2 => {
					if let Some(e) = prevline {
						repeat!({
							mixmask <<= 1;
							if mixmask == 0 {
								mask = if fom_mask != 0 { fom_mask } else { input_cursor.read_u8()? };
								mixmask = 1;
							}
							if (mask & mixmask) != 0 {
								output[line.unwrap() + x] = output[e + x] ^ mix;
							}
							else {
								output[line.unwrap() + x] = output[e + x];
							}
						}, count, x, width);
					}
					else {
						repeat!({
							mixmask <<= 1;
							if mixmask == 0 {
								mask = if fom_mask != 0 { fom_mask } else { input_cursor.read_u8()? };
								mixmask = 1;
							}
							if (mask & mixmask) != 0 {
								output[line.unwrap() + x] = mix;
							}
							else {
								output[line.unwrap() + x] = 0;
							}
						}, count, x, width);
					}
				},
				3 => {
					repeat!(output[line.unwrap() + x] = colour2, count, x, width);
				},
				4 => {
					repeat!(output[line.unwrap() + x] = input_cursor.read_u16::<LittleEndian>()?, count, x, width);
				},
				8 => {
					repeat!({
						if bicolour {
							output[line.unwrap() + x] = colour2;
							bicolour = false;
						} else {
							output[line.unwrap() + x] = colour1;
							bicolour = true;
							count += 1;
						};
					}, count, x, width);
				},
				0xd => {
					repeat!(output[line.unwrap() + x] = 0xffff, count, x, width);
				},
				0xe => {
					repeat!(output[line.unwrap() + x] = 0, count, x, width);
				}
				_ => panic!("opcode")
			}
		}
	}

	Ok(())
}

//Changed 2 lines of code for GBR -> RBG conversion: skelsec
pub fn rgb565torgb32(input: &[u16], width: usize, height: usize) -> Vec<u8> {
	let mut result_32_bpp = vec![0 as u8; width as usize * height as usize * 4];
	for i in 0..height {
		for j in 0..width {
			let index = (i * width + j) as usize;
			let v = input[index];
			result_32_bpp[index * 4 + 3] = 0xff;
			result_32_bpp[index * 4 + 2] = ((((v & 0x1f) * 527) + 23) >> 6) as u8;
			result_32_bpp[index * 4 + 1] = (((((v >> 5) & 0x3f) * 259) + 33) >> 6) as u8;
			result_32_bpp[index * 4] = (((((v >> 11) & 0x1f) * 527) + 23) >> 6) as u8; 
		}
	}
	result_32_bpp
}




/*
	#########################################################################################################
	######################################################################################################### 
	#						THE MESS BELOW IS SKELSEC
	#
	#########################################################################################################
	#########################################################################################################
*/


fn convert_rgb555_rgb32(decomp_buff: Vec<u8>, decomp_buff_size: usize, dst: &mut Vec<u8>, _dst_size: usize) {
    let mut j = 0;
    for i in (0..decomp_buff_size).step_by(2) {
        let t = ((decomp_buff[i+1] as u16) << 8) + decomp_buff[i] as u16;
        dst[j]   = (t >> 8) as u8;
        dst[j+1] = (((t >> 5) & 0b11111) << 3) as u8;
        dst[j+2] = ((t & 0x1F) as u8) << 3;
        dst[j+3] = 0xff;
        j += 4;
    }
}

fn convert_rgb565_rgb32(decomp_buff: Vec<u8>, decomp_buff_size: usize, dst: &mut Vec<u8>, _dst_size: usize) {
    let mut j = 0;
    for i in (0..decomp_buff_size).step_by(2) {
        let t = ((decomp_buff[i+1] as u16) << 8) + decomp_buff[i] as u16;
        dst[j]   = (t >> 8) as u8;
        dst[j+1] = (((t >> 5) & 0b111111) << 2) as u8;
        dst[j+2] = ((t & 0x1F) as u8) << 3;
        dst[j+3] = 0xff;
        j += 4;
    }
}

fn convert_rgb24_rgb32(decomp_buff: Vec<u8>, decomp_buff_size: usize, dst: &mut Vec<u8>, _dst_size: usize) {
    let mut j = 0;
    for i in (0..decomp_buff_size).step_by(3) {
        dst[j]   = decomp_buff[i];
        dst[j+1] = decomp_buff[i+1];
        dst[j+2] = decomp_buff[i+2];
        dst[i+3] = 0xff;
        j += 4;
    }
}

fn convert_rgbx_rgba(decomp_buff: Vec<u8>, decomp_buff_size: usize, dst: &mut Vec<u8>) {
    for i in (0..decomp_buff_size).step_by(4) {
        dst[i]   = decomp_buff[i];
        dst[i+1] = decomp_buff[i+1];
        dst[i+2] = decomp_buff[i+2];
        dst[i+3] = 0xff;
    }
}

fn decode_rre(rre_buff: Vec<u8>, rre_buff_size: usize, dst: &mut Vec<u8>, bypp: u16, width: u16, height: u16) -> i16 {
	let dst_size: usize = dst.len();
    let sub_rect_num  = ((rre_buff[0] as u32) << 24) + ((rre_buff[1] as u32) << 16) + ((rre_buff[2] as u32) << 8) + rre_buff[3] as u32;
    let sub_rect_num_bytes = sub_rect_num*12;
    let rectangle_pixel_count = width * height;
    let rectangle_size = rectangle_pixel_count * bypp;
    let mut sub_rectangle_pixel_count = 0;
    let mut subrect_color_offset = 0;
    let mut subwidth_bytes = 0;
    let mut subx = 0u16;
    let mut suby = 0u16;
    let mut subwidth = 0u16;
    let mut subheight = 0u16;
    let mut substart = 0u16;
    
    if rectangle_size as usize > dst_size {
        return 1;
    }

    // filling rectangle with default pattern
    for i in (0..rectangle_size).step_by(bypp as usize) {
        dst[i as usize]     = rre_buff[4];
        dst[(i+1) as usize] = rre_buff[5];
        dst[(i+2) as usize] = rre_buff[6];
        dst[(i+3) as usize] = 0xff; // alpha channel
    }
    
    //println!("rs dst: {:?}", dst);

    if sub_rect_num*12+8 != rre_buff_size as u32 {
        //println!("sub_rect_num {}", sub_rect_num);
        //println!("boundary: {}", sub_rect_num*12+8);
        //println!("rre_buff_size: {}", rre_buff_size);
        return 1;
    }

    for i in (0..sub_rect_num_bytes).step_by(12) {
        //memo: 12 = 4(RGBX) + subx, suby, subwidth, subheight
        subx = ((rre_buff[(8+4+i) as usize] as u16) << 8) + rre_buff[(8+5+i) as usize] as u16;
        suby = ((rre_buff[(8+6+i) as usize] as u16) << 8) + rre_buff[(8+7+i) as usize] as u16;
        subwidth = ((rre_buff[(8+8+i) as usize] as u16) << 8) + rre_buff[(8+9+i) as usize] as u16;
        subwidth_bytes = subwidth * 4;
        subheight = ((rre_buff[(8+10+i) as usize] as u16) << 8) + rre_buff[(8+11+i) as usize] as u16;
        sub_rectangle_pixel_count = subwidth * subheight;
        subrect_color_offset = 8+i;
        
        for j in 0..sub_rectangle_pixel_count {
            for y in 0..subheight {
                substart = (subx + (suby+y) * width) * bypp;
                if substart > dst_size as u16 || substart + subwidth_bytes > dst_size as u16 {
                    return 1;
                }

                for x in (0..subwidth_bytes).step_by(4) {
                    dst[(substart+x  ) as usize] = rre_buff[(subrect_color_offset  ) as usize];
                    dst[(substart+x+1) as usize] = rre_buff[(subrect_color_offset+1) as usize];
                    dst[(substart+x+2) as usize] = rre_buff[(subrect_color_offset+2) as usize];
                    dst[(substart+x+3) as usize] = 0xff; // alpha channel
                }
            }
        }
    }
    return 0;
}
  
// *INDENT-ON*
#[pyfunction]
#[pyo3(name = "bitmap_decompress")]
fn bitmap_decompress_wrapper(py: Python<'_>, input: PyBuffer<u8>, width: usize, height: usize, bpp: usize, is_compressed: usize) -> PyResult<&PyByteArray> {
	// actually only handle 32 bpp

	let mut data = input.to_vec(py).unwrap();
	
	if bpp == 32  {
			// 32 bpp is straight forward
			return Ok(
				if is_compressed != 0  {
					let mut result = vec![0 as u8; width as usize * height as usize * 4];
					match rle_32_decompress(&data, width as u32, height as u32, &mut result){
						Err(e) => {
							return Err(PyTypeError::new_err("Decompression Error 32"));
						},
						Ok(x) => {
							let output_as_bytes = PyByteArray::new(py, &result);
							//return Ok(output_as_bytes);
							output_as_bytes
						}
					}
					
				} else {
					let output_as_bytes = PyByteArray::new(py, &data);
					//return Ok(output_as_bytes);
					output_as_bytes
				}
			)
	}
	if bpp == 16  {
		// 16 bpp is more consumer
		if is_compressed != 0 {
			let mut result = vec![0 as u16; width as usize * height as usize * 2];
			let res = match rle_16_decompress(&data, width as usize, height as usize, &mut result){
				Err(e) => {
					return Err(PyTypeError::new_err("Decompression Error 16"));
				},
				Ok(()) => {
					let mut output_buffer = rgb565torgb32(&result, width as usize, height as usize);
					let output_as_bytes = PyByteArray::new(py, &mut output_buffer);
					return Ok(output_as_bytes)
				},
				
			};
			res
			
		} else {
			let mut result = vec![0 as u16; width as usize * height as usize];
			for i in 0..height {
				for j in 0..width {
					let src = (((height - i - 1) * width + j) * 2) as usize;
					result[(i * width + j) as usize] = (data[src + 1] as u16) << 8 | data[src] as u16;
				}
			}
			let mut output_buffer = rgb565torgb32(&result, width as usize, height as usize);
			let output_as_bytes = PyByteArray::new(py, &mut output_buffer);
			return Ok(output_as_bytes)
		};
			
	}
	return Err(PyTypeError::new_err("Unsupported bpp!"));
}


#[pyfunction]
#[pyo3(name = "mask_rgbx")]
fn mask_rgbx_wrapper(py: Python<'_>, input: PyBuffer<u8>) -> PyResult<&PyByteArray> {
    let mut output_buffer = vec![0 as u8; input.len_bytes() as usize];
    convert_rgbx_rgba(input.to_vec(py).unwrap(), input.len_bytes(), &mut output_buffer);
    return Ok(PyByteArray::new(py, &output_buffer));
}

#[pyfunction]
#[pyo3(name = "decode_rre")]
fn decode_rre_wrapper(py: Python<'_>, input: PyBuffer<u8>, width: u16, height: u16, bypp: u16) -> PyResult<&PyByteArray> {
    let mut output_buffer = vec![0 as u8; width as usize * height as usize * bypp as usize];
    if decode_rre(input.to_vec(py).unwrap(), input.len_bytes(), &mut output_buffer, bypp, width, height) != 0 {
        return Err(PyTypeError::new_err("Decode failed!"));
    }
    return Ok(PyByteArray::new(py, &output_buffer));
}

#[pymodule]
fn librlers(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(bitmap_decompress_wrapper, m)?)?;
    m.add_function(wrap_pyfunction!(mask_rgbx_wrapper,         m)?)?;
    m.add_function(wrap_pyfunction!(decode_rre_wrapper,        m)?)?;
    Ok(())
}

  