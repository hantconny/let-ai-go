# Quickstart: 订阅解析器 (Subscription Parser)

**Feature**: 001-subscription-parser
**Date**: 2026-03-05
**Purpose**: Quick start guide for developers implementing the subscription parser

## Prerequisites

- Python 3.12 or higher
- Redis 5.0 or higher (running and accessible)
- Basic understanding of proxy protocols (ss, vmess, etc.)

## Installation

```bash
# Clone repository
git clone <repository-url>
cd let-ai-go

# Checkout feature branch
git checkout 001-subscription-parser

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

```
src/
├── parsers/              # Protocol-specific parsers
├── decoders/            # Format detection and decoding
├── storage/             # Redis and file export
├── models/              # Data models
├── utils/               # Utilities (hashing, logging)
└── cli/                 # CLI interface

tests/
├── unit/                # Unit tests
├── integration/         # Integration tests
└── fixtures/            # Test data
```

## Quick Start (5 minutes)

### 1. Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:5.0

# Or use existing Redis instance
redis-cli ping  # Should return PONG
```

### 2. Parse a Sample File

```bash
# Parse single subscription file
python -m src.cli.main parse tests/fixtures/sample_base64.txt

# Expected output:
# Parsing: tests/fixtures/sample_base64.txt
# Format detected: base64
# Nodes found: 10
# Successfully parsed: 10
# Failed: 0
# Duration: 0.15s
#
# Stored in Redis: subscription:sample_base64
# Exported to: ./output/sample_base64.json
# Exported to: ./output/sample_base64.csv
```

### 3. Verify Results

```bash
# Check Redis
redis-cli SMEMBERS subscription:sample_base64:nodes

# Check exported files
cat output/sample_base64.json
cat output/sample_base64.csv
```

## Development Workflow

### 1. Implement a Protocol Parser

Create a new parser in `src/parsers/`:

```python
# src/parsers/ss.py
from src.parsers.base import BaseParser
from src.models.node import Node
import base64
from urllib.parse import urlparse

class ShadowsocksParser(BaseParser):
    """Parser for Shadowsocks (ss://) URIs"""

    def parse(self, uri: str) -> Node:
        """
        Parse ss:// URI format:
        ss://base64(cipher:password)@host:port#remarks
        """
        if not uri.startswith('ss://'):
            raise ValueError(f"Invalid ss URI: {uri}")

        # Remove ss:// prefix
        uri_body = uri[5:]

        # Split remarks if present
        if '#' in uri_body:
            uri_body, remarks = uri_body.split('#', 1)
        else:
            remarks = None

        # Parse user info and server
        if '@' not in uri_body:
            raise ValueError("Missing @ separator in ss URI")

        user_info, server = uri_body.split('@', 1)

        # Decode base64 user info
        try:
            decoded = base64.b64decode(user_info).decode('utf-8')
            cipher, password = decoded.split(':', 1)
        except Exception as e:
            raise ValueError(f"Failed to decode ss user info: {e}")

        # Parse server (host:port)
        if ':' not in server:
            raise ValueError("Missing port in ss URI")

        host, port = server.rsplit(':', 1)

        # Create Node object
        return Node(
            protocol='ss',
            host=host,
            port=int(port),
            password=password,
            cipher=cipher,
            remarks=remarks
        )
```

### 2. Add Tests

Create tests in `tests/unit/`:

```python
# tests/unit/test_ss_parser.py
import pytest
from src.parsers.ss import ShadowsocksParser

def test_parse_valid_ss_uri():
    parser = ShadowsocksParser()
    uri = "ss://YWVzLTI1Ni1nY206cGFzc3dvcmQ=@example.com:8388#Test"
    # base64 decodes to: aes-256-gcm:password

    node = parser.parse(uri)

    assert node.protocol == 'ss'
    assert node.host == 'example.com'
    assert node.port == 8388
    assert node.cipher == 'aes-256-gcm'
    assert node.password == 'password'
    assert node.remarks == 'Test'

def test_parse_invalid_ss_uri():
    parser = ShadowsocksParser()

    with pytest.raises(ValueError):
        parser.parse("vmess://invalid")

    with pytest.raises(ValueError):
        parser.parse("ss://invalid_base64@host:port")
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_ss_parser.py

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### 4. Test Integration

```bash
# Create test subscription file
echo "ss://YWVzLTI1Ni1nY206cGFzc3dvcmQ=@example.com:8388#Test" > test_sub.txt

# Parse it
python -m src.cli.main parse test_sub.txt --verbose

