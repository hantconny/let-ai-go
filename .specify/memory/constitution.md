<!--
Sync Impact Report:
- Version change: Initial → 1.0.0
- Modified principles: N/A (initial creation)
- Added sections:
  * Core Principles (4 principles)
  * Tech Stack Constraints
  * Security & Compliance
  * Delivery Quality Standards
  * Governance
- Removed sections: N/A
- Templates requiring updates:
  ✅ plan-template.md - Constitution Check section aligned
  ✅ spec-template.md - Requirements section aligned with principles
  ✅ tasks-template.md - Task categorization aligned with quality standards
- Follow-up TODOs: None
-->

# Let-AI-Go Constitution

## Core Principles

### I. Spec-First Development (先规范后代码)

All feature development MUST begin with a corresponding business logic specification in the `specs/` directory. No code implementation is permitted without an approved specification document.

**Rationale**: Ensures alignment between business requirements and technical implementation, reduces rework, and provides clear documentation for team review.

### II. Defensive Programming (防御性编程)

Web scraping and automation scripts MUST anticipate target changes. All implementations MUST include fault tolerance for:
- UI element changes and layout modifications
- Network fluctuations and timeout scenarios
- Anti-scraping mechanism upgrades

**Rationale**: Target systems evolve continuously. Defensive programming ensures script longevity and reduces maintenance overhead.

### III. Code Quality Standards (代码整洁度)

- MUST follow PEP8 coding standards
- Variable names MUST be semantic and in English
- Comments MUST be written in Chinese for team review purposes

**Rationale**: Balances international coding standards with team communication efficiency. English variable names ensure code portability while Chinese comments facilitate internal collaboration.

### IV. Self-Healing Capability (自愈能力)

When UI element location fails, scripts MUST:
- Automatically retry up to 3 times
- Save screenshot to `debug/screenshots/` on the 3rd failure
- Log failure context with device ID, task ID, and error details

**Rationale**: Reduces manual intervention requirements and provides debugging artifacts for rapid issue resolution.

## Tech Stack Constraints

**Language**: Python 3.10+

**Web Scraping**:
- MUST use Playwright in async mode
- MUST NOT use raw `requests` library for large-scale scraping without proper encapsulation

**Mobile Automation**:
- MUST use uiautomator2 for Android automation

**Logging System**:
- MUST use loguru
- Logs MUST include: device ID, task ID, execution time, exception stack traces

**Rationale**: Standardized tech stack ensures consistency, maintainability, and team expertise concentration.

## Security & Compliance

### Rate Limiting (频率控制)

- Single device/account scraping frequency MUST NOT exceed business baseline (default: 1 request per 3 seconds)
- MUST implement `random.uniform` jitter to avoid detection patterns

### Data Privacy (脱敏要求)

- User information (phone numbers, IDs) MUST be MD5 hashed or masked before database insertion
- No plaintext sensitive data in logs or storage

### Resource Management (资源回收)

- Scripts MUST enforce cleanup on exit or error
- MUST NOT produce zombie processes
- All browser instances, network connections, and file handles MUST be properly closed

**Rationale**: Compliance with data protection regulations, respect for target systems, and operational stability.

## Delivery Quality Standards

### Observability (可观测性)

- MUST generate real-time progress indicators (e.g., using tqdm)
- MUST log all critical operations with timestamps and context
- MUST provide clear error messages with actionable information

### Testing Requirements

- All scripts MUST be tested with simulated failure scenarios
- MUST verify self-healing mechanisms work as expected
- MUST validate rate limiting and privacy controls

**Rationale**: Ensures production readiness and reduces incident response time.

## Governance

This constitution supersedes all other development practices. All code reviews, pull requests, and deployments MUST verify compliance with these principles.

**Amendment Process**:
1. Proposed changes MUST be documented with rationale
2. Team approval required before adoption
3. Version increment according to semantic versioning
4. Migration plan required for breaking changes

**Compliance Review**:
- All PRs MUST pass constitution compliance checks
- Any complexity or deviation MUST be explicitly justified
- Regular audits to ensure ongoing adherence

**Version**: 1.0.0 | **Ratified**: 2026-03-05 | **Last Amended**: 2026-03-05
