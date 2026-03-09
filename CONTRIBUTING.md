# Contributing to SVTD

Thank you for your interest in contributing to SVTD (Surgical Vector Trust Decay)! This document provides guidelines for contributing to the project.

---

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/your-username/svtd.git
cd svtd
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests to verify setup
pytest tests/ -v
```

---

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_trust_engine.py -v

# Run with coverage
pytest tests/ --cov=svtd --cov-report=html
```

### Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings to all public functions and classes
- Keep functions focused and modular

### Pre-commit Checks

Before submitting a PR:

```bash
# Run tests
pytest tests/ -v

# Check code style (if using black/flake8)
black svtd/ tests/
flake8 svtd/ tests/
```

---

## Types of Contributions

### 🐛 Bug Reports

When reporting bugs, please include:

- **Description:** Clear description of the bug
- **Reproduction:** Steps to reproduce
- **Expected behavior:** What you expected to happen
- **Actual behavior:** What actually happened
- **Environment:** Python version, OS, SVTD version
- **Code example:** Minimal code that reproduces the issue

### 💡 Feature Requests

We welcome feature requests! Please:

- Describe the use case clearly
- Explain why current functionality doesn't suffice
- Provide examples of how the feature would work

### 🔧 Pull Requests

1. **Branch naming:**
   - `feature/description` for new features
   - `fix/description` for bug fixes
   - `docs/description` for documentation updates

2. **Commit messages:**
   - Use clear, descriptive commit messages
   - Reference issues when applicable: "Fix #123: Correct decay calculation"

3. **PR description should include:**
   - What changes were made
   - Why the changes were needed
   - Testing performed
   - Any breaking changes

### 📚 Documentation

Documentation improvements are always welcome:

- Fix typos or unclear explanations
- Add examples for complex features
- Improve API documentation
- Add tutorials or use cases

---

## Project Structure

```
svtd/
├── svtd/              # Core package
├── tests/             # Test suite
├── examples/          # Usage examples
├── demos/             # Demo applications
├── docs/              # Documentation
└── README.md          # Main readme
```

---

## Core Principles

When contributing, keep these principles in mind:

1. **Zero Friction:** SVTD should never require explicit user action for basic functionality
2. **Privacy First:** Support opaque handles and privacy modes
3. **Backwards Compatibility:** Avoid breaking changes without deprecation warnings
4. **Simplicity:** Prefer simple solutions over complex ones
5. **Enterprise Ready:** Code should be production-quality

---

## Questions?

- 🌐 [MemoryGate.io](https://memorygate.io) - Learn more about SVTD and the managed enterprise version
- For bug reports and feature requests, please open an issue on this repository

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism gracefully
- Focus on what's best for the community

### Unacceptable Behavior

- Trolling, insulting comments, or personal attacks
- Public or private harassment
- Publishing others' private information without permission

---

## Recognition

Contributors will be recognized in our README and release notes. Thank you for helping make SVTD better!

---

*Built with 💙 by the Goldfish Team @ NovaCore and contributors like you.*
