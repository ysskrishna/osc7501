# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2]

### Changed

- GitHub releases no longer attach the wheel, the sdist, or the attestation files. Install from PyPI. GitHub still attaches the source zip and tar.gz for the tag
- The README opener no longer mentions osc-status. The credit stays in the acknowledgments
- The probe is described as asking whether the terminal supports OSC 7501
- The job example states that `working()` writes before the `with` block
- Terminal names are no longer listed. The README links to the awesome-osc7501 matrix and notes that this library does not wrap reports for tmux

## [1.0.1]

### Fixed

- A `Job` write that raises no longer counts as sent, so a retry still sends and a `with` block still writes its exit report
- `detect()` no longer raises when a support reply contains a non-ASCII byte. The result stays supported, and the default states and kinds are used

## [1.0.0]

### Added

- `encode()` builds one OSC 7501 revision 0.4 report
- `idle()`, `working()`, `done()`, `blocked()`, `error()`, and `clear()` write that report to a terminal
- `working()` returns a `Job` that repeats `app`, `id`, and `title`, skips a repeated report, and writes `done`, `error`, or `idle` when a `with` block ends
- `detect()`, `query()`, and `parse_reply()` ask whether the terminal supports the protocol
- Control characters in `msg` and `title` are replaced before base64 encoding
- Zero runtime dependencies
- Python 3.11+

[1.0.2]: https://github.com/ysskrishna/osc7501/releases/tag/v1.0.2
[1.0.1]: https://github.com/ysskrishna/osc7501/releases/tag/v1.0.1
[1.0.0]: https://github.com/ysskrishna/osc7501/releases/tag/v1.0.0
