# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2025-12-10

### Fixed

- CI: Use `--package` flag for workspace builds to output to correct dist directories
- CI: Correct glob pattern for collecting package distributions
- Resolve lint errors (unused imports) across multiple packages
- Improve type safety in QR parser with proper `Optional[str]` annotations
- Fix PIL.Image import for correct type checking

## [2.0.0] - 2025-12-09

### Added

- CLI tool with `thanakan qr`, `thanakan statement`, `thanakan mail`, and `thanakan accounting` commands
- Pipe-friendly design: auto-detect stdin type (image/text), compact JSON output when piped
- Verbose mode (`-v`) for detailed output and next steps guidance
- **thanakan-statement**: Parse Thai bank PDF statements (KBank, BBL) with bilingual support
- **thanakan-mail**: Download bank statements from Gmail with OAuth2 authentication
- **thanakan-accounting**: Export to Peak accounting format with TUI account selection
- PyPI publishing with Sigstore attestations
- Ko-fi support link and GitHub funding

### Changed

- Redesigned README with Thai-primary content
- Deferred zbar import to qr command for faster CLI startup

## [1.0.0] - Initial Release

### Added

- **thanakan-qr**: Parse Thai bank slip mini QR codes (SCB specification)
- **thanakan-oauth**: OAuth API clients for SCB and KBank slip verification
