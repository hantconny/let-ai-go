# Data Model: 订阅解析器 (Subscription Parser)

**Feature**: 001-subscription-parser
**Date**: 2026-03-05
**Purpose**: Define data structures and relationships for subscription parsing

## Overview

This document defines the core data entities, their attributes, relationships, and validation rules for the subscription parser system.

## Core Entities

### 1. Node (Proxy Node)

Represents a single proxy server configuration extracted from a subscription file.

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| node_id | str | Yes | SHA256 hash of (protocol + host + port) | 64-char hex string |
| protocol | str | Yes | Proxy protocol type | One of: ss, ssr, trojan, vmess, vless, hysteria, hysteria2 |
| host | str | Yes* | PI address or domain name | Valid IP or FQDN |
| port | int | Yes | Port number | 1-65535 |
| tls | bool | No | Whether TLS is enabled | true/false |
| sni | str | No | Server Name Indication | Valid domain name |
| uuid | str | No | UUID for vmess/vless | Valid UUID format |
| password | str | No | Password for ss/ssr/trojan | Non-empty string |
| cipher | str | No | Encryption cipher | Protocol-specific values |
| transport | str | No | Transport layer protocol | tcp, kcp, ws, h2, quic, grpc |
| network | str | No | Application layer protocol | tcp, udp, ws, h2 |
| auth_protocol | str | No | Authentication protocol (ssr) | origin, auth_sha1_v4, etc. |
| obfuscation | str | No | Obfuscation method (ssr) | plain, http_simple, tls1.2_ticket_auth, etc. |
| remarks | str | No | Human-readable node name | Any string |
| source_id | str | Yes | Subscription file identifier | Filename without extension |
| parsed_at | datetime | Yes | Timestamp when parsed | ISO 8601 format |

*Note: Either `host` must be present (domain or IP)

**Relationships**:
- Belongs to one or more Subscriptions (many-to-many via Redis Set)
- Identified uniquely by node_id across all subscriptions

**State Transitions**: None (immutable once parsed)

**Validation Rules**:
1. `node_id` must be generated from canonical form: `{protocol}://{host}:{port}`
2. `protocol` must be one of the supported types
3. `port` must be in valid range (1-65535)
4. Protocol-specific required fields:
   - ss: password, cipher
   - ssr: password, cipher, auth_protocol, obfuscation
   - trojan: password
   - vmess: uuid, cipher
   - vless: uuid
   - hysteria/hysteria2: varies by version
5. If `tls` is true, `sni` should be present (warning if missing)
6. `host` must be either valid IPv4, IPv6, or domain name

**Example**:
```python
{
    "node_id": "a1b2c3d4e5f6...",
    "protocol": "vmess",
    "host": "example.com",
    "port": 443,
    "tls": true,
    "sni": "example.com",
    "uuid": "12345678-1234-1234-1234-123456789012",
    "cipher": "auto",
    "transport": "ws",
    "network": "tcp",
    "remarks": "US Server 1",
    "source_id": "subscription_2024",
    "parsed_at": "2026-03-05T10:30:00Z"
}
```

### 2. Subscription

Represents metadata about a subscription file and its parsing results.

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| source_id | str | Yes | Unique identifier (filename without extension) | Non-empty, valid filename chars |
| file_path | str | Yes | Original file path | Valid path |
| format | str | Yes | Detected format | base64, yaml, mixed |
| total_nodes | int | Yes | Total nodes found | >= 0 |
| successful_nodes | int | Yes | Successfully parsed nodes | >= 0, <= total_nodes |
| failed_nodes | int | Yes | Failed to parse nodes | >= 0, total = successful + failed |
| parsed_at | datetime | Yes | Parsing timestamp | ISO 8601 format |
| duration_ms | int | Yes | Parsing duration in milliseconds | >= 0 |
| errors | list[str] | No | Error messages for failed nodes | List of error strings |

**Relationships**:
- Has many Nodes (via Redis Set: `subscription:{source_id}:nodes`)

**State Transitions**: None (immutable once parsing complete)

**Validation Rules**:
1. `source_id` must be unique per parsing session
2. `total_nodes` = `successful_nodes` + `failed_nodes`
3. `format` must be one of: base64, yaml, mixed
4. `duration_ms` should be positive

**Example**:
```python
{
    "source_id": "subscription_2024",
    "file_path": "/data/subscriptions/subscription_2024.txt",
    "format": "base64",
    "total_nodes": 150,
    "successful_nodes": 148,
    "failed_nodes": 2,
    "parsed_at": "2026-03-05T10:30:00Z",
    "duration_ms": 1250,
    "errors": [
        "Line 45: Invalid vmess URI - missing uuid",
        "Line 89: Unknown protocol 'socks5'"
    ]
}
```

### 3. ParseResult

Represents the complete output of a parsing operation (used for file exports).

**Attributes**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| subscription | Subscription | Yes | Subscription metadata |
| nodes | list[Node] | Yes | List of successfully parsed nodes |
| export_format | str | Yes | Format of this export (json or csv) |
| exported_at | datetime | Yes | Export timestamp |

**Relationships**:
- Contains one Subscription
- Contains many Nodes

**Validation Rules**:
1. `nodes` length must equal `subscription.successful_nodes`
2. `export_format` must be 'json' or 'csv'
3. All nodes must have same `source_id` as subscription

