# FreeRDP reports two malformed client PDUs

Status: open, low priority; connections work (noted 2026-11-04)

## Summary

The FreeRDP 3.32.1 shadow server (`freerdp-shadow-cli3`) logs two errors for
aardwolf's traffic. Neither one stops the session: aardwolf connects over NLA,
receives screen updates (9,600 in a 3-second probe) and only the final
disconnect is affected. Both are real encoding bugs in aardwolf.

## 1. Bitmap Cache capability set is 30 bytes too long

FreeRDP log:

```
[rdp_read_capability_set]: incorrect offset, type:0x0004 actual:36 expected:66
```

FreeRDP read the 36-byte body of the Bitmap Cache capability set
(`CAPSTYPE_BITMAPCACHE`, MS-RDPBCGR 2.2.7.1.4.1: 24 bytes of padding plus six
2-byte fields), but the capability set's length field says the body is 66
bytes.

Cause: `TS_BITMAPCACHE_CAPABILITYSET.to_bytes` in
`aardwolf/protocol/pdu/capabilities/bitmapcache.py` writes
`Cache2MaximumCellSize` with `to_bytes(32, ...)` instead of `to_bytes(2, ...)`.

`from_buffer` in the same class also has a bug: it never reads
`Cache1MaximumCellSize`, so `Cache2Entries` and `Cache2MaximumCellSize` get the
wrong values when parsing.

## 2. Shutdown Request PDU has 4 extra bytes

FreeRDP log:

```
[peer_recv_tpkt_pdu] Received invalid TPKT header length 22, 4 bytes too long!
```

followed by `STATE_RUN_FAILED` and the shadow client thread exiting. It
appears when aardwolf disconnects.

Cause: `RDPConnection.send_disconnect` in `aardwolf/connection.py` wraps
`TS_SHUTDOWN_REQ_PDU` in a `TS_INPUT_PDU_DATA`, whose `to_bytes` adds
`numEvents` (2 bytes) and `pad2Octets` (2 bytes) before the (empty) shutdown
body. Per MS-RDPBCGR 2.2.2.2.1 the Shutdown Request PDU is only the share
data header (18 bytes); aardwolf sends 22.

Consequence: FreeRDP drops the connection instead of answering with Shutdown
Denied, so `send_disconnect` reads a closed connection rather than the
server's reply. Connections to Windows, xrdp and IronRDP worked, but I did
not check how those servers handle the oversized shutdown request.

## Fix sketch

- `bitmapcache.py`: write `Cache2MaximumCellSize` as 2 bytes, read
  `Cache1MaximumCellSize` in `from_buffer`, and add a round-trip test that
  checks the body is 36 bytes.
- `send_disconnect`: send the share data header with an empty body instead of
  wrapping the shutdown request in `TS_INPUT_PDU_DATA`, and add a test for the
  18-byte PDU.
- Re-test against FreeRDP shadow, Windows, xrdp and IronRDP.

## Reproduction

FreeRDP shadow server in Docker (Ubuntu 24.04, `freerdp3-shadow-x11`, Xvfb),
started with `freerdp-shadow-cli3 /port:3389 /sec:nla /sam-file:/tmp/sam`.
Connect with aardwolf over NLA, wait a few seconds and disconnect. Both
errors appear in the container log.
