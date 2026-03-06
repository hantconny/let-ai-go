---

description: "Task list for subscription parser implementation"
---

# Tasks: 订阅解析器 (Subscription Parser)

**Input**: Design documents from `/specs/001-subscription-parser/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - only included if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below follow single project structure from plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per plan.md (src/, tests/, tests/fixtures/)
- [X] T002 Initialize Python project with pyproject.toml and requirements.txt
- [X] T003 [P] Configure development tools (black, flake8, mypy) in pyproject.toml
- [X] T004 [P] Setup loguru logger configuration in src/utils/logger.py
- [X] T005 [P] Create test fixtures directory and sample files in tests/fixtures/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create Node data model in src/models/node.py with all 17 attributes
- [X] T007 Create Subscription metadata model in src/models/subscription.py
- [X] T008 Create ParseResult model in src/models/__init__.py
- [X] T009 Implement SHA256 hash generator for node_id in src/utils/hash_generator.py
- [X] T010 Create base parser interface in src/parsers/base.py with parse() method
- [X] T011 Create base decoder interface in src/decoders/__init__.py
- [X] T012 [P] Setup Redis connection manager in src/storage/redis_store.py with connection pooling
- [X] T013 [P] Create file export base class in src/storage/file_export.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 解析单个订阅文件 (Priority: P1) 🎯 MVP

**Goal**: Parse a single subscription file (any format) and extract all node information to Redis and file exports

**Independent Test**: Provide a subscription file with multiple nodes, system successfully parses and outputs all node information to both Redis and files

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement base64 decoder in src/decoders/base64_decoder.py
- [X] T015 [P] [US1] Implement YAML decoder in src/decoders/yaml_decoder.py
- [X] T016 [US1] Implement format detector with fallback chain in src/decoders/format_detector.py
- [X] T017 [P] [US1] Implement Shadowsocks (ss) parser in src/parsers/ss.py
- [X] T018 [P] [US1] Implement VMess parser in src/parsers/vmess.py
- [X] T019 [US1] Create parser registry in src/parsers/__init__.py for protocol selection
- [X] T020 [US1] Implement Redis storage operations (store_node, get_node, store_subscription) in src/storage/redis_store.py
- [X] T021 [US1] Implement JSON export in src/storage/file_export.py
- [X] T022 [US1] Implement CSV export in src/storage/file_export.py
- [X] T023 [US1] Create main parsing orchestrator in src/cli/main.py with parse command
- [X] T024 [US1] Add 3-retry mechanism with exponential backoff for file I/O and Redis operations
- [X] T025 [US1] Add error handling for encoding detection failures, format errors, and field validation
- [X] T026 [US1] Add loguru logging for all parsing operations (file, nodes, errors, duration)

**Checkpoint**: At this point, User Story 1 should be fully functional - can parse single file, detect format, extract ss/vmess nodes, store in Redis with 7-day TTL, export to JSON/CSV

---

## Phase 4: User Story 2 - 批量处理多个订阅文件 (Priority: P2)

**Goal**: Process multiple subscription files from a directory with progress tracking and error resilience

**Independent Test**: Provide directory with 10 different format subscription files, system traverses all files and generates unified output

### Implementation for User Story 2

- [X] T027 [US2] Implement directory traversal logic in src/cli/main.py batch command
- [X] T028 [US2] Add tqdm progress bar for batch processing with file count and rate display
- [X] T029 [US2] Implement batch error handling (continue on single file failure, collect errors)
- [X] T030 [US2] Add batch summary statistics (total files, successful, failed, total nodes, duration)
- [X] T031 [US2] Implement parallel processing option with configurable worker count
- [X] T032 [US2] Add batch result aggregation and consolidated export

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - single file parsing works, batch processing works with progress tracking

---

## Phase 5: User Story 3 - 导出结构化数据 (Priority: P3)

**Goal**: Export parsed node data from Redis to JSON/CSV formats for integration with other tools

**Independent Test**: After parsing, export results to JSON and CSV formats with complete and accurate data

### Implementation for User Story 3

- [X] T033 [US3] Implement export command in src/cli/main.py to retrieve from Redis
- [X] T034 [US3] Add source_id query functionality to Redis store
- [X] T035 [US3] Implement list command to show all subscriptions in Redis with TTL info
- [X] T036 [US3] Implement info command to show subscription details and protocol distribution
- [X] T037 [US3] Add export format validation and output path handling
- [X] T038 [US3] Add export error handling for missing source_id and file write failures

**Checkpoint**: All user stories should now be independently functional - parse, batch, and export all work

---

## Phase 6: Additional Protocol Support

**Purpose**: Extend parser to support remaining 5 protocol types

- [X] T039 [P] Implement ShadowsocksR (ssr) parser in src/parsers/ssr.py
- [X] T040 [P] Implement Trojan parser in src/parsers/trojan.py
- [X] T041 [P] Implement VLESS parser in src/parsers/vless.py
- [X] T042 [P] Implement Hysteria parser in src/parsers/hysteria.py
- [X] T043 [P] Implement Hysteria2 parser in src/parsers/hysteria2.py
- [X] T044 Register all new parsers in parser registry

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

**Constitution Compliance Tasks**:
- [X] T045 Verify PEP8 compliance across all code using black and flake8
- [X] T046 Validate all variables use English names, comments use Chinese
- [X] T047 Ensure 3-retry mechanism with error context logging in all I/O operations
- [X] T048 Verify loguru logging includes: source_id, node count, duration, error stack traces
- [X] T049 Confirm resource cleanup (file handles, Redis connections) in all exit paths
- [X] T050 Add progress indicators (tqdm) to all long-running operations
- [X] T051 Validate error messages are clear and actionable (<1 second response time)

**General Polish**:
- [X] T052 [P] Add type hints to all functions and classes
- [X] T053 [P] Add docstrings (Chinese) to all public APIs
- [X] T054 [P] Create sample subscription files for all 7 protocols in tests/fixtures/
- [X] T055 Add CLI help text and usage examples for all commands
- [X] T056 Add version command to display tool and dependency versions
- [X] T057 Implement configuration file support (~/.subscription-parser.yaml)
- [X] T058 Add environment variable support (REDIS_URL, OUTPUT_DIR, LOG_LEVEL)
- [ ] T059 Performance profiling and optimization for large files (>10MB)
- [X] T060 Run quickstart.md validation with all sample files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 2 (P2): Can start after Foundational - Depends on US1 parse logic but independently testable
  - User Story 3 (P3): Can start after Foundational - Depends on US1 storage but independently testable
- **Additional Protocols (Phase 6)**: Can start after US1 completes (parser infrastructure ready)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Reuses US1 parsing logic, independently testable with batch workflow
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Reuses US1 storage, independently testable with export workflow

### Within Each User Story

- Models before services
- Decoders before parsers
- Parsers before storage
- Storage before CLI commands
- Core implementation before error handling
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Within User Story 1: T014-T015 (decoders), T017-T018 (parsers) can run in parallel
- Within Phase 6: All protocol parsers (T039-T043) can run in parallel
- Within Phase 7: T045-T046, T052-T054 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch decoders in parallel:
Task: "Implement base64 decoder in src/decoders/base64_decoder.py"
Task: "Implement YAML decoder in src/decoders/yaml_decoder.py"

# Launch parsers in parallel (after decoders complete):
Task: "Implement Shadowsocks (ss) parser in src/parsers/ss.py"
Task: "Implement VMess parser in src/parsers/vmess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently with sample files
5. Verify: Format detection works, ss/vmess parsing works, Redis storage works with TTL, JSON/CSV export works
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (batch processing added)
4. Add User Story 3 → Test independently → Deploy/Demo (export commands added)
5. Add Phase 6 → Test independently → Deploy/Demo (all 7 protocols supported)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (core parsing)
   - Developer B: User Story 2 (batch processing) - starts after US1 parse logic ready
   - Developer C: Phase 6 (additional protocols) - starts after US1 parser infrastructure ready
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Tests are OPTIONAL - not included in this task list as not explicitly requested in spec
