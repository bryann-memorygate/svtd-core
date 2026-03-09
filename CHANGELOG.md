# Changelog

All notable changes to SVTD will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Initial open-source release
- Comprehensive test suite with pytest
- Examples for LangChain and LlamaIndex integration
- Documentation for architecture and value proposition
- CONTRIBUTING.md and CHANGELOG.md

---

## [0.1.0] - 2026-03-08

### Added
- **Core Trust Engine:**
  - `apply_decay()` - Multiplicative trust decay (×0.01)
  - `calculate_trust_weight()` - Trust-weighted relevance scoring
  - `GHOST_STATE_THRESHOLD` constant (0.1)
  - `DEFAULT_TRUST_WEIGHT` constant (1.0)
  - `DECAY_FACTOR` constant (0.01)

- **Trust Ledger:**
  - SQLite-based persistence for trust weights
  - Client isolation (multi-tenant support at data layer)
  - Feedback count tracking
  - Cold memory detection (trust < 0.2)
  - Audit trail with timestamps

- **Correction Handler:**
  - `flag_memory_as_correction()` - Apply decay to memories
  - Support for explicit corrections
  - Configurable decay factors
  - Correction reason tracking

- **Integration Functions:**
  - `rerank_results()` - Apply trust weighting and sort
  - `multiply_relevance_by_trust()` - Multiply scores in place
  - Ghost state marking
  - Backwards-compatible with vanilla RAG

- **Demos:**
  - Law demo (FLSA salary threshold example)
  - Shows before/after comparison
  - Real-world legal use case

- **Documentation:**
  - README with quickstart guide
  - Apache 2.0 license with patent grant
  - MemoryGate.io integration notes

---

## Roadmap

### [0.2.0] - Planned

- Time-based decay (gradual trust reduction over time)
- Rehabilitation tracking (positive feedback)
- More vector DB integration examples
- Performance benchmarks

### [0.3.0] - Planned

- Batch correction operations
- Trust weight analytics and reporting
- REST API wrapper
- Docker support

### [1.0.0] - Planned

- Stable API guarantee
- Comprehensive documentation
- Production deployment guides
- Enterprise integration patterns

---

## Contributing Changes

When submitting changes, please add a note to the [Unreleased] section describing:

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for removed features
- **Fixed** for bug fixes
- **Security** for security fixes

---

*For more information about SVTD, visit [memorygate.io](https://memorygate.io)*
