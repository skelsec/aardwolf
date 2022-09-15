/*
   rdesktop: A Remote Desktop Protocol client.
   Bitmap decompression routines
   Copyright (C) Matthew Chapman <matthewc.unsw.edu.au> 1999-2008

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

*/

/*
    Added few modifications:
    The code now ALWAYS returns RGB32 format regardless of input bpp. Makes life easier on upper levels.
    The code also takes non-compressed input (and a flag that indicates wether it's compressed or not.)
    Non-compressed data will be only converted to RGB32.
    There are some out-of-bounds write possibilities in the RRE decoder.

    Mod author: Tamas Jos @skelsec
*/

/*
    Portation to Rust:
    The original C code is now ported to Rust code.
    The functions bitmap_decompress2, mask_rgbx, decode_rre, their wrapper and all the functions that
    get called by those one are tested and are working.
    The rest is not tested yet so that it may contain any logical bugs.
    However, all functions are syntactically correct and do compile.

    I am the author and tester of this code. I am not the sole owner or the algorithm developer.
    The sole owner is Tamas Jos @skelsec.

    Mod author: Julien Schminke @ProgrammerSkill
    Fiverr: ProgrammerSkill
 */

use std::ffi::CString;
use std::slice;

use pyo3::prelude::*;
use pyo3::exceptions::PyTypeError;
use pyo3::types::PyByteArray;

use pyo3::ffi::{Py_buffer, PyArg_ParseTuple, PyErr_SetString, PyExc_TypeError, Py_None, PyObject};
use pyo3::{exceptions, pyfunction, pymodule, PyResult, Python, wrap_pyfunction};
use pyo3::buffer::PyBuffer;
use pyo3::types::PyModule;

#[macro_use] extern crate lazy_static;

macro_rules! cval {
    ($p:expr, $p_index:expr) => ({
        let c = $p[$p_index];
        $p_index += 1;
        c
    })
}

macro_rules! cval2 {
    ($p:expr, $p_index:expr, $v:expr) => ({
        if cfg!(need_align) && cfg!(l_endian) { // NEED_ALIGN & L_ENDIAN
            $v = $p[$p_index] as u16;
            $p_index += 1;
            $v |= ($p[$p_index] as u16) << 8;
            $p_index += 1;
        } else if cfg!(need_align) { // NEED_ALIGN & !L_ENDIAN
            $v = ($p[$p_index] as u16) << 8;
            $p_index += 1;
            $v |= $p[$p_index] as u16;
            $p_index += 1;
        } else { // !NEED_ALIGN
            $v = (($p[$p_index] as u16) << 8) + $p[$p_index+1] as u16;
            $p_index += 2;
        }
    })
}

macro_rules! unroll8 {
    ($exp:block) => ($exp $exp $exp $exp $exp $exp $exp $exp)
}

macro_rules! repeat {
    ($statement:block, $count:expr, $x:expr, $width:expr) => (
        while ($count & !0x7) != 0 && ($x + 8 < $width) {
            unroll8!({$statement; $count -= 1; $x += 1;});
        }

        while ($count > 0) && ($x < $width) {
            $statement;
            $count -= 1;
            $x += 1;
        }
    );
}

macro_rules! mask_update {
    ($mixmask:expr, $fom_mask:expr, $input_index:expr, $input:expr, $mask:expr) => {
        $mixmask <<= 1;
        if $mixmask == 0 {
            $mask = if $fom_mask != 0 {
                $fom_mask
            } else {
                cval!($input, $input_index)
            };
            $mixmask = 1;
        }
    }
}