**Example** (JSON export):
```json
{
    "subscription": {
        "source_id": "subscription_2024",
        "file_path": "/data/subscriptions/subscription_2024.txt",
        "format": "base64",
        "total_nodes": 150,
        "successful_nodes": 148,
        "failed_nodes": 2,
        "parsed_at": "2026-03-05T10:30:00Z",
        "duration_ms": 1250
    },
    "nodes": [
        { "node_id": "...", "protocol": "vmess", ... },
        { "node_id": "...", "protocol": "ss", ... }
    ],
    "export_format": "json",
    "exported_at": "2026-03-05T10:31:00Z"
}
```

## Redis Storage Schema

### Key Patterns

1. **Node Storage** (Hash):
   ```
   Key: node:{node_id}
   Type: Hash
   TTL: 7 days (604800 seconds)
   Fields: All Node attributes as hash fields
   ```

2. **Subscription Index** (Set):
   ```
   Key: subscription:{source_id}:nodes
   Type: Set
   TTL: 7 days (604800 seconds)
   Members: node_id values
   ```

3. **Subscription Metadata** (Hash):
   ```
   Key: subscription:{source_id}:meta
   Type: Hash
   TTL: 7 days (604800 seconds)
   Fields: All Subscription attributes as hash fields
   ```

### Example Redis Operations

**Store a node**:
```redis
HSET node:a1b2c3d4e5f6 protocol vmess host example.com port 443 tls true ...
EXPIRE node:a1b2c3d4e5f6 604800
SADD subscription:subscription_2024:nodes a1b2c3d4e5f6
EXPIRE subscription:subscription_2024:nodes 604800
```

**Query nodes by subscription**:
```redis
SMEMBERS subscription:subscription_2024:nodes
# Returns: ["a1b2c3d4e5f6", "b2c3d4e5f6a7", ...]

# Then fetch each node:
HGETALL node:a1b2c3d4e5f6
```

**Check if node exists**:
```redis
EXISTS node:a1b2c3d4e5f6
```

## Protocol-Specific Field Requirements

### Shadowsocks (ss)

**Required**: protocol, host, port, password, cipher
**Optional**: remarks

**Example URI**: `ss://base64(cipher:password)@host:port#remarks`

### ShadowsocksR (ssr)

**Required**: protocol, host, port, password, cipher, auth_protocol, obfuscation
**Optional**: remarks

**Example URI**: `ssr://base64(host:port:auth:cipher:obfs:base64(password)/?params)`

### Trojan

**Required**: protocol, host, port, password
**Optional**: tls, sni, remarks

**Example URI**: `trojan://password@host:port?sni=example.com#remarks`

### VMess

**Required**: protocol, host, port, uuid, cipher
**Optional**: tls, sni, transport, network, remarks

**Example URI**: `vmess://base64(json_config)`

### VLESS

**Required**: protocol, host, port, uuid
**Optional**: tls, sni, transport, network, remarks

**Example URI**: `vless://uuid@host:port?type=tcp&security=tls#remarks`

### Hysteria / Hysteria2

**Required**: protocol, host, port
**Optional**: tls, sni, password, remarks

**Example URI**: `hysteria://host:port?auth=password&peer=sni#remarks`

## Data Flow

```
┌─────────────────┐
│ Subscription    │
│ File (raw)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Format Detector │
│ & Decoder       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Protocol Parser │
│ (per node URI)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Node Model      │
│ (validated)     │
└────────┬────────┘
         │
         ├──────────────┐
         │              │
         ▼              ▼
┌─────────────┐  ┌──────────────┐
│ Redis Store │  │ File Export  │
│ (Hash+Set)  │  │ (JSON/CSV)   │
└─────────────┘  └──────────────┘
```

## Validation Error Handling

### Node-Level Errors

| Error Type | Action | Logged As |
|------------|--------|-----------|
| Missing required field | Skip node, continue parsing | WARNING |
| Invalid protocol | Skip node, continue parsing | WARNING |
| Invalid port range | Skip node, continue parsing | WARNING |
| Malformed URI | Skip node, continue parsing | WARNING |
| Hash collision (rare) | Log warning, use existing node | WARNING |

### File-Level Errors

| Error Type | Action | Logged As |
|------------|--------|-----------|
| File not found | Retry 3x, then fail | ERROR |
| Permission denied | Retry 3x, then fail | ERROR |
| Encoding detection failed | Try all formats, then fail | ERROR |
| Empty file | Log warning, return empty result | WARNING |
| All nodes failed | Log error, return empty result | ERROR |

### Redis Errors

| Error Type | Action | Logged As |
|------------|--------|-----------|
| Connection failed | Retry 3x with backoff, then fail | ERROR |
| Timeout | Retry 3x with backoff, then fail | ERROR |
| Out of memory | Fail immediately, log critical | CRITICAL |
| Authentication failed | Fail immediately | ERROR |

## Performance Considerations

### Memory Usage

- Each node: ~500 bytes (average)
- 100 nodes: ~50 KB
- 10,000 nodes: ~5 MB
- Redis overhead: ~2x (Hash structure)

### Redis Key Count

- Per subscription with N nodes: 1 + N + 1 = N + 2 keys
  - 1 subscription metadata hash
  - N node hashes
  - 1 subscription index set

### TTL Management

- All keys expire after 7 days automatically
- No manual cleanup required
- Re-parsing same subscription refreshes TTL

## Future Extensions

Potential data model extensions (not in current scope):

1. **Node History**: Track changes to node configurations over time
2. **Subscription Updates**: Detect and merge updates to existing subscriptions
3. **Node Health**: Store availability/latency metrics
4. **User Annotations**: Allow manual tagging/categorization of nodes
5. **Geolocation**: Add country/region fields based on IP
