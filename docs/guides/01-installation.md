# Guides: Installation

## Requirements

- Python 3.10+
- No external dependencies (stdlib only)

## Installing

### From PyPI (recommended)

```bash
pip install catpile
```

### From source

```bash
git clone https://github.com/swirx/catpile.git
cd catpile
pip install -e .
```

### Verify

```bash
cpile --help
python3 -m catpile.cli --help
```

## Optional Dependencies

- **gunicorn** - for production web server (`pip install gunicorn`)
- **requests** - for schema auto-fetching (stdlib `urllib` used as fallback)

## Development Setup

```bash
# Clone
git clone <repo-url>
cd catpile

# Install in editable mode
pip install -e .

# Run tests
python3 tests/test_all.py
python3 tests/test_optimizer.py

# Compile examples
python3 -m catpile.cli examples/basic.cat

# Start web server
python3 -m catpile.web
```

## Testing

```bash
# All tests
python3 -m pytest tests/

# Specific test
python3 -m pytest tests/test_all.py -k test_dict_literal

# Optimizer tests
python3 tests/test_optimizer.py

# Test roundtrip (compile → decompile → recompile)
python3 tests/test_roundtrip.py
```

## Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8788
CMD ["gunicorn", "catpile.web:app", "-b", "0.0.0.0:8788"]
```