// 1 byte bitmap decompress
fn bitmap_decompress1(mut output: &mut Vec<u8>, width: i16, mut height: i16, input: &mut Vec<u8>, _size: usize) -> bool {
    let mut prevline_index = None;
    let mut line_index     = None;
    let mut opcode: i16;
    let mut count: i16;
    let mut offset: i16 = 0;
    let mut isfillormix: bool;
    let mut x = width;
    let mut lastopcode  = -1;
    let mut insertmix  = false;
    let mut bicolour   = false;
    let mut code: u8;
    let mut colour1 = 0u8;
    let mut colour2 = 0u8;
    let mut mixmask: u8;
    let mut mask = 0u8;
    let mut mix = 0xffu8;
    let mut fom_mask = 0;

    let mut input_index = 0;
    while input_index < input.len() {
        fom_mask = 0;
        code = cval!(input, input_index);
        opcode = (code >> 4) as i16;

        // Handle different opcode forms
        match opcode {
            0xc | 0xd | 0xe => {
                opcode -= 6;
                count = (code & 0xf) as i16;
                offset = 16;
            },
            0xf => {
                opcode = (code & 0xf) as i16;
                if opcode < 9 {
                    count  =  cval!(input, input_index) as i16;
                    count |= (cval!(input, input_index) as i16) << 8
                } else {
                    count = if opcode < 0xb { 8 } else { 1 };
                }
                offset = 0;
            }
            _ => {
                opcode >>= 1;
                count = (code & 0x1f) as i16;
                offset = 32;
            },
        }
        // Handle strange cases for counts
        if offset != 0 {
            isfillormix = opcode == 2 || opcode == 7;
            if count == 0 {
                count = if isfillormix {
                    cval!(input, input_index) as i16 + 1
                } else {
                    cval!(input, input_index) as i16 + offset
                }
            } else if isfillormix {
                count <<= 3;
            }
        }

        // Read preliminary data

        // Bicolour
        if opcode == 8 {
            colour1 = cval!(input, input_index);
        }

        match opcode {
            0 => {
                // Fill
                if lastopcode == opcode && !(x == width && prevline_index.is_none()) {
                    insertmix = true;
                }
            },
            3 => {
                // Colour
                colour2 = cval!(input, input_index);
            },
            6 | 7 => {
                // 6 = SetMix/Mix
                // 7 = SetMix/FillOrMix
                mix = cval!(input, input_index);
                opcode -= 5;
            },
            9 => {
                // FillOrMix_1
                mask     = 0x03;
                opcode   = 0x02;
                fom_mask = 3;
            },
            0x0a => {
                // FillOrMix_2
                mask = 0x05;
                opcode = 0x02;
                fom_mask = 5;
            },
            _ => (),
        }
        lastopcode = opcode;
        mixmask = 0;
        // Output body
        while count > 0 {
            if x >= width {
                if height <= 0 {
                    return false;
                }
                x = 0;
                height -= 1;
                prevline_index = line_index;
                line_index = Some(height * width);
            }
            match opcode {
                0 => {
                    // Fill
                    if insertmix {
                        if prevline_index.is_none() {
                            output[(line_index.unwrap()+x) as usize] = mix;
                        } else {
                            output[(line_index.unwrap()+x) as usize] = output[prevline_index.unwrap() as usize]^mix;
                        }
                        insertmix = false;
                        count -= 1;
                        x += 1;
                    }
                    if prevline_index.is_none() {
                        repeat!({output[(line_index.unwrap()+x) as usize] = 0;}, count, x, width);
                    } else {
                        repeat!({output[(line_index.unwrap()+x) as usize] = output[(prevline_index.unwrap() + x) as usize];}, count, x, width);
                    }
                },
                1 => {
                    // Mix
                    if prevline_index.is_none() {
                        repeat!({output[(line_index.unwrap()+x) as usize] = mix;}, count, x, width);
                    } else {
                        repeat!({output[(line_index.unwrap()+x) as usize] = output[(((prevline_index.unwrap()) + x) ^ mix as i16) as usize];}, count, x, width);
                    }
                },
                2 => {
                    //Fill or Mix
                    if prevline_index.is_none() {
                        repeat!({
                            mask_update!(mixmask, fom_mask, input_index, input, mask);
                            if (mask  & mixmask) != 0 {
                                output[(line_index.unwrap()+x) as usize] = mix
                            } else {
                                output[(line_index.unwrap()+x) as usize] = 0;
                            }
                        }, count, x, width);
                    } else {
                        repeat!({
                            mask_update!(mixmask, fom_mask, input_index, input, mask);
                            if (mask  & mixmask) != 0 {
                                output[(line_index.unwrap()+x) as usize] = output[((prevline_index.unwrap()+x) ^ mix as i16) as usize];
                            } else {
                                output[(line_index.unwrap()+x) as usize] = output[(prevline_index.unwrap()+x) as usize]
                            }
                        }, count, x, width);
                    }
                },
                3 => { // Colour
                    repeat!({output[(line_index.unwrap()+x) as usize] = colour2;}, count, x, width);
                },
                4 => { // Copy
                    repeat!({output[(line_index.unwrap()+x) as usize] = cval!(input, input_index);}, count, x, width);
                },
                8 => { // Bicolour
                    repeat!({
                        if bicolour {
                            output[(line_index.unwrap()+x) as usize] = colour2;
                            bicolour = false;
                        } else {
                            output[(line_index.unwrap()+x) as usize] = colour1;
                            bicolour = true;
                            count += 1;
                        }
                    }, count, x, width);
                },
                0xd => { // White
                    repeat!({output[(line_index.unwrap()+x) as usize] = 0xff;}, count, x, width);
                },
                0xe => { // Black
                    repeat!({output[(line_index.unwrap()+x) as usize] = 0;} , count, x, width);
                },
                _ => {
                    return false;
                },
            }
        }
    }
    true
}


