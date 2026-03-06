# Feature Specification: 订阅解析器 (Subscription Parser)

**Feature Branch**: `001-subscription-parser`
**Created**: 2026-03-05
**Status**: Draft
**Input**: User description: "我会将其他团队从流量中得到的订阅保存起来，然后解析他们。这些订阅可能是clash订阅，也可能是其他订阅。内容可能是全部base64编码的字符串，也可能是clash的yml的明文，也可能是部分base64编码的字符串。协议的类型会是如下几种ss、ssr、trojan、vmess、vless、hysteria、hysteria2。我需要从订阅节点中解析出ip、port、domain、是否使用tls、sni、uuid、传输层协议、应用层协议、cipher、password、authprotocol、obfuscation等。"

## Clarifications

### Session 2026-03-05

- Q: Should the parser store results in Redis, or only export to JSON/CSV files? → A: Both Redis and file export are required outputs
- Q: What Redis data structure should be used to store parsed subscription nodes? → A: Hash per node with set index
- Q: How should node_id be generated to ensure uniqueness? → A: Hash of node attributes (deterministic, enables deduplication)
- Q: Should parsed node data in Redis have an expiration policy? → A: TTL of 7 days
- Q: How should source_id be determined for each subscription file? → A: Filename without extension

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 解析单个订阅文件 (Priority: P1)

作为数据分析人员，我需要能够读取从流量中获取的订阅文件，并将其中的节点信息提取出来，以便进行后续的数据分析和处理。

**Why this priority**: 这是核心功能，没有解析能力就无法进行任何后续工作。这是最小可用产品(MVP)的基础。

**Independent Test**: 提供一个包含多个节点的订阅文件（任意格式），系统能够成功解析并输出所有节点的完整信息。

**Acceptance Scenarios**:

1. **Given** 一个完全base64编码的订阅文件，**When** 用户提供该文件进行解析，**Then** 系统自动检测编码格式，解码后提取所有节点信息
2. **Given** 一个Clash YAML明文订阅文件，**When** 用户提供该文件进行解析，**Then** 系统识别YAML格式并提取所有节点信息
3. **Given** 一个部分base64编码的混合格式订阅文件，**When** 用户提供该文件进行解析，**Then** 系统能够处理混合格式并提取所有节点信息
4. **Given** 一个包含ss协议节点的订阅，**When** 解析完成，**Then** 输出包含ip、port、cipher、password等完整信息
5. **Given** 一个包含vmess协议节点的订阅，**When** 解析完成，**Then** 输出包含domain、port、uuid、传输层协议、应用层协议、tls、sni等完整信息

---

### User Story 2 - 批量处理多个订阅文件 (Priority: P2)

作为数据分析人员，我需要能够一次性处理多个订阅文件，提高工作效率，避免重复手动操作。

**Why this priority**: 在实际工作中，经常需要处理大量订阅文件。批量处理能显著提升工作效率。

**Independent Test**: 提供包含10个不同格式订阅文件的目录，系统能够自动遍历并解析所有文件，生成统一的输出结果。

**Acceptance Scenarios**:

1. **Given** 一个包含多个订阅文件的目录，**When** 用户指定该目录进行批量解析，**Then** 系统遍历所有文件并生成汇总结果
2. **Given** 批量处理过程中某个文件解析失败，**When** 继续处理其他文件，**Then** 系统记录失败文件信息但不中断整体流程
3. **Given** 批量处理大量文件，**When** 处理进行中，**Then** 系统显示实时进度信息

---

### User Story 3 - 导出结构化数据 (Priority: P3)

作为数据分析人员，我需要将解析后的节点信息导出为结构化格式（如JSON、CSV），以便与其他数据分析工具集成。

**Why this priority**: 导出功能使解析结果能够被其他系统使用，提升数据流转效率。

**Independent Test**: 解析订阅文件后，能够将结果导出为JSON和CSV两种格式，且数据完整准确。

**Acceptance Scenarios**:

1. **Given** 已解析的节点数据，**When** 用户选择导出为JSON格式，**Then** 生成符合JSON规范的结构化文件
2. **Given** 已解析的节点数据，**When** 用户选择导出为CSV格式，**Then** 生成包含所有字段的CSV文件，便于Excel打开
3. **Given** 导出的数据文件，**When** 使用其他工具读取，**Then** 所有字段信息完整且格式正确

---

### Edge Cases

