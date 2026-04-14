# Changelog

All notable changes to this repository are documented in this file.

## 2026-04-14

### Added
- Added `vastai/references/python-setup.md` with guidance for setting up remote Python environments on Vast.ai instances using `uv`, including CUDA-aware PyTorch installation, verification steps, and common pitfalls.
- Added the `research-report` skill with report templates, plot manifest tooling, report version tracking, artifact validation helpers, and reusable plot templates for research and experiment reporting.

### Changed
- Expanded the Vast.ai skill guide with a dedicated Python setup section and linked the new remote setup reference from the main skill document.
- Updated the Vast.ai skill title and introduction to match the upstream skill source.
- Updated the repository README to include the new `research-report` skill in the index, usage guidance, and directory structure.

## 2026-04-13

### Added
- Added the initial skills collection repository structure and normalized skill layout across included skills.
- Added `.gitignore` entries to reduce the risk of committing local secrets and generated artifacts.
- Added a repository-level `README.md` describing the collection and its included skills.
- Added a skill index table to the README for faster skill discovery.

### Changed
- Restricted the Dropbox skill credential path handling.
- Polished and refined the repository README for clearer usage guidance and structure.
