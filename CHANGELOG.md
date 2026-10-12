# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0]

### Added

- `encode()` builds one OSC 7501 revision 0.4 report
- `idle()`, `working()`, `done()`, `blocked()`, `error()`, and `clear()` write that report to a terminal
- `working()` returns a `Job` that repeats `app`, `id`, and `title`, skips a repeated report, and writes `done`, `error`, or `idle` when a `with` block ends
- `detect()`, `query()`, and `parse_reply()` ask whether the terminal supports the protocol
- Control characters in `msg` and `title` are replaced before base64 encoding
- Zero runtime dependencies
- Python 3.11+

[1.0.0]: https://github.com/ysskrishna/osc7501/releases/tag/v1.0.0