# Check Redis
redis-cli HGETALL node:<node_id>
```

## Common Development Tasks

### Add a New Protocol Parser

1. Create parser class in `src/parsers/<protocol>.py`
2. Inherit from `BaseParser`
3. Implement `parse(uri: str) -> Node` method
4. Register parser in `src/parsers/__init__.py`
5. Add unit tests in `tests/unit/test_<protocol>_parser.py`
6. Add test fixtures in `tests/fixtures/`

### Add a New Export Format

1. Create exporter class in `src/storage/<format>_export.py`
2. Implement `export(result: ParseResult, output_path: str)` method
3. Register exporter in `src/storage/__init__.py`
4. Add unit tests
5. Update CLI to support new format

### Debug Parsing Issues

```bash
# Enable verbose logging
python -m src.cli.main parse file.txt --verbose

# Check log file
tail -f ~/.subscription-parser.log

# Use Python debugger
python -m pdb -m src.cli.main parse file.txt
```

### Test Redis Integration

```python
# tests/integration/test_redis_integration.py
import pytest
from src.storage.redis_store import RedisStore
from src.models.node import Node

@pytest.fixture
def redis_store():
    store = RedisStore(url='redis://localhost:6379/1')  # Use DB 1 for tests
    yield store
    store.client.flushdb()  # Clean up after test

def test_store_and_retrieve_node(redis_store):
    node = Node(
        protocol='ss',
        host='example.com',
        port=8388,
        password='test',
        cipher='aes-256-gcm'
    )

    # Store node
    redis_store.store_node(node, source_id='test_sub')

    # Retrieve node
    retrieved = redis_store.get_node(node.node_id)

    assert retrieved.protocol == node.protocol
    assert retrieved.host == node.host
    assert retrieved.port == node.port
```

## Configuration

### Environment Variables

```bash
# Set Redis URL
export REDIS_URL=redis://localhost:6379/0

# Set output directory
export SUBSCRIPTION_PARSER_OUTPUT_DIR=/data/exports

# Set log level
export SUBSCRIPTION_PARSER_LOG_LEVEL=DEBUG
```

### Configuration File

Create `~/.subscription-parser.yaml`:

```yaml
redis:
  url: redis://localhost:6379/0
  timeout: 5

output:
  directory: ./output
  format: both

logging:
  level: INFO
  file: ~/.subscription-parser.log

parsing:
  retry_attempts: 3
  retry_backoff: exponential
```

## Troubleshooting

### Redis Connection Failed

```bash
# Check Redis is running
redis-cli ping

# Check connection
redis-cli -h localhost -p 6379 ping

# Check firewall
telnet localhost 6379
```

### Import Errors

```bash
# Ensure virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Parsing Failures

```bash
# Check file encoding
file -i subscription.txt

# Try manual base64 decode
base64 -d subscription.txt

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('subscription.txt'))"
```

### Performance Issues

```bash
# Profile parsing
python -m cProfile -o profile.stats -m src.cli.main parse large_file.txt

# Analyze profile
python -m pstats profile.stats
# Then: sort cumtime, stats 20

# Use parallel processing for batch
python -m src.cli.main batch /data/subs --parallel 4
```

## Next Steps

1. **Implement remaining parsers**: Complete all 7 protocol parsers (ss, ssr, trojan, vmess, vless, hysteria, hysteria2)
2. **Add comprehensive tests**: Achieve 90%+ code coverage
3. **Optimize performance**: Profile and optimize hot paths
4. **Add CLI commands**: Implement list, info, export commands
5. **Write documentation**: Add docstrings and user guide

## Resources

- [Specification](./spec.md) - Feature requirements
- [Data Model](./data-model.md) - Entity definitions
- [CLI Contract](./contracts/cli-contract.md) - Interface specification
- [Research](./research.md) - Technical decisions

## Getting Help

- Check logs: `~/.subscription-parser.log`
- Run tests: `pytest -v`
- Enable debug mode: `--verbose` flag
- Review test fixtures: `tests/fixtures/`

## Code Style

Follow project constitution:
- PEP8 compliance (use `black` and `flake8`)
- English variable names
- Chinese comments for team review
- Type hints for all functions
- Docstrings for all public APIs

```bash
# Format code
black src/ tests/

# Check style
flake8 src/ tests/

# Type check
mypy src/
```

## Commit Guidelines

```bash
# After implementing a feature
git add src/parsers/ss.py tests/unit/test_ss_parser.py
git commit -m "feat: implement Shadowsocks parser

- Add ShadowsocksParser class
- Support ss:// URI format
- Add unit tests with 95% coverage
- Handle base64 encoding edge cases

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

## Ready to Code!

You now have everything needed to start implementing the subscription parser. Begin with the core parsing logic (Phase 1 from research.md), then add storage integration (Phase 2), and finally batch processing (Phase 3).

Happy coding! 🚀
