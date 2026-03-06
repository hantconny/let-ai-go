# Research: 订阅解析器 (Subscription Parser)

**Feature**: 001-subscription-parser
**Date**: 2026-03-05
**Purpose**: Technical research and decision documentation for implementation planning

## Overview

This document consolidates research findings for building a subscription parser that handles multiple proxy protocols and encoding formats, with dual storage (Redis + file exports).

## Key Technical Decisions

### 1. Protocol Parsing Strategy

**Decision**: Implement protocol-specific parser classes with a common base interface

**Rationale**:
- Each protocol (ss, ssr, trojan, vmess, vless, hysteria, hysteria2) has unique URI schemes and parameter formats
- Protocol specifications vary significantly in complexity (ss is simple, vmess is complex JSON-based)
- Extensibility: new protocols can be added without modifying existing parsers
- Testability: each parser can be unit tested independently

**Alternatives Considered**:
- Single monolithic parser with conditional logic: Rejected due to poor maintainability and testing complexity
- External parsing libraries: Evaluated but most are incomplete or unmaintained; custom implementation provides better control

**Implementation Approach**:
- Base parser interface defines: `parse(uri: str) -> Node`
- Each protocol parser handles its specific URI format (e.g., `ss://`, `vmess://`)
- Common validation logic extracted to base class
- Parser registry pattern for dynamic protocol selection

### 2. Format Detection and Decoding

**Decision**: Multi-stage detection pipeline with fallback chain

**Rationale**:
- Subscription files can be: pure base64, pure YAML, or mixed (base64 lines within YAML)
- No reliable magic bytes or headers to distinguish formats
- Must handle malformed or partially corrupted data gracefully

**Detection Strategy**:
1. Attempt YAML parsing first (most structured format)
2. If YAML fails, attempt full base64 decode
3. If full decode fails, try line-by-line base64 decode (mixed format)
4. Extract proxy URIs from decoded content using regex patterns

**Alternatives Considered**:
- File extension-based detection: Rejected - files from traffic capture have unreliable extensions
- ML-based format classification: Rejected - overkill for 3 known formats, adds dependency complexity

### 3. Node ID Generation (Deduplication)

**Decision**: SHA256 hash of canonical key attributes (protocol + host + port)

**Rationale**:
- Deterministic: same node configuration always produces same ID
- Enables automatic deduplication across multiple subscription sources
- Collision probability negligible with SHA256
- Supports identifying when same node appears in different subscriptions

**Hash Input Format**:
```
{protocol}://{ip_or_domain}:{port}
```

**Alternatives Considered**:
- UUID v4: Rejected - random IDs prevent deduplication
- Hash of all attributes: Rejected - minor config differences (e.g., remarks) would create duplicates
- Sequential integers: Rejected - not globally unique across distributed parsing

### 4. Redis Data Structure Design

**Decision**: Hash per node + Set index per subscription (as clarified)

**Redis Keys**:
- `node:{node_id}` → Hash with all node fields
- `subscription:{source_id}:nodes` → Set of node_ids
- TTL: 7 days on all keys

**Rationale**:
- Efficient individual node access: O(1) lookup by node_id
- Efficient subscription queries: O(N) where N = nodes in subscription
- Supports deduplication: same node_id across subscriptions
- Memory efficient: shared nodes referenced by multiple subscriptions
- TTL prevents unbounded growth

**Field Storage in Hash**:
```
HSET node:{node_id}
  protocol "vmess"
  host "example.com"
  port "443"
  tls "true"
  sni "example.com"
  uuid "xxx-xxx-xxx"
  ... (all extracted fields)
```

**Alternatives Considered**:
- JSON string per subscription: Rejected - inefficient for queries, no deduplication
- Sorted sets with timestamps: Rejected - time-based queries not required
- Relational structure with multiple key types: Rejected - over-engineered for use case

### 5. Error Handling and Retry Strategy

**Decision**: 3-level retry with exponential backoff for transient errors

**Retry Scope**:
- File I/O errors (permission, not found)
- Redis connection failures
- Encoding detection failures

**Non-Retryable Errors**:
- Malformed protocol URIs (log and skip node)
- Invalid YAML syntax (log and skip file)
- Missing required fields (log and skip node)

**Rationale**:
- Aligns with constitution's 3-retry requirement
- Transient errors (network, file locks) often resolve quickly
- Permanent errors (bad data) won't be fixed by retries
- Exponential backoff prevents resource exhaustion

**Implementation**:
```python
@retry(max_attempts=3, backoff=exponential, exceptions=(IOError, RedisConnectionError))
def parse_file(path):
    ...
```

### 6. Progress Tracking and Observability

**Decision**: tqdm for progress bars + loguru for structured logging

**Progress Indicators**:
- File-level progress bar for batch processing
- Node-level counter within each file
- Real-time statistics: success/failure counts, processing rate

**Logging Strategy**:
- INFO: File start/complete, summary statistics
- WARNING: Skipped nodes, format detection fallbacks
- ERROR: Retry attempts, final failures with context
- DEBUG: Detailed parsing steps (disabled by default)