// 2 byte bitmap decompress
fn bitmap_decompress2(mut output: &mut Vec<u8>, width: i16, mut height: i16, input: &mut Vec<u8>, _size: usize) -> bool {
    let mut prevline_index = None;
    let mut line_index     = None;
    let mut opcode: i16;
    let mut count: i16;
    let mut offset: i16 = 0;
    let mut isfillormix: bool;
    let mut x = width;
    let mut lastopcode  = -1;
    let mut insertmix  = false;
    let mut bicolour   = false;
    let mut code: u8;
    let mut colour1 = 0u16;
    let mut colour2 = 0u16;
    let mut mixmask: u8;
    let mut mask = 0u8;
    let mut mix = 0xffffu16;
    let mut fom_mask = 0;

    let mut input_index = 0;
    let mut output_u16_clone: Vec<u16> = output
        .chunks_exact(2)
        .into_iter()
        .map(|a| u16::from_ne_bytes([a[0], a[1]]))
        .collect();

    while input_index < input.len() {
        fom_mask = 0;
        code = cval!(input, input_index);
        opcode = (code >> 4) as i16;

        // Handle different opcode forms
        match opcode {
            0xc | 0xd | 0xe => {
                opcode -= 6;
                count = (code & 0xf) as i16;
                offset = 16;
            },
            0xf => {
                opcode = (code & 0xf) as i16;
                if opcode < 9 {
                    count  =  cval!(input, input_index) as i16;
                    count |= (cval!(input, input_index) as i16) << 8
                } else {
                    count = if opcode < 0xb { 8 } else { 1 };
                }
                offset = 0;
            }
            _ => {
                opcode >>= 1;
                count = (code & 0x1f) as i16;
                offset = 32;
            },
        }
        // Handle strange cases for counts
        if offset != 0 {
            isfillormix = opcode == 2 || opcode == 7;
            if count == 0 {
                count = if isfillormix {
                    cval!(input, input_index) as i16 + 1
                } else {
                    cval!(input, input_index) as i16 + offset
                };
                
            } else if isfillormix {
                count <<= 3;
            }
        }

        // Read preliminary data

        // Bicolour
        if opcode == 8 {
            cval2!(input, input_index, colour1);
        }

        match opcode {
            0 => {
                // Fill
                if lastopcode == opcode && !(x == width && prevline_index.is_none()) {
                    insertmix = true;
                }
            },
            3 => {
                // Colour
                cval2!(input, input_index, colour2);
            },
            6 | 7 => {
                // 6 = SetMix/Mix
                // 7 = SetMix/FillOrMix
                cval2!(input, input_index, mix);
                opcode = -5;
            },
            9 => {
                // FillOrMix_1
                mask     = 0x03;
                opcode   = 0x02;
                fom_mask = 3;
            },
            0x0a => {
                // FillOrMix_2
                mask     = 0x05;
                opcode   = 0x02;
                fom_mask = 5;
            },
            _ => (),
        }
        lastopcode = opcode;
        mixmask = 0;

        // Output body
        while count > 0 {
            if x >= width {
                if height <= 0 {
                    for i in 0..output_u16_clone.len() {
                        output[i*2  ] = (output_u16_clone[i] >> 8    ) as u8;
                        output[i*2+1] = (output_u16_clone[i] | 0x00ff) as u8;

                    }
                    return false;
                }
                x = 0;
                height -= 1;
                prevline_index = line_index;
                line_index = Some(height * width);
            }

            match opcode {
                0 => {
                    // Fill
                    if insertmix {

                        if prevline_index.is_none() {
                            output_u16_clone[(line_index.unwrap()+x) as usize] = mix;
                        } else {
                            output_u16_clone[(line_index.unwrap()+x) as usize] = output_u16_clone[(prevline_index.unwrap()+x) as usize] ^ mix;
                        }
                        insertmix = false;
                        count -= 1;
                        x += 1;
                    }
                    if prevline_index.is_none() {
                        repeat!({output_u16_clone[(line_index.unwrap()+x) as usize] = 0}, count, x, width);
                    } else {
                        repeat!({output_u16_clone[(line_index.unwrap()+x) as usize] = output_u16_clone[(prevline_index.unwrap() + x) as usize];}, count, x, width);
                    }
                },
                1 => {
                    // Mix
                    if prevline_index.is_none() {
                        repeat!({output_u16_clone[(line_index.unwrap()+x) as usize] = mix}, count, x, width);
                    } else {
                        repeat!({output_u16_clone[(line_index.unwrap()+x) as usize] = output_u16_clone[(prevline_index.unwrap()+x) as usize] ^ mix}, count, x, width);
                    }
                },
                2 => {
                    //Fill or Mix
                    if prevline_index.is_none() {
                        repeat!({
                            mask_update!(mixmask, fom_mask, input_index, input, mask);
                            if (mask  & mixmask) != 0 {
                                output_u16_clone[(line_index.unwrap()+x) as usize] = mix;
                            } else {
                                output_u16_clone[(line_index.unwrap()+x) as usize] = 0;
                            }
                        }, count, x, width);
                    } else {
                        repeat!({
                            mask_update!(mixmask, fom_mask, input_index, input, mask);
                            if (mask  & mixmask) != 0 {
                                output_u16_clone[(line_index.unwrap()+x) as usize] = output_u16_clone[(prevline_index.unwrap()+x) as usize] ^ mix;
                            } else {
                                output_u16_clone[(line_index.unwrap()+x) as usize] = output_u16_clone[(prevline_index.unwrap()+x) as usize];
                            }
                        }, count, x, width);
                    }
                },
                3 => { // Colour
                    repeat!({output_u16_clone[(line_index.unwrap()+x) as usize] = colour2}, count, x, width); //TODO unsicher mit colour2
                },
                4 => { // Copy
                    repeat!({cval2!(input, input_index, output_u16_clone[(line_index.unwrap()+x) as usize])}, count, x, width);
                },
                8 => { // Bicolour
                    repeat!({
                        if bicolour {
                            output_u16_clone[(line_index.unwrap()+x) as usize] = colour2;
                            bicolour = false;
                        } else {
                            output_u16_clone[(line_index.unwrap()+x) as usize] = colour1;
                            bicolour = true;
                            count += 1;
                        }
                    }, count, x, width);
                },
                0xd => { // White
                    repeat!({output_u16_clone[(line_index.unwrap()+x) as usize] = 0xffff;}, count, x, width);
                },
                0xe => { // Black
                    repeat!({output_u16_clone[(line_index.unwrap()+x) as usize] = 0;} , count, x, width);
                },
                _ => {
                    for i in 0..output_u16_clone.len() {
                        output[i*2  ] = (output_u16_clone[i] >> 8    ) as u8;
                        output[i*2+1] = (output_u16_clone[i] & 0x00ff) as u8;

                    }
                    return false;
                },
            }
        }
    }
    for i in 0..output_u16_clone.len() {
        output[i*2  ] = (output_u16_clone[i] >> 8    ) as u8;
        output[i*2+1] = (output_u16_clone[i] & 0x00ff) as u8;

    }
    true
}

