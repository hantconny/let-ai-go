# CLI Contract: Subscription Parser

**Feature**: 001-subscription-parser
**Date**: 2026-03-05
**Purpose**: Define command-line interface contract for the subscription parser tool

## Overview

This document specifies the command-line interface contract for the subscription parser. The tool provides commands for parsing subscription files, batch processing, and exporting data.

## Command Structure

```
subscription-parser <command> [options] [arguments]
```

## Commands

### 1. parse - Parse Single Subscription File

**Syntax**:
```bash
subscription-parser parse <file_path> [options]
```

**Arguments**:
- `file_path` (required): Path to subscription file

**Options**:
- `--redis-url <url>`: Redis connection URL (default: `redis://localhost:6379/0`)
- `--output-dir <dir>`: Directory for file exports (default: `./output`)
- `--format <format>`: Export format - `json`, `csv`, or `both` (default: `both`)
- `--no-redis`: Skip Redis storage, only export to files
- `--no-export`: Skip file export, only store in Redis
- `--verbose`, `-v`: Enable debug logging
- `--quiet`, `-q`: Suppress progress output

**Exit Codes**:
- `0`: Success
- `1`: File not found or permission error
- `2`: Parsing failed (all nodes failed)
- `3`: Redis connection error
- `4`: File export error

**Output** (stdout):
```
Parsing: /path/to/subscription.txt
Format detected: base64
Nodes found: 150
Successfully parsed: 148
Failed: 2
Duration: 1.25s

Stored in Redis: subscription:subscription
Exported to: ./output/subscription.json
Exported to: ./output/subscription.csv
```

**Example Usage**:
```bash
# Basic usage
subscription-parser parse subscription.txt

# Custom Redis and output directory
subscription-parser parse subscription.txt --redis-url redis://192.168.1.100:6379 --output-dir /data/exports

# Only store in Redis, no file export
subscription-parser parse subscription.txt --no-export

# Only export to JSON, no Redis
subscription-parser parse subscription.txt --no-redis --format json

# Verbose mode
subscription-parser parse subscription.txt -v
```

### 2. batch - Batch Process Multiple Files

**Syntax**:
```bash
subscription-parser batch <directory> [options]
```

**Arguments**:
- `directory` (required): Directory containing subscription files

**Options**:
- `--redis-url <url>`: Redis connection URL (default: `redis://localhost:6379/0`)
- `--output-dir <dir>`: Directory for file exports (default: `./output`)
- `--format <format>`: Export format - `json`, `csv`, or `both` (default: `both`)
- `--pattern <glob>`: File pattern to match (default: `*`)
- `--recursive`, `-r`: Process subdirectories recursively
- `--no-redis`: Skip Redis storage
- `--no-export`: Skip file export
- `--parallel <n>`: Number of parallel workers (default: 1)
- `--verbose`, `-v`: Enable debug logging
- `--quiet`, `-q`: Suppress progress output

**Exit Codes**:
- `0`: Success (at least one file processed successfully)
- `1`: Directory not found or permission error
- `2`: All files failed to parse
- `3`: Redis connection error
- `4`: File export error

**Output** (stdout with progress bar):
```
Processing directory: /data/subscriptions
Files found: 25

Processing: 100%|████████████████████| 25/25 [00:32<00:00,  1.28s/file]

Summary:
  Total files: 25
  Successful: 23
  Failed: 2
  Total nodes: 3,450
  Successfully parsed: 3,398
  Failed nodes: 52
  Duration: 32.5s

Stored in Redis: 23 subscriptions
Exported to: ./output/ (46 files)

Failed files:
  - corrupted_file.txt: Invalid format
  - empty_file.txt: No nodes found
```

**Example Usage**:
```bash
# Process all files in directory
subscription-parser batch /data/subscriptions

# Process only .txt files recursively
subscription-parser batch /data/subscriptions --pattern "*.txt" --recursive

# Parallel processing with 4 workers
subscription-parser batch /data/subscriptions --parallel 4

# Quiet mode (no progress bar)
subscription-parser batch /data/subscriptions --quiet
```

