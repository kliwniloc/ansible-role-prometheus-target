# Changelog

## [1.3.0] - 2026-02-09

### Added: yaml strategy

- Support for `yaml` strategy to read multiple targets per file (commit `049689c`).

### Documentation

- `README.md`: make Troubleshooting section more parsable (commit `7c09cd3`).

## [1.2.0] - 2023-10-11

### Added: run_once option

- Add `run_once` option for command and shell handlers.

### Changed

- Handlers now use Ansible tasks instead of handlers to allow `run_once`
  option to work properly.

## [1.1.0] - 2023-06-15

### Added: prefix option

- Prefix option for target files (`579b168`).
- Ability to define exporters without id (`232bdca`).