// 3 byte bitmap decompress
fn bitmap_decompress3(mut output: &mut Vec<u8>, width: i16, mut height: i16, input: &mut Vec<u8>, _size: usize) -> bool {
    let mut prevline_index = None;
    let mut line_index     = None;
    let mut opcode: i16;
    let mut count: i16;
    let mut offset: i16 = 0;
    let mut isfillormix: bool;
    let mut x = width;
    let mut lastopcode  = -1;
    let mut insertmix  = false;
    let mut bicolour   = false;
    let mut code: u8;
    let mut colour1 = [0u8, 0, 0];
    let mut colour2 = [0u8, 0, 0];
    let mut mixmask: u8;
    let mut mask = 0u8;
    let mut mix = [0xffu8, 0xff, 0xff];
    let mut fom_mask = 0;

    let mut input_index = 0;
    while input_index < input.len() {
        fom_mask = 0;
        code = cval!(input, input_index);
        opcode = (code >> 4) as i16;

        match opcode {
            0xc | 0xd | 0xe => {
                opcode -= 6;
                count = (code & 0xf) as i16;
                offset = 16;
            },
            0xf => {
                opcode = (code & 0xf) as i16;
                if opcode < 9 {
                    count  =  cval!(input, input_index) as i16;
                    count |= (cval!(input, input_index) as i16) << 8
                } else {
                    count = if opcode < 0xb { 8 } else { 1 };
                }
                offset = 0;
            }
            _ => {
                opcode >>= 1;
                count = (code & 0x1f) as i16;
                offset = 32;
            },
        }
        // Handle strange cases for counts
        if offset != 0 {
            isfillormix = opcode == 2 || opcode == 7;
            if count == 0 {
                count = if isfillormix {
                    cval!(input, input_index) as i16 + 1
                } else {
                    cval!(input, input_index) as i16 + offset
                }
            } else if isfillormix {
                count <<= 3;
            }
        }

        // Read preliminary data

        // Bicolour
        if opcode == 8 {
            colour1[0] = cval!(input, input_index);
            colour1[1] = cval!(input, input_index);
            colour1[2] = cval!(input, input_index);
        }

        match opcode {
            0 => {
                // Fill
                if lastopcode == opcode && !(x == width && prevline_index.is_none()) {
                    insertmix = true;
                }
            },
            3 => {
                // Colour
                colour2[0] = cval!(input, input_index);
                colour2[1] = cval!(input, input_index);
                colour2[2] = cval!(input, input_index);
            },
            6 | 7 => {
                // 6 = SetMix/Mix
                // 7 = SetMix/FillOrMix
                mix[0] = cval!(input, input_index);
                mix[1] = cval!(input, input_index);
                mix[2] = cval!(input, input_index);
                opcode = -5;
            },
            9 => {
                // FillOrMix_1
                mask     = 0x03;
                opcode   = 0x02;
                fom_mask = 3;
            },
            0x0a => {
                // FillOrMix_2
                mask     = 0x05;
                opcode   = 0x02;
                fom_mask = 5;
            },
            _ => (),
        }
        lastopcode = opcode;
        mixmask = 0;
        // Output body
        while count > 0 {
            if x >= width {
                if height <= 0 {
                    return false;
                }
                x = 0;
                height -= 1;
                prevline_index = line_index;
                line_index = Some(height * width * 3);
            }
            match opcode {
                0 => {
                    // Fill
                    if insertmix {
                        if prevline_index.is_none() {
                            output[(line_index.unwrap()+x*3  ) as usize] = mix[0];
                            output[(line_index.unwrap()+x*3+1) as usize] = mix[1];
                            output[(line_index.unwrap()+x*3+2) as usize] = mix[2];
                        } else {
                            output[(line_index.unwrap()+x*3  ) as usize] = output[(prevline_index.unwrap()+x*3  ) as usize] ^ mix[0];
                            output[(line_index.unwrap()+x*3+1) as usize] = output[(prevline_index.unwrap()+x*3+1) as usize] ^ mix[1];
                            output[(line_index.unwrap()+x*3+2) as usize] = output[(prevline_index.unwrap()+x*3+2) as usize] ^ mix[2];
                        }
                        insertmix = false;
                        count -= 1;
                        x += 1;
                    }
                    if prevline_index.is_none() {
                        repeat!({
                            output[(line_index.unwrap()+x*3  ) as usize] = 0;
                            output[(line_index.unwrap()+x*3+1) as usize] = 0;
                            output[(line_index.unwrap()+x*3+2) as usize] = 0;
                        }, count, x, width);
                    } else {
                        repeat!({
                            output[(line_index.unwrap()+x*3  ) as usize] = output[(prevline_index.unwrap()+x*3  ) as usize];
                            output[(line_index.unwrap()+x*3+1) as usize] = output[(prevline_index.unwrap()+x*3+1) as usize];
                            output[(line_index.unwrap()+x*3+2) as usize] = output[(prevline_index.unwrap()+x*3+2) as usize];
                        }, count, x, width);
                    }
                },
                1 => {
                    // Mix
                    if prevline_index.is_none() {
                        repeat!({
                            output[(line_index.unwrap()+x*3  ) as usize] = mix[0];
                            output[(line_index.unwrap()+x*3+1) as usize] = mix[1];
                            output[(line_index.unwrap()+x*3+2) as usize] = mix[2];
                        }, count, x, width);
                    } else {
                        repeat!({
                            output[(line_index.unwrap()+x*3  ) as usize] = output[(prevline_index.unwrap()+x*3  ) as usize] ^ mix[0];
                            output[(line_index.unwrap()+x*3+1) as usize] = output[(prevline_index.unwrap()+x*3+1) as usize] ^ mix[1];
                            output[(line_index.unwrap()+x*3+2) as usize] = output[(prevline_index.unwrap()+x*3+2) as usize] ^ mix[2];
                        }, count, x, width);
                    }
                },
                2 => {
                    //Fill or Mix
                    if prevline_index.is_none() {
                        repeat!({
                            mask_update!(mixmask, fom_mask, input_index, input, mask);
                            if (mask  & mixmask) != 0 {
                                output[(line_index.unwrap()+x*3  ) as usize] = mix[0];
                                output[(line_index.unwrap()+x*3+1) as usize] = mix[1];
                                output[(line_index.unwrap()+x*3+2) as usize] = mix[2];
                            } else {
                                output[(line_index.unwrap()+x*3  ) as usize] = 0;
                                output[(line_index.unwrap()+x*3+1) as usize] = 0;
                                output[(line_index.unwrap()+x*3+2) as usize] = 0;
                            }
                        }, count, x, width);
                    } else {
                        repeat!({
                            mask_update!(mixmask, fom_mask, input_index, input, mask);
                            if (mask  & mixmask) != 0 {
                                output[(line_index.unwrap()+x*3  ) as usize] = output[(prevline_index.unwrap()+x*3  ) as usize] ^ mix[0];
                                output[(line_index.unwrap()+x*3+1) as usize] = output[(prevline_index.unwrap()+x*3+1) as usize] ^ mix[1];
                                output[(line_index.unwrap()+x*3+2) as usize] = output[(prevline_index.unwrap()+x*3+2) as usize] ^ mix[2];
                            } else {
                                output[(line_index.unwrap()+x*3  ) as usize] = output[(prevline_index.unwrap()+x*3  ) as usize];
                                output[(line_index.unwrap()+x*3+1) as usize] = output[(prevline_index.unwrap()+x*3+1) as usize];
                                output[(line_index.unwrap()+x*3+2) as usize] = output[(prevline_index.unwrap()+x*3+2) as usize];
                            }
                        }, count, x, width);
                    }
                },
                3 => { // Colour
                    repeat!({
                        output[(line_index.unwrap()+x*3  ) as usize] = colour2[0];
                        output[(line_index.unwrap()+x*3+1) as usize] = colour2[1];
                        output[(line_index.unwrap()+x*3+2) as usize] = colour2[2];
                    }, count, x, width);
                },
                4 => { // Copy
                    repeat!({
                        output[(line_index.unwrap()+x*3  ) as usize] = cval!(input, input_index);
                        output[(line_index.unwrap()+x*3+1) as usize] = cval!(input, input_index);
                        output[(line_index.unwrap()+x*3+2) as usize] = cval!(input, input_index);
                    }, count, x, width);
                },
                8 => { // Bicolour
                    repeat!({
                        if bicolour {
                            output[(line_index.unwrap()+x*3  ) as usize] = colour2[0];
                            output[(line_index.unwrap()+x*3+1) as usize] = colour2[1];
                            output[(line_index.unwrap()+x*3+2) as usize] = colour2[2];
                            bicolour = false;
                        } else {
                            output[(line_index.unwrap()+x*3  ) as usize] = colour1[0];
                            output[(line_index.unwrap()+x*3+1) as usize] = colour1[1];
                            output[(line_index.unwrap()+x*3+2) as usize] = colour1[2];
                            bicolour = true;
                            count += 1;
                        }
                    }, count, x, width);
                },
                0xd => { // White
                    repeat!({
                        output[(line_index.unwrap()+x*3  ) as usize] = 0xff;
                        output[(line_index.unwrap()+x*3+1) as usize] = 0xff;
                        output[(line_index.unwrap()+x*3+2) as usize] = 0xff;
                }, count, x, width);
                },
                0xe => { // Black
                    repeat!({
                        output[(line_index.unwrap()+x*3  ) as usize] = 0;
                        output[(line_index.unwrap()+x*3+1) as usize] = 0;
                        output[(line_index.unwrap()+x*3+2) as usize] = 0;
                    }, count, x, width);
                },
                _ => {
                    return false;
                },
            }
        }
    }
    true
}