**Log Format**:
```
{time} | {level} | {module} | file={filename} nodes_parsed={count} duration={ms}
```

**Rationale**:
- tqdm provides user-friendly visual feedback
- loguru offers structured logging without boilerplate
- Separation of concerns: progress for users, logs for debugging
- Aligns with constitution's observability requirements

### 7. File Export Formats

**Decision**: Support both JSON (structured) and CSV (tabular)

**JSON Structure**:
```json
{
  "source_id": "subscription_name",
  "parsed_at": "2026-03-05T10:30:00Z",
  "nodes": [
    {
      "node_id": "abc123...",
      "protocol": "vmess",
      "host": "example.com",
      ...
    }
  ]
}
```

**CSV Structure**:
- Header row with all possible fields
- One row per node
- Empty cells for protocol-specific fields not applicable

**Rationale**:
- JSON: Machine-readable, preserves types, easy integration with other tools
- CSV: Human-readable in Excel, simple data analysis
- Both formats specified in requirements (FR-008)

**Alternatives Considered**:
- XML: Rejected - verbose, not commonly used in this domain
- Protocol Buffers: Rejected - requires schema distribution, overkill for simple exports
- SQLite: Rejected - adds complexity, Redis already provides queryable storage

### 8. Dependency Management

**Core Dependencies**:
- `redis>=5.0.0` - Redis client
- `pyyaml>=6.0` - YAML parsing
- `loguru>=0.7.0` - Logging
- `tqdm>=4.65.0` - Progress bars
- `pytest>=7.4.0` - Testing framework

**Standard Library Usage**:
- `urllib.parse` - URL parsing
- `json` - JSON handling
- `hashlib` - SHA256 hashing
- `base64` - Base64 encoding/decoding
- `pathlib` - File path operations
- `typing` - Type hints

**Rationale**:
- Minimal external dependencies reduces maintenance burden
- All chosen libraries are mature and widely used
- Standard library preferred where functionality sufficient
- Aligns with plan.md specified dependencies

### 9. Testing Strategy

**Unit Tests**:
- Each protocol parser with valid/invalid URIs
- Format detectors with various encoding combinations
- Hash generator with collision testing
- Redis store with mocked connections

**Integration Tests**:
- End-to-end: file → parse → Redis → export
- Redis integration with real Redis instance (test container)
- Batch processing with multiple files

**Test Fixtures**:
- Sample subscription files for each format
- Known-good protocol URIs for each type
- Edge cases: empty files, malformed data, mixed protocols

**Coverage Target**: 90%+ line coverage

**Rationale**:
- Constitution requires testing with simulated failure scenarios
- Unit tests enable rapid development feedback
- Integration tests validate real-world workflows
- Fixtures ensure consistent test data

### 10. CLI Interface Design

**Decision**: Simple command-line interface with subcommands

**Commands**:
```bash
# Parse single file
subscription-parser parse <file> [--output-dir <dir>] [--redis-url <url>]

# Parse directory (batch)
subscription-parser batch <directory> [--output-dir <dir>] [--redis-url <url>]

# Export from Redis
subscription-parser export <source_id> --format {json|csv} --output <file>
```

**Options**:
- `--redis-url`: Redis connection string (default: localhost:6379)
- `--output-dir`: Directory for file exports (default: ./output)
- `--format`: Export format (json or csv)
- `--verbose`: Enable debug logging
- `--no-redis`: Skip Redis storage (file export only)
- `--no-export`: Skip file export (Redis only)

**Rationale**:
- Subcommand pattern scales well for future features
- Sensible defaults minimize required arguments
- Flags for disabling storage backends support different use cases
- Follows Unix philosophy: do one thing well

## Implementation Priorities

### Phase 1: Core Parsing (MVP)
1. Format detection and decoding
2. Protocol parsers (start with ss, vmess as most common)
3. Node model and hash generation
4. Basic file I/O

### Phase 2: Storage Integration
1. Redis client and data structure implementation
2. File export (JSON first, then CSV)
3. Error handling and retry logic

### Phase 3: Batch Processing
1. Directory traversal
2. Progress tracking with tqdm
3. Parallel processing (if performance requires)

### Phase 4: Remaining Protocols
1. ssr, trojan, vless parsers
2. hysteria, hysteria2 parsers
3. Comprehensive protocol test coverage

### Phase 5: Polish
1. CLI interface refinement
2. Logging optimization
3. Documentation and examples
4. Performance profiling and optimization

## Open Questions

None - all clarifications resolved during specification phase.

## References

- Shadowsocks URI Scheme: https://shadowsocks.org/doc/sip002.html
- VMess Protocol: https://www.v2fly.org/config/protocols/vmess.html
- Clash Configuration: https://github.com/Dreamacro/clash/wiki/configuration
- Redis Commands: https://redis.io/commands/
- Python Redis Client: https://redis-py.readthedocs.io/
