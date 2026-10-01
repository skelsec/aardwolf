mod bitstream;
mod dispatcher;
mod error;
mod mppc;
mod rdp6;
mod rdp61;
mod types;

use dispatcher::BulkDecompressor;
use error::BulkError;
use pyo3::create_exception;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyBytes, PyBytesMethods, PyModule};

create_exception!(_bulk, BulkCompressionError, PyValueError);

fn constructor_type(raw: i128) -> PyResult<u8> {
    let compression_type = u8::try_from(raw)
        .map_err(|_| PyValueError::new_err(format!("{raw} is not a valid BulkCompressionType")))?;
    if compression_type > types::RDP61 {
        return Err(PyValueError::new_err(format!(
            "{raw} is not a valid BulkCompressionType"
        )));
    }
    Ok(compression_type)
}

fn constructor_output_limit(raw: Option<i128>) -> PyResult<Option<usize>> {
    match raw {
        None => Ok(None),
        Some(value) if value <= 0 => Err(PyValueError::new_err(
            "Maximum decompressed size must be positive",
        )),
        Some(value) => usize::try_from(value).map(Some).map_err(|_| {
            PyValueError::new_err("Maximum decompressed size does not fit the platform word size")
        }),
    }
}

fn packet_flags(raw: i128) -> PyResult<u8> {
    u8::try_from(raw)
        .map_err(|_| BulkCompressionError::new_err("Reserved bulk-compression flag is set"))
}

fn decode_error(error: BulkError) -> PyErr {
    BulkCompressionError::new_err(error.to_string())
}

#[pyclass(module = "_bulk")]
struct NativeBulkDecompressor {
    inner: BulkDecompressor,
}

#[pymethods]
impl NativeBulkDecompressor {
    #[new]
    #[pyo3(signature = (max_compression_type=3, max_output_size=None))]
    fn new(max_compression_type: i128, max_output_size: Option<i128>) -> PyResult<Self> {
        let max_compression_type = constructor_type(max_compression_type)?;
        let max_output_size = constructor_output_limit(max_output_size)?;
        let inner = BulkDecompressor::new(max_compression_type, max_output_size)
            .map_err(|error| PyValueError::new_err(error.to_string()))?;
        Ok(Self { inner })
    }

    #[pyo3(signature = (data, flags, expected_size=None))]
    fn decompress<'py>(
        &mut self,
        py: Python<'py>,
        data: &Bound<'py, PyAny>,
        flags: i128,
        expected_size: Option<usize>,
    ) -> PyResult<Bound<'py, PyBytes>> {
        let input = py
            .get_type::<PyBytes>()
            .call1((data,))?
            .cast_into::<PyBytes>()?
            .as_bytes()
            .to_vec();
        let flags = packet_flags(flags)?;

        // The owned input and Rust-only dispatcher are safe to move across the
        // GIL boundary. PyO3 keeps this method's exclusive pyclass borrow held,
        // so another call cannot concurrently mutate the connection state.
        let output = py
            .detach(move || self.inner.decompress(&input, flags, expected_size))
            .map_err(decode_error)?;
        Ok(PyBytes::new(py, &output))
    }

    #[getter]
    fn max_compression_type(&self) -> u8 {
        self.inner.max_compression_type()
    }

    #[getter]
    fn selected_type(&self) -> Option<u8> {
        self.inner.selected_type()
    }

    #[getter]
    fn packet_count(&self) -> usize {
        self.inner.packet_count()
    }

    #[getter]
    fn compressed_packet_count(&self) -> usize {
        self.inner.compressed_packet_count()
    }

    #[getter]
    fn compressed_byte_count(&self) -> usize {
        self.inner.compressed_byte_count()
    }

    #[getter]
    fn decompressed_byte_count(&self) -> usize {
        self.inner.decompressed_byte_count()
    }

    #[getter]
    fn history_offset(&self) -> Option<usize> {
        self.inner.history_offset()
    }

    #[getter]
    fn history_size(&self) -> Option<usize> {
        self.inner.history_size()
    }

    #[getter]
    fn offset_cache_len(&self) -> Option<usize> {
        self.inner.offset_cache_len()
    }

    #[getter]
    fn level2_history_offset(&self) -> Option<usize> {
        self.inner.level2_history_offset()
    }
}

#[pymodule]
fn _bulk(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add(
        "BulkCompressionError",
        module.py().get_type::<BulkCompressionError>(),
    )?;
    module.add_class::<NativeBulkDecompressor>()?;
    Ok(())
}