fn process_plane(input: &Vec<u8>, width: i16, height: i16, mut output: &mut Vec<u8>, _size: usize) -> usize {
    let mut indexw;
    let mut indexh = 0;
    let mut code;
    let mut collen;
    let mut replen;
    let mut color;
    let mut x: u8;
    let mut revcode;
    let mut last_line_index = 0;
    let mut this_line_index = 0;
    let mut org_output_index = 0;
    let mut output_index = 0;
    let mut input_index = 0;

    while indexh < height {
        output_index = ((org_output_index + width * height * 4) - ((indexh + 1) * width * 4)) as usize;
        color = 0;
        this_line_index = output_index;
        indexw = 0;
        if last_line_index == 0 {
            while indexw < width {
                code = cval!(input, input_index);
                replen = code & 0xf;
                collen = (code >> 4) & 0xf;
                revcode = (replen << 4) | collen;
                if revcode <= 47 && revcode >= 16 {
                    replen = revcode;
                    collen = 0;
                }
                while collen > 0 {
                    color = cval!(input, input_index);
                    output[output_index] = color;
                    output_index += 4;
                    indexw += 1;
                    collen -= 1;
                }
                while replen > 0 {
                    output[output_index] = color;
                    output_index += 4;
                    indexw += 1;
                    collen -= 1;
                }
            }
        } else {
            while indexw < width {
                code = cval!(input, input_index);
                replen = code & 0xf;
                collen = (code >> 4) & 0xf;
                revcode = (replen << 4) | collen;
                if revcode <= 47 && revcode >= 16 {
                    replen = revcode;
                    collen = 0;
                }
                while collen > 0 {
                    x = cval!(input, input_index);
                    if x & 1 != 0 {
                        x >>= 1;
                        x += 1;
                        color -= x;
                    } else {
                        x >>= 1;
                        color = x;
                    }
                    x = output[last_line_index * 4] + color;
                    output[output_index] = x;
                    output_index += 4;
                    indexw += 1;
                    collen -= 1;
                }
                while replen > 0 {
                    x = output[last_line_index * 4] + color;
                    output[output_index] = x;
                    output_index += 4;
                    indexw += 1;
                    replen -= 1;
                }
            }
        }
        indexh += 1;
        last_line_index = this_line_index;
    }
    return input_index;

}