### 3. export - Export from Redis

**Syntax**:
```bash
subscription-parser export <source_id> [options]
```

**Arguments**:
- `source_id` (required): Subscription source identifier

**Options**:
- `--redis-url <url>`: Redis connection URL (default: `redis://localhost:6379/0`)
- `--output <file>`: Output file path (required)
- `--format <format>`: Export format - `json` or `csv` (required)
- `--verbose`, `-v`: Enable debug logging

**Exit Codes**:
- `0`: Success
- `1`: Source not found in Redis
- `2`: Output file write error
- `3`: Redis connection error

**Output** (stdout):
```
Exporting: subscription:my_subscription
Nodes found: 148
Exported to: /data/exports/my_subscription.json
```

**Example Usage**:
```bash
# Export to JSON
subscription-parser export my_subscription --output /data/exports/my_subscription.json --format json

# Export to CSV
subscription-parser export my_subscription --output /data/exports/my_subscription.csv --format csv
```

### 4. list - List Subscriptions in Redis

**Syntax**:
```bash
subscription-parser list [options]
```

**Options**:
- `--redis-url <url>`: Redis connection URL (default: `redis://localhost:6379/0`)
- `--verbose`, `-v`: Show detailed information

**Exit Codes**:
- `0`: Success
- `3`: Redis connection error

**Output** (stdout):
```
Subscriptions in Redis:

source_id              nodes  parsed_at            ttl
─────────────────────  ─────  ───────────────────  ─────────
subscription_2024      148    2026-03-05 10:30:00  6d 23h
another_subscription   95     2026-03-04 15:20:00  5d 18h
test_subscription      12     2026-03-05 09:00:00  6d 22h

Total: 3 subscriptions, 255 nodes
```

**Example Usage**:
```bash
# List all subscriptions
subscription-parser list

# Verbose mode with full details
subscription-parser list --verbose
```

### 5. info - Show Subscription Details

**Syntax**:
```bash
subscription-parser info <source_id> [options]
```

**Arguments**:
- `source_id` (required): Subscription source identifier

**Options**:
- `--redis-url <url>`: Redis connection URL (default: `redis://localhost:6379/0`)
- `--show-nodes`: Display all node details

**Exit Codes**:
- `0`: Success
- `1`: Source not found in Redis
- `3`: Redis connection error

**Output** (stdout):
```
Subscription: subscription_2024

Metadata:
  Source ID: subscription_2024
  File Path: /data/subscriptions/subscription_2024.txt
  Format: base64
  Total Nodes: 150
  Successful: 148
  Failed: 2
  Parsed At: 2026-03-05 10:30:00
  Duration: 1.25s
  TTL: 6 days 23 hours

Protocol Distribution:
  vmess: 85 (57%)
  ss: 40 (27%)
  trojan: 15 (10%)
  vless: 8 (5%)

Errors:
  - Line 45: Invalid vmess URI - missing uuid
  - Line 89: Unknown protocol 'socks5'
```

**Example Usage**:
```bash
# Show subscription info
subscription-parser info subscription_2024

# Show with all node details
subscription-parser info subscription_2024 --show-nodes
```

### 6. version - Show Version Information

**Syntax**:
```bash
subscription-parser version
```

**Output** (stdout):
```
subscription-parser version 1.0.0
Python 3.12.0
Redis client: redis-py 5.0.0
```

### 7. help - Show Help Information

**Syntax**:
```bash
subscription-parser help [command]
```

**Arguments**:
- `command` (optional): Show help for specific command

**Output**: Displays usage information and available commands

## Global Options

Available for all commands:

- `--help`, `-h`: Show help message
- `--version`: Show version information

## Environment Variables

