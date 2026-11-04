# Client Info PDU never sets INFO_AUTOLOGON

Status: implemented, not committed (noted 2026-11-04)

## Summary

aardwolf sends the username, domain and password in the Client Info PDU
(`TS_INFO_PACKET`, built in `RDPConnection.__send_userdata` in
`aardwolf/connection.py`), but never set `INFO_FLAG.AUTOLOGON` (0x8).

Without that flag the server does not use the password from the Client Info
PDU. Over TLS-only (`SSL`) and Standard RDP Security (`RDP`) connections,
that PDU is the only place credentials are sent, so aardwolf never signed in
on those connection types. It connected, rendered the server's sign-in screen
and reported success.

NLA (`HYBRID` / `HYBRID_EX`) connections are not affected: the server signs
the user in with the credentials from the NLA (CredSSP) exchange, and the
Client Info PDU carries no password.

## What was implemented

- `RDPTarget.autologon` (default `True`, URL `?autologon=0`): set
  `INFO_FLAG.AUTOLOGON` whenever a password is placed in the Client Info PDU.
- `RDPTarget.autologon_confirm` (default `True`, URL `?autologon_confirm=0`):
  after an autologon, `connect()` waits up to
  `RDPConnection.autologon_timeout` (15 s) for the server's verdict:
  - Save Session Info with Logon Info, or Logon Info Extended without errors:
    signed in.
  - Logon errors reporting session contention (`BUMP_OPTIONS`,
    `SESSION_BUSY_OPTIONS`, `RECONNECT_OPTIONS`): the credentials were
    accepted, `connect()` succeeds and the notification is on
    `logon_info_queue` as before.
  - `SESSION_CONTINUE`: keep waiting.
  - Any other logon error, a non-zero Set Error Info, a closed connection, or
    nothing within the timeout: `connect()` fails with `AutologonError`
    (`aardwolf/connection.py`; `.notification` holds the Save Session Info PDU
    when there was one).
- Every parsed Save Session Info PDU is also kept in
  `RDPConnection.logon_notifications`.
- The xrdp interop tests connect with `autologon_confirm=0`.
- Tests: `tests/unit/protocol/t128/test_autologon.py`.

## Server behaviour

Windows (lab host, `NORTH\hodor`, TLS-only):

| Case | What the server did |
|---|---|
| no AUTOLOGON | sign-in screen, username pre-filled, no password; no Save Session Info |
| AUTOLOGON, correct password | Save Session Info about 3 s after the connection sequence (here Logon Errors `BUMP_OPTIONS`, because the host's two sessions were in use) |
| AUTOLOGON, wrong password | "The user name or password is incorrect" on the sign-in screen, **nothing sent to the client**; after about 33 s Set Error Info `LOGOFF_BY_USER` and disconnect |

So a wrong password can only be detected by the missing confirmation, hence
the timeout.

xrdp 0.9.21 (interop lab, Xorg session): AUTOLOGON signs the user in
("login successful" in the xrdp log), but xrdp never sends Save Session Info.
Its source only relays that PDU from the neutrinordp proxy module, so Xorg and
VNC sessions give no confirmation. Use `autologon_confirm=0` for such servers.

## Side effects

AUTOLOGON turns a password that used to be ignored into a real sign-in on
TLS-only and Standard RDP Security connections. That matches what NLA already
does:

- A wrong password counts as a failed sign-in towards account lockout.
- A successful sign-in creates a session, and can disconnect or compete with
  existing sessions (session arbitration, "too many users" prompts).

Differences from NLA:

- Where failures happen: over NLA a wrong password fails during the CredSSP
  exchange, before any session exists. Over AUTOLOGON it fails at the sign-in
  screen inside an existing session.
- Windows security log: NLA failures are logged as network logons (logon
  type 3), AUTOLOGON failures as remote-interactive logons (logon type 10).
- `connect()` takes about 3 s longer on Windows with AUTOLOGON, and 15 s to
  report a wrong password.

## Still open

- The first sign-in of a user (profile creation) was not measured; if the
  confirmation can take longer than 15 s there, raise `autologon_timeout`.
- Plain `HYBRID` connections that the server drops right after NLA (user not
  allowed to sign in) still only report "Connection closed!".
- In the xrdp lab, the Xorg session sends no screen updates and xrdp drops the
  connection after about 16 s, right after logging that it cannot reach
  `chansrv`. `test_xrdp_screenshot_buffer` therefore still skips. Not
  investigated.
