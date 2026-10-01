# Disposable RDP and VNC interoperability labs

This tree holds opt-in live tests and pinned Docker targets. No container,
profile, port, or credential is required for collection or for the default
offline suite.

## Reproducible targets

Both labs pin:

- `debian:12.11-slim` by digest
  `sha256:b1a741487078b369e78119849663d7f1a5341ef2768798f7b7406c4240f86aef`
- APT snapshot `20250811T000000Z`

xrdp is pinned to Debian `0.9.21.1-1` with `xorgxrdp` `0.9.19-1`. TigerVNC is
pinned to `tigervnc-standalone-server` `1.12.0+dfsg-8`. Compose maps the
services to host ports `13389` and `15900`.

xrdp runs with `security_layer=rdp` (NLA off). CredSSP/NLA is not the default;
a later `--capability nla` can be added if a target supports it.

## Test-only credentials

Committed defaults are intentionally non-secret and must never be reused:

- username: `aardwolftest`
- password: `Aardwolf-Test-Only-1!`

Override client and container together with `AARDWOLF_XRDP_*` / `AARDWOLF_VNC_*`
environment variables. Credential values are not printed by the runner or
included in assertion messages. Local overrides belong in ignored
`profile.local.yml` files; point `AARDWOLF_XRDP_PROFILE` or
`AARDWOLF_VNC_PROFILE` at them.

## Run the managed labs

From the repository root:

```console
./run-tests.sh lab
./run-tests.sh xrdp
./run-tests.sh vnc
```

Each runner builds the image, waits for Compose health, runs the marked suite,
and tears the project down with volumes and orphans removed. Extra pytest
arguments are accepted.

Infrastructure failures (Docker down, closed port, missing profile) skip. Only
lab-confirmed client bugs become `KF-07xx` xfails.