- `REDIS_URL`: Default Redis connection URL (overridden by `--redis-url`)
- `SUBSCRIPTION_PARSER_OUTPUT_DIR`: Default output directory (overridden by `--output-dir`)
- `SUBSCRIPTION_PARSER_LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR)

## Configuration File

Optional configuration file: `~/.subscription-parser.yaml`

```yaml
redis:
  url: redis://localhost:6379/0
  timeout: 5

output:
  directory: ./output
  format: both  # json, csv, or both

logging:
  level: INFO
  file: ~/.subscription-parser.log

parsing:
  retry_attempts: 3
  retry_backoff: exponential
```

## Error Messages

### Common Errors

**File Not Found**:
```
Error: File not found: /path/to/file.txt
```

**Permission Denied**:
```
Error: Permission denied: /path/to/file.txt
```

**Redis Connection Failed**:
```
Error: Failed to connect to Redis at redis://localhost:6379
Retrying (1/3)...
```

**Invalid Format**:
```
Warning: Could not detect format for file: /path/to/file.txt
Tried: base64, yaml, mixed
Skipping file.
```

**Parsing Errors**:
```
Warning: Failed to parse node at line 45: Invalid vmess URI - missing uuid
Continuing with remaining nodes...
```

## Output File Formats

### JSON Export Format

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
  ],
  "export_format": "json",
  "exported_at": "2026-03-05T10:31:00Z"
}
```

### CSV Export Format

```csv
node_id,protocol,host,port,tls,sni,uuid,password,cipher,transport,network,auth_protocol,obfuscation,remarks,source_id,parsed_at
a1b2c3d4e5f6...,vmess,example.com,443,true,example.com,12345678-1234-1234-1234-123456789012,,auto,ws,tcp,,,US Server 1,subscription_2024,2026-03-05T10:30:00Z
b2c3d4e5f6a7...,ss,192.168.1.100,8388,false,,,mypassword,aes-256-gcm,tcp,tcp,,,HK Server,subscription_2024,2026-03-05T10:30:00Z
```

## Logging Format

**Console Output** (INFO level):
```
2026-03-05 10:30:00 | INFO | Parsing file: /data/subscriptions/subscription_2024.txt
2026-03-05 10:30:01 | INFO | Format detected: base64
2026-03-05 10:30:01 | INFO | Found 150 nodes
2026-03-05 10:30:01 | WARNING | Failed to parse node at line 45: Invalid vmess URI
2026-03-05 10:30:01 | INFO | Successfully parsed 148 nodes
2026-03-05 10:30:01 | INFO | Stored in Redis: subscription:subscription_2024
2026-03-05 10:30:01 | INFO | Exported to: ./output/subscription_2024.json
```

**File Log** (DEBUG level):
```
2026-03-05 10:30:00.123 | DEBUG | parser.py:45 | Starting parse operation
2026-03-05 10:30:00.125 | DEBUG | decoder.py:23 | Attempting base64 decode
2026-03-05 10:30:00.130 | DEBUG | decoder.py:28 | Base64 decode successful
2026-03-05 10:30:00.135 | DEBUG | parser.py:67 | Extracted 150 URIs
2026-03-05 10:30:00.140 | DEBUG | vmess_parser.py:12 | Parsing vmess URI
...
```

## Performance Expectations

Based on success criteria from spec.md:

- Single file (100 nodes): < 5 seconds
- Batch (100 files): < 5 minutes
- Error response: < 1 second
- Format recognition: 95%+ accuracy
- Field extraction: 98%+ accuracy

## Backward Compatibility

This is version 1.0.0 - no backward compatibility concerns.

Future versions will follow semantic versioning:
- MAJOR: Breaking CLI changes
- MINOR: New commands/options (backward compatible)
- PATCH: Bug fixes

## Security Considerations

- File paths are validated to prevent directory traversal
- Redis credentials should not be logged
- Exported files inherit permissions from output directory
- No sensitive data (passwords, UUIDs) logged at INFO level
