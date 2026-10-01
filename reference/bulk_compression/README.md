# RDP bulk-compression Python reference

This directory preserves a complete, educational Python reference
implementation of RDP bulk decompression. It is intended for studying the
wire formats, validating test vectors, and comparing other implementations
against clear Python code.

The reference package is deliberately independent from Aardwolf's production
compression package. Production code must not import it, and it is not a
runtime fallback for production codecs.

The implementation is derived only from these normative specifications:

- [MS-RDPBCGR]
- [MS-RDPEGDI]
- RFC 2118

Run the preserved reference tests from the repository root with:

```console
python -m unittest reference.bulk_compression.tests.test_reference
```
