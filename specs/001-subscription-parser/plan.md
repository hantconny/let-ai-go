# Implementation Plan: 订阅解析器 (Subscription Parser)

**Branch**: `001-subscription-parser` | **Date**: 2026-03-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-subscription-parser/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a subscription parser that processes proxy subscription files from network traffic, supporting multiple formats (base64, YAML, mixed) and protocols (ss, ssr, trojan, vmess, vless, hysteria, hysteria2). The parser extracts node configuration details and stores results in both Redis (with 7-day TTL) and file exports (JSON/CSV). Implements defensive programming with 3-retry mechanism, progress tracking, and comprehensive logging.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**:
- urlparse (URL parsing)
- json (JSON handling)
- yaml (YAML parsing)
- requests (network access)
- redis (Redis 5.0+ client)
- loguru (logging)
- tqdm (progress indicators)
- hashlib (node ID generation)

**Storage**: Redis 5.0+ (primary with 7-day TTL) + File system (JSON/CSV exports)
**Testing**: pytest
**Target Platform**: Linux/Windows server environment
**Project Type**: CLI tool / library
**Performance Goals**:
- Single file (100 nodes): <5 seconds
- Batch (100 files): <5 minutes
- 95%+ format recognition accuracy
- 98%+ field extraction accuracy

**Constraints**:
- File size: typically <10MB, max 100MB
- Redis TTL: 7 days auto-expiration
- Retry limit: 3 attempts max
- Error response: <1 second

**Scale/Scope**:
- Support 7 protocol types
- Handle 3 encoding formats (base64, YAML, mixed)
- Extract 13+ node attributes per proxy
- Batch processing capability

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Spec-First**: Specification exists in `specs/001-subscription-parser/` directory before implementation
- [x] **Defensive Programming**: 3-retry mechanism, fault tolerance for encoding/format/network errors specified in FR-012, FR-013
- [x] **Code Quality**: PEP8 compliance required, English variables + Chinese comments per constitution
- [x] **Self-Healing**: 3-retry mechanism with error context logging specified in FR-013
- [x] **Tech Stack**: Python 3.12+ (exceeds 3.10+ requirement), loguru for logging (FR-010)
- [N/A] **Rate Limiting**: Not applicable - parsing local files, not web scraping
- [N/A] **Data Privacy**: No sensitive personal data per assumptions section
- [x] **Resource Management**: Proper cleanup specified in FR-011 (file handles, memory, Redis connections)
- [x] **Observability**: Progress indicators (tqdm) in FR-006, comprehensive logging in FR-010

**Gate Status**: ✅ PASSED (2 items N/A for this feature type)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── parsers/              # Protocol-specific parsers
│   ├── __init__.py
│   ├── base.py          # Base parser interface
│   ├── ss.py            # Shadowsocks parser
│   ├── ssr.py           # ShadowsocksR parser
│   ├── trojan.py        # Trojan parser
│   ├── vmess.py         # VMess parser
│   ├── vless.py         # VLESS parser
│   ├── hysteria.py      # Hysteria parser
│   └── hysteria2.py     # Hysteria2 parser
├── decoders/            # Format detection and decoding
│   ├── __init__.py
│   ├── base64_decoder.py
│   ├── yaml_decoder.py
│   └── format_detector.py
├── storage/             # Storage backends
│   ├── __init__.py
│   ├── redis_store.py   # Redis operations
│   └── file_export.py   # JSON/CSV export
├── models/              # Data models
│   ├── __init__.py
│   ├── node.py          # Node data model
│   └── subscription.py  # Subscription metadata
├── utils/               # Utilities
│   ├── __init__.py
│   ├── hash_generator.py # node_id generation
│   └── logger.py        # Loguru configuration
└── cli/                 # CLI interface
    ├── __init__.py
    └── main.py          # Entry point

tests/
├── unit/                # Unit tests
│   ├── test_parsers.py
│   ├── test_decoders.py
│   └── test_storage.py
├── integration/         # Integration tests
│   ├── test_end_to_end.py
│   └── test_redis_integration.py
└── fixtures/            # Test data
    ├── sample_base64.txt
    ├── sample_yaml.yml
    └── sample_mixed.txt
```

**Structure Decision**: Single project structure selected. This is a CLI tool/library for parsing subscription files, not a web application or mobile app. The structure separates concerns into parsers (protocol-specific logic), decoders (format handling), storage (Redis + file exports), models (data structures), utilities (cross-cutting concerns), and CLI (user interface).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - all constitution requirements met or marked N/A for this feature type.

## Phase 0: Research (✅ Complete)

**Output**: [research.md](./research.md)

**Key Decisions**:
1. Protocol-specific parser classes with common base interface
2. Multi-stage format detection pipeline (YAML → base64 → mixed)
3. SHA256 hash for deterministic node IDs (enables deduplication)
4. Redis Hash per node + Set index per subscription
5. 3-level retry with exponential backoff for transient errors
6. tqdm for progress + loguru for structured logging
7. JSON and CSV export formats
8. Minimal external dependencies (redis, pyyaml, loguru, tqdm, pytest)
9. Comprehensive testing strategy (unit + integration)
10. CLI with subcommands (parse, batch, export, list, info)

## Phase 1: Design & Contracts (✅ Complete)

**Outputs**:
- [data-model.md](./data-model.md) - Entity definitions, validation rules, Redis schema
- [contracts/cli-contract.md](./contracts/cli-contract.md) - CLI interface specification
- [quickstart.md](./quickstart.md) - Developer quick start guide
- [CLAUDE.md](../../CLAUDE.md) - Updated agent context

**Data Model Summary**:
- **Node**: 17 attributes, protocol-specific validation, SHA256 node_id
- **Subscription**: Metadata with parsing statistics
- **ParseResult**: Complete export structure
- **Redis Schema**: Hash per node + Set index + metadata hash, 7-day TTL

**CLI Commands**: parse, batch, export, list, info, version, help

## Constitution Check (Re-evaluation)

*Post-design validation*

- [x] **Spec-First**: ✅ Complete specification with clarifications
- [x] **Defensive Programming**: ✅ 3-retry mechanism, comprehensive error handling in design
- [x] **Code Quality**: ✅ PEP8, English variables, Chinese comments specified in quickstart
- [x] **Self-Healing**: ✅ Retry logic with error context logging designed
- [x] **Tech Stack**: ✅ Python 3.12+, loguru confirmed in dependencies
- [N/A] **Rate Limiting**: N/A - File parsing, not web scraping
- [N/A] **Data Privacy**: N/A - No sensitive personal data per assumptions
- [x] **Resource Management**: ✅ Cleanup logic specified in data model error handling
- [x] **Observability**: ✅ tqdm progress bars + loguru logging designed

**Final Gate Status**: ✅ PASSED - Ready for implementation (Phase 2: /speckit.tasks)

## Next Steps

Run `/speckit.tasks` to generate actionable task breakdown for implementation.
