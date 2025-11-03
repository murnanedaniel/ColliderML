# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [0.4.2] - 2025-09-17

### Added
- [dataset] Added public S3 mirrors for Run-3 samples with resume support.
- [library] New `colliderml get` option `--verify-checksums` for end-to-end integrity.

### Changed
- [dataset] Updated detector geometry to v3.2 for calorimeter segmentation.

### Fixed
- [library] Resolved Windows path handling in CLI subcommands.

## [0.4.1] - 2025-08-30

### Added
- [dataset] Released "taster" dataset with 1k events per class and example notebooks.
- [library] Added download progress bars and ETA to the CLI.

### Deprecated
- [dataset] Deprecated legacy download endpoint; use the regional endpoints instead.

## [0.4.0] - 2025-08-12

### Added
- [dataset] Introduced per-object reconstruction labels (tracks, clusters, jets) in parquet.
- [library] Added `DataConfig` schema validation with helpful error messages.

### Changed
- [dataset] Standardized units to GeV and mm across all tables.

## [0.3.3] - 2025-07-22

### Fixed
- [dataset] Corrected jet energy scale for high-η region (v2.9 → v3.0).
- [library] Fixed retry logic edge case when resuming partial downloads.

## [0.3.2] - 2025-07-05

### Added
- [dataset] Published validation splits for electron/photon samples.
- [library] Added `colliderml taster --notebooks` convenience flag.

## [0.3.0] - 2025-06-14

### Added
- [dataset] First public release of Run-3 simulated samples with full detector response.
- [library] Initial release of `colliderml` CLI and Python API.

### Security
- [library] Pinned transitive dependencies to address CVE advisories.

---

Unreleased changes should be added under a `## [Unreleased]` header above with entries marked as `[dataset]` or `[library]`.