fn bitmap_decompress4(output: &mut Vec<u8>, width: i16, height: i16, input: &mut Vec<u8>, size: usize) -> bool {
    let code;
    let mut bytes_pro;
    let mut total_pro;
    let mut input_index = 0;

    code = cval!(input, input_index);
    if code != 0x10 {
        return false;
    }
    total_pro = 1;
    bytes_pro = process_plane(&input, width, height, &mut output[3..].to_vec(), size - total_pro);
    total_pro += bytes_pro;
    input[0]  += bytes_pro as u8;
    bytes_pro = process_plane(&input, width, height, &mut output[2..].to_vec(), size - total_pro);
    total_pro += bytes_pro;
    input[0]  += bytes_pro as u8;
    bytes_pro = process_plane(&input, width, height, &mut output[1..].to_vec(), size - total_pro);
    total_pro += bytes_pro;
    input[0]  += bytes_pro as u8;
    bytes_pro = process_plane(&input, width, height, &mut output[0..].to_vec(), size - total_pro);
    total_pro += bytes_pro;
    size == total_pro
}

fn bitmap_decompress(output: &mut Vec<u8>, width: i16, height: i16, input: &mut Vec<u8>, size: usize, bpp: usize) -> bool {
    let mut rv = false;
    match bpp {
        1 => rv = bitmap_decompress1(output, width, height, input, size),
        2 => rv = bitmap_decompress2(output, width, height, input, size),
        3 => rv = bitmap_decompress3(output, width, height, input, size),
        4 => rv = bitmap_decompress4(output, width, height, input, size),
        _ => ()
    }
    rv
}

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

