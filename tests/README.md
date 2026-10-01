# aardwolf test suite

Do not set up a venv or Docker lab by hand. From the repository root:

```bash
./run-tests.sh              # offline baseline
./run-tests.sh full         # baseline plus disposable xrdp and VNC labs
./run-tests.sh --help
```

The runner creates `.venv-test` if needed, installs the package and test
deps, runs the named profile, and always stops leftover lab containers.
`./run-tests.sh --ephemeral` deletes the venv on exit; `./run-tests.sh clean`
removes `.venv-test` and stops labs.

The leftover `aardwolf-0.2.15/` source snapshot is not collected
(`testpaths = ["tests"]`).

The configured `pytest-randomly` seed is fixed so ordering and per-test random
state are reproducible. Pass another `--randomly-seed` after `--` to reproduce
a reported seed. Asyncio runs in strict mode, and the default per-test timeout
is 30 seconds.

```bash
./run-tests.sh unit --cov
./run-tests.sh xrdp -- -k login -vv
```

## Layout

- `unit/`: deterministic tests with no network access.
- `fake_peer/`: async connection tests against scripted in-process peers.
- `component/`: tests spanning multiple repository components.
- `interop/xrdp/`: explicitly configured xrdp interoperability.
- `interop/vnc/`: explicitly configured VNC interoperability.
- `support/`: reusable test-only helpers.
- `known_failures.yml`: confirmed production defects and blocker links.

## Marker and safety policy

Every test uses one primary scope marker: `unit`, `fake_peer`, `component`,
`xrdp`, or `vnc`. Add `slow`, `destructive`, `privileged`, `quarantine`,
and `capability("name")` as applicable.

xrdp, VNC, slow, destructive, privileged, and quarantine tests are skipped
unless their matching `--run-*` option is supplied. Capabilities are declared
with repeatable `--capability NAME` options. A test carrying multiple gates
must satisfy every gate. Never use an opt-in as a substitute for a disposable
target, least-privilege credentials, or a cleanup plan.

The default suite requires no xrdp or VNC infrastructure. Local target
profiles must use the ignored `profile.local.yml` locations documented under
`interop/`.

## Results and production defects

- Pass tests for supported behavior.
- Use strict `xfail` for one minimal reproducer of a confirmed production
  defect or planned feature, and reference its stable known-failure ID.
- Skip only when the platform, lab, credential tier, or capability is absent.
- Quarantine unsafe, flaky, or not-yet-classified cases.

Do not fix production code while developing this suite. Add or update
`known_failures.yml` with sanitized evidence, then request a separate
production-fix review.

## Live labs

```bash
./run-tests.sh lab
./run-tests.sh xrdp
./run-tests.sh vnc
./run-tests.sh destructive
```

Each lab profile builds a disposable container, waits for health, runs the
marked suite, and tears the project down even if the tests fail or you hit
Ctrl-C. Extra pytest arguments are accepted after `--`.


