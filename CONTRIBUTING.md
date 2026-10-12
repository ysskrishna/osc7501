# Contributing to osc7501

Thank you for your interest in contributing to `osc7501`! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv)

### Setting Up the Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ysskrishna/osc7501.git
   cd osc7501
   ```

2. **Install dependencies**:
   ```bash
   uv sync --locked --dev
   ```

3. **Verify the setup**:
   ```bash
   uv run pytest
   ```

## Development Workflow

### Running Tests

Run the test suite to ensure everything works:

```bash
uv run pytest
```

Run a specific test file:

```bash
uv run pytest tests/test_encode.py
```

### Code Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use type hints for all function parameters and return values
- Keep functions simple and focused
- Add docstrings to all public functions

### Changing a report

The byte format lives in `osc7501/encode.py`. Writing and `detect()` live in `osc7501/terminal.py`.

1. Add a failing test in `tests/` for the sequence or the error
2. Change the encoder or the writer
3. Run `uv run pytest`
4. Open a pull request into `main`

Do not probe the terminal from an emit path. `detect()` is opt-in because it reads input.

## Submitting Changes

### Pull Request Process

1. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-fix-name
   ```

2. **Make your changes**:
   - Write your code
   - Add tests for new functionality
   - Ensure all tests pass
   - Update documentation if needed

3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

   Use clear, descriptive commit messages. Follow the format:
   - `feat: add new feature`
   - `fix: fix bug description`
   - `docs: update documentation`
   - `test: add tests for feature`
   - `refactor: improve code structure`

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** into `main`:
   - Go to the repository on GitHub
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR description with:
     - Description of changes
     - Related issues (if any)
     - Testing instructions

### Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Ensure all tests pass
- Update documentation if you're adding new features
- Write clear commit messages
- Reference any related issues

## Reporting Issues

When reporting issues, please include:

- Python version
- Package version
- Operating system and version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Any relevant error messages or stack traces

## Code of Conduct

- Be respectful and considerate
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Be open to feedback and suggestions

## Questions?

If you have questions about contributing, feel free to:

- Open an issue on GitHub
- Check existing issues and discussions

Thank you for contributing to `osc7501`!