- 订阅文件为空或格式完全无法识别时，系统如何处理？
- 订阅文件中包含损坏或不完整的节点信息时，如何处理？
- 遇到未知的协议类型（不在ss、ssr、trojan、vmess、vless、hysteria、hysteria2范围内）时，如何处理？
- base64解码失败时，如何处理？
- YAML解析失败时，如何处理？
- 节点信息缺少必需字段（如ip/domain、port）时，如何处理？
- 文件编码不是UTF-8时，如何处理？
- 订阅文件过大（如超过100MB）时，如何处理？
- Redis连接失败或超时时，系统如何处理？
- Redis存储空间不足时，如何处理？

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 系统必须能够自动检测订阅文件的编码格式（完全base64、明文YAML、部分base64混合）
- **FR-002**: 系统必须使用文件名（不含扩展名）作为订阅源标识（source_id），用于在Redis中组织和索引节点数据
- **FR-003**: 系统必须支持解析以下协议类型的节点：ss、ssr、trojan、vmess、vless、hysteria、hysteria2
- **FR-004**: 系统必须从每个节点中提取以下信息：
  - 网络地址：ip、port、domain
  - 安全配置：是否使用tls、sni
  - 认证信息：uuid、password
  - 协议参数：传输层协议、应用层协议、cipher、authprotocol、obfuscation
- **FR-005**: 系统必须在解析失败时提供清晰的错误信息，包括失败原因和失败位置（文件名、行号等）
- **FR-006**: 系统必须支持批量处理多个订阅文件，并在处理过程中显示实时进度
- **FR-007**: 系统必须在遇到单个节点解析失败时继续处理其他节点，不中断整体流程
- **FR-008**: 系统必须将解析结果同时保存到Redis和文件系统，支持JSON和CSV格式导出
- **FR-009**: 系统必须将解析后的节点数据存储到Redis（版本5.0+）中，使用以下数据结构：
  - 每个节点存储为独立的Hash：`node:{node_id}`，包含所有提取的字段
  - node_id通过对节点关键属性（ip/domain + port + protocol）进行哈希生成，确保相同节点具有相同ID，实现自动去重
  - 每个订阅源维护一个Set索引：`subscription:{source_id}:nodes`，包含该订阅的所有节点ID
  - 所有Redis键设置7天TTL（过期时间），自动清理过期数据，防止内存无限增长
  - 支持通过订阅源快速查询所有相关节点
- **FR-010**: 系统必须记录详细的处理日志，包括：处理的文件数量、成功/失败的节点数量、错误详情、处理耗时
- **FR-011**: 系统必须在处理完成或异常退出时正确释放所有资源（文件句柄、内存、Redis连接等）
- **FR-012**: 系统必须对解析过程中的异常情况进行容错处理，包括：文件读取失败、编码错误、格式错误、字段缺失、Redis连接失败
- **FR-013**: 系统必须在解析失败时自动重试最多3次，并在第3次失败时保存错误上下文信息到日志文件

### Key Entities

- **订阅文件 (Subscription File)**: 从流量中获取的原始订阅数据，可能是base64编码、YAML明文或混合格式。使用文件名（不含扩展名）作为唯一的source_id标识
- **节点 (Node/Proxy)**: 订阅文件中的单个代理服务器配置，包含协议类型和连接参数。每个节点通过其关键属性（ip/domain + port + protocol）的哈希值生成唯一的node_id，相同配置的节点将自动去重
- **解析结果 (Parsed Result)**: 从节点中提取的结构化信息，包含所有必需和可选字段
- **协议配置 (Protocol Config)**: 特定协议类型的参数集合，不同协议有不同的必需字段
- **Redis存储结构**:
  - `node:{node_id}` - Hash类型，存储单个节点的所有字段（node_id为节点关键属性的哈希值），TTL为7天
  - `subscription:{source_id}:nodes` - Set类型，存储订阅源的所有节点ID索引，TTL为7天

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 系统能够正确解析95%以上的常见订阅格式（base64、YAML、混合格式）
- **SC-002**: 单个订阅文件（包含100个节点）的解析时间不超过5秒
- **SC-003**: 批量处理100个订阅文件时，系统能够在5分钟内完成处理
- **SC-004**: 解析准确率达到98%以上（正确提取所有必需字段）
- **SC-005**: 系统在遇到格式错误时，能够在1秒内返回清晰的错误信息
- **SC-006**: 导出的JSON和CSV文件能够被标准工具（如jq、Excel）正确读取
- **SC-007**: 日志信息完整记录所有关键操作，便于问题追溯和性能分析

## Assumptions

- 订阅文件来源可信，不需要进行安全扫描或恶意代码检测
- 订阅文件大小通常在10MB以内，极端情况不超过100MB
- 节点信息不涉及敏感个人数据，无需进行脱敏处理（如果包含用户ID等信息，需在后续存储时处理）
- 解析工具主要用于内部数据分析，不需要提供Web界面或API接口
- 文件编码默认为UTF-8，如遇其他编码会尝试自动检测
- Redis服务已部署并可访问，版本为5.0或更高
- 解析结果需要同时存储到Redis和导出为文件，以支持不同的使用场景
