# OSC 7501


[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/ysskrishna/osc7501/blob/main/LICENSE)
![Tests](https://github.com/ysskrishna/osc7501/actions/workflows/test.yml/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/osc7501)](https://pypi.org/project/osc7501/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/osc7501?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/osc7501)

Report terminal program status with OSC 7501.

## Features

- **States**: `idle`, `working`, `done`, `blocked`, `error`, and `clear`
- **One job**: a context manager that repeats `app`, `id`, and `title` and closes the job for you
- **Safe text**: control characters become spaces before base64, so one newline cannot drop the report
- **Optional probe**: ask the terminal whether it supports OSC 7501
- **Zero dependencies**: the library only uses the Python standard library
- **TTY gate**: reports are skipped when stderr is a pipe, unless you pass `enabled=True`

## Why OSC 7501?

OSC 9;4 progress can say that a program is busy, at a percentage, or failed. It has no message and no way to say the program is waiting on the user. A window title is one free-form string.

OSC 7501 adds a state, a reason (`permission`, `question`, or `auth`), and a stable `app` name. The terminal decides how to show that. A terminal that does not know the sequence ignores it, so sending a report is safe.

Spec: [Program Status Protocol, revision 0.4](https://control-codes.page/proposals/osc-7501/) (2026-10-10).

## Installation

```bash
pip install osc7501
```

## Usage Examples

### Helpers

```python
from osc7501 import blocked, done, working

working(progress=40, msg="Building docs")
blocked(kind="permission", msg="Approve deploy?")
done(msg="Docs built")
```

Each report replaces the terminal's record. Repeat every field you still want. `clear()` with no `id` removes every record in the terminal.

Reports go to stderr, and only when it is a terminal.

### One job

```python
from osc7501 import working

with working(app="make", msg="Building docs") as job:
    job.blocked(kind="question", msg="Overwrite config.toml?")
    job.done(msg="Docs built")
```

`working()` writes `working` when you call it, before the `with` block. Enter writes nothing more. A clean exit writes `done` with no message. An exception writes `error`. `KeyboardInterrupt` writes `idle`. If you already called `job.done()` or `job.error()`, the exit writes nothing.

`msg` for `kind="auth"` is the prompt, never the secret.

### Detection

```python
from osc7501 import detect

print(detect().result)
```

Call `detect()` before reading input. It can consume keystrokes typed during the wait. On Windows, or when `/dev/tty` cannot be opened, the result is `Detection.UNKNOWN`. Helpers never probe on their own.

## Where reports show up

Which terminals show a report is tracked in the [awesome-osc7501 matrix](https://github.com/hyeebeen/awesome-osc7501). This library does not wrap reports for tmux.

## API Reference

| Name | Description |
|------|-------------|
| `encode(state, *, msg, title, app, id, kind, progress) -> str` | Build one sequence. Does not write. |
| `working(*, msg, title, app, id, progress, stream, enabled) -> Job` | Write `working` and return a `Job`. |
| `Job.update(*, progress, msg) -> bool` | Write another `working` report. Skips a byte-identical repeat. |
| `Job.blocked(*, kind, msg, progress) -> bool` | Write `blocked`, repeating `app`, `id`, and `title`. |
| `Job.done(*, msg) -> bool` / `Job.error` / `Job.idle` | Write that state. |
| `idle`, `done`, `error`, `blocked`, `clear` | Write one report. Return `True` only when bytes were written. |
| `query() -> str` | The `OSC 7501 ; ? ST` query. |
| `parse_reply(sequence) -> Support \| None` | Parse one reply. Missing lists mean the five states and three kinds. |
| `detect(*, timeout=0.2) -> Support` | Probe `/dev/tty`. `Support.supported` is true only for `Detection.SUPPORTED`. |
| `State`, `Kind` | `StrEnum` values. Plain strings are accepted too. |

## Learn More

- [Program Status Protocol (OSC 7501)](https://control-codes.page/proposals/osc-7501/)
- [Mitchell Hashimoto: A Terminal Protocol for Program Status](https://mitchellh.com/writing/program-status-osc7501)
- [awesome-osc7501](https://github.com/hyeebeen/awesome-osc7501)

## Acknowledgments

- [Mitchell Hashimoto](https://github.com/mitchellh), for the specification
- [Jonah Snider](https://github.com/jonahsnider), for [osc-status](https://github.com/jonahsnider/osc-status)
- [Adam Duke](https://github.com/adamvduke), for [pst](https://github.com/adamvduke/pst)

## Built and maintained by

osc7501 is built and maintained by:

| | Name | GitHub | Role |
|---|------|--------|------|
| <img src="https://github.com/ysskrishna.png?size=120" width="60" height="60" alt="Y. Siva Sai Krishna"> | **Y. Siva Sai Krishna** | [@ysskrishna](https://github.com/ysskrishna) | Creator |

## Changelog

See [CHANGELOG.md](https://github.com/ysskrishna/osc7501/blob/main/CHANGELOG.md) for a detailed list of changes and version history.

## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/ysskrishna/osc7501/blob/main/CONTRIBUTING.md) for details.

## Support

If you find this library helpful:

- ⭐ Star the repository
- 🐛 Report issues
- 🔀 Submit pull requests
- 💝 [Sponsor on GitHub](https://github.com/sponsors/ysskrishna)

## License

MIT © [Y. Siva Sai Krishna](https://github.com/ysskrishna) - see [LICENSE](https://github.com/ysskrishna/osc7501/blob/main/LICENSE) file for details.

---

<p align="left">
  <a href="https://github.com/ysskrishna">Author's GitHub</a> •
  <a href="https://linkedin.com/in/ysskrishna">Author's LinkedIn</a> •
  <a href="https://github.com/ysskrishna/osc7501/issues">Report Issues</a> •
  <a href="https://pypi.org/project/osc7501/">Package on PyPI</a>
</p>