fn convert_rgbx_rgba(decomp_buff: Vec<u8>, decomp_buff_size: usize, dst: &mut Vec<u8>, _dst_size: usize) {
    for i in (0..decomp_buff_size).step_by(4) {
        dst[i]   = decomp_buff[i];
        dst[i+1] = decomp_buff[i+1];
        dst[i+2] = decomp_buff[i+2];
        dst[i+3] = 0xff;
    }
}

fn decode_rre(rre_buff: Vec<u8>, rre_buff_size: usize, dst: &mut Vec<u8>, dst_size: usize, bypp: u16, width: u16, height: u16) -> i16 {
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
        println!("sub_rect_num {}", sub_rect_num);
        println!("boundary: {}", sub_rect_num*12+8);
        println!("rre_buff_size: {}", rre_buff_size);
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
fn bitmap_decompress_wrapper(py: Python<'_>, output: PyBuffer<u8>, width: usize, height: usize, input: PyBuffer<u8>, bitsperpixel: usize, bpp: usize, is_compressed: usize) -> PyResult<&PyByteArray> {
    let mut decomp_size = 0usize;
    let mut decomp_buffer;

    if is_compressed != 0 {
        decomp_size = width * height * bpp;
        decomp_buffer = vec![0; decomp_size];

        if !bitmap_decompress(&mut decomp_buffer, width as i16, height as i16, &mut input.to_vec(py).unwrap(), input.len_bytes(), bpp) {
            return Err(PyTypeError::new_err("Decompression Error"));
        }
    } else {
        decomp_size = input.len_bytes();
        decomp_buffer = input.to_vec(py).unwrap();
    }

    let mut output_buffer = output.to_vec(py).unwrap();

    match bitsperpixel {
        15 => convert_rgb555_rgb32(decomp_buffer, decomp_size, &mut output_buffer, output.len_bytes()),
        16 => convert_rgb565_rgb32(decomp_buffer, decomp_size, &mut output_buffer, output.len_bytes()),
        24 =>  convert_rgb24_rgb32(decomp_buffer, decomp_size, &mut output_buffer, output.len_bytes()),
        32 | _ => (),
    }

    let output_as_bytes = PyByteArray::new(py, &output_buffer);
    return Ok(output_as_bytes);
}

#[pyfunction]
#[pyo3(name = "mask_rgbx")]
fn mask_rgbx_wrapper(py: Python<'_>, output: PyBuffer<u8>, input: PyBuffer<u8>) -> PyResult<&PyByteArray> {
    let mut output_buffer = output.to_vec(py).unwrap();
    convert_rgbx_rgba(input.to_vec(py).unwrap(), input.len_bytes(), &mut output_buffer, output.len_bytes());
    return Ok(PyByteArray::new(py, &output_buffer));
}

#[pyfunction]
#[pyo3(name = "decode_rre")]
fn decode_rre_wrapper(py: Python<'_>, output: PyBuffer<u8>, input: PyBuffer<u8>, width: u16, height: u16, bypp: u16) -> PyResult<&PyByteArray> {
    let mut output_buffer = output.to_vec(py).unwrap();
    if decode_rre(input.to_vec(py).unwrap(), input.len_bytes(), &mut output_buffer, output.len_bytes(), bypp, width, height) != 0 {
        return Err(PyTypeError::new_err("Decode failed!"));
    }
    return Ok(PyByteArray::new(py, &output_buffer));
}

#[pymodule]
fn rle(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(bitmap_decompress_wrapper, m)?)?;
    m.add_function(wrap_pyfunction!(mask_rgbx_wrapper,         m)?)?;
    m.add_function(wrap_pyfunction!(decode_rre_wrapper,        m)?)?;
    Ok(())
}


