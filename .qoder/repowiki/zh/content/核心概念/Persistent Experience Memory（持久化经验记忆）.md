# 持久化经验记忆（Persistent Experience Memory）

<cite>
**本文引用的文件**   
- [README.md](file://README.md)
- [README_CN.md](file://README_CN.md)
- [memory_store.py](file://cloud/storage/memory_store.py)
- [sqlite_memory_store.py](file://cloud/storage/sqlite_memory_store.py)
- [scoring_backend.py](file://cloud/storage/scoring_backend.py)
- [scoring.py](file://cnaa/scoring.py)
- [scoring_algorithms.py](file://cnaa/scoring_algorithms.py)
- [interaction.py](file://cnaa/interaction.py)
- [models.py](file://cnaa/models.py)
- [test_scoring_system.py](file://tests/test_scoring_system.py)
- [memory_scoring_demo.py](file://examples/memory_scoring_demo.py)
</cite>

## 更新摘要
**所做更改**   
- 移除了旧的本地评分器实现，采用全新的分布式评分架构
- 新增了完整的评分后端系统，支持增量更新和批量处理
- 增强了内存存储的评分集成能力
- 添加了详细的评分算法实现和多维度评分机制
- 扩展了API使用示例以反映新的分布式评分功能
- 更新了数据模型和接口规范说明

## 目录
1. [引言](#引言)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构总览](#架构总览)
5. [详细组件分析](#详细组件分析)
6. [依赖分析](#依赖分析)
7. [性能考虑](#性能考虑)
8. [故障排查指南](#故障排查指南)
9. [结论](#结论)
10. [附录](#附录)

## 引言
本文件面向"持久化经验记忆"这一主题，基于仓库提供的概念与架构说明，系统化阐述：
- 持久化记忆与传统内存系统的本质区别
- 如何将 AI Agent 的经验从临时上下文转换为可持久化的运行时资源
- 经验数据的结构定义、存储格式、版本控制机制
- 经验的序列化/反序列化过程与数据一致性保证
- 经验检索算法、缓存策略、备份恢复机制
- 数据模型示例与 API 使用示例
- 与不同存储后端的集成方式与配置选项

需要特别说明的是：当前仓库为概念性文档仓库，未包含具体实现代码。因此，本节内容以仓库中明确提出的"Experience Runtime"和"Persistent Memory"为核心，结合通用工程实践给出可落地的设计与建议，便于后续在真实工程中落地实施。

**章节来源**
- [README.md:9-41](file://README.md#L9-L41)
- [README_CN.md:9-49](file://README_CN.md#L9-L49)

## 项目结构
仓库目前包含中英文 README 以及空的 docs 目录，表明该项目处于早期规划阶段，重点在于理念与架构方向。根据 README 中的架构图，系统由三层组成：
- AI Agent：业务智能体，不直接管理记忆，仅通过运行时接口交互
- Experience Runtime SDK：提供状态接口、记忆管理、任务生命周期、Agent 适配等能力
- CNAA State Service：作为统一的状态服务，对外暴露 MCP / HTTP 接口，负责持久化与同步

```mermaid
graph TB
subgraph "AI Agent"
A["AI Agent"]
end
subgraph "Experience Runtime SDK"
R1["状态接口"]
R2["记忆管理器"]
R3["任务生命周期"]
R4["Agent 适配器"]
end
subgraph "CNAA State Service"
S1["MCP / HTTP 接口"]
S2["持久化存储"]
end
A --> R1
R1 --> R2
R2 --> R3
R3 --> R4
R4 --> S1
S1 --> S2
```

**图表来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

**章节来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

## 核心组件
根据 README 的架构描述，核心组件包括：
- 状态接口（State Interface）：统一的读写抽象，屏蔽底层存储差异
- 记忆管理器（Memory Manager）：负责经验的增删改查、版本管理、序列化/反序列化
- 任务生命周期（Task Lifecycle）：将经验与任务阶段绑定，确保经验沉淀时机正确
- Agent 适配器（Agent Adapter）：解耦不同 Agent 的实现细节，提供统一接入点
- 状态服务（State Service）：对外提供 MCP / HTTP 接口，承载并发访问与一致性保障

这些组件共同构成"经验运行时"，使经验成为独立于 Agent 推理过程的运行时资源。

**章节来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

## 架构总览
下图展示了从 Agent 到持久化存储的整体调用链，强调"经验运行时"作为中间层的作用。

```mermaid
sequenceDiagram
participant Agent as "AI Agent"
participant Runtime as "Experience Runtime SDK"
participant Service as "CNAA State Service"
participant Store as "持久化存储"
Agent->>Runtime : "记录经验(任务ID, 片段, 元数据)"
Runtime->>Runtime : "序列化与校验"
Runtime->>Service : "POST /experience (JSON)"
Service->>Store : "写入并生成版本号"
Store-->>Service : "确认写入成功"
Service-->>Runtime : "返回经验ID与版本"
Runtime-->>Agent : "返回操作结果"
```

**图表来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

## 详细组件分析

### 经验数据结构与版本控制
- 经验实体建议包含以下字段：
  - 经验ID：唯一标识
  - 任务ID：关联的任务或会话
  - 片段内容：结构化或半结构化的经验片段
  - 元数据：标签、权重、来源、时间戳、有效性区间等
  - 版本：每次更新递增的版本号，支持回滚与对比
- 版本控制机制：
  - 写时复制（Copy-on-Write）：每次更新生成新版本，保留历史
  - 合并策略：多源经验合并时采用冲突检测与优先级规则
  - 快照与差分：定期生成快照，增量更新差分，降低存储压力

```mermaid
classDiagram
class Experience {
+string id
+string taskId
+object content
+map metadata
+int version
+timestamp createdAt
+timestamp updatedAt
}
class VersionedStore {
+write(experience) Experience
+read(id, version?) Experience
+list(taskId, filters) Experience[]
+snapshot() string
+restore(snapshotId) bool
}
Experience <.. VersionedStore : "持久化"
```

**图表来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

**章节来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

### 分布式评分架构详解

#### 评分后端系统（MemoryScoringBackend）
新的分布式评分架构提供了强大的评分计算和存储能力：

**核心特性：**
- **增量评分更新**：无需重新计算所有分数，支持高效更新
- **多维度评分**：时效性、完成度、重要性、频率、相关性五个维度
- **批量处理能力**：支持大规模记忆的批量评分
- **上下文感知**：基于当前上下文的智能相关性评分
- **可配置权重**：支持按Agent自定义评分权重

```mermaid
flowchart TD
ScoreRequest["评分请求"] --> Calculate["计算各维度分数"]
Calculate --> Recency["时效性评分"]
Calculate --> Completion["完成度评分"]
Calculate --> Importance["重要性评分"]
Calculate --> Frequency["频率评分"]
Calculate --> Relevance["相关性评分"]
Recency --> Composite["综合评分计算"]
Completion --> Composite
Importance --> Composite
Frequency --> Composite
Relevance --> Composite
Composite --> Store["存储评分结果"]
Store --> Return["返回评分结果"]
```

**图表来源**
- [scoring_backend.py:35-75](file://cloud/storage/scoring_backend.py#L35-L75)

**章节来源**
- [scoring_backend.py:23-75](file://cloud/storage/scoring_backend.py#L23-L75)

#### 评分算法实现
评分系统实现了多种专业的评分算法：

**时效性评分（RecencyScorer）：**
- 指数衰减算法：score = 2^(-t/half_life)
- 支持线性衰减模式
- 默认半衰期为7天

**完成度评分（CompletionScorer）：**
- 基于Agent提供的完成度分数
- 关键词增强：success、completed等关键词提升分数
- 内容分析：自动识别完成状态

**重要性评分（ImportanceScorer）：**
- 关键词匹配：critical、important、urgent等高优先级词汇
- 多级权重：从高到低分为多个等级
- 显式字段融合：支持用户指定的重要性值

**频率评分（FrequencyScorer）：**
- 对数缩放：避免高频访问导致分数过高
- 时间窗口：支持指定回溯期（默认7天）
- 速率计算：基于访问频率的动态评分

**相关性评分（RelevanceScorer）：**
- 关键词匹配：Jaccard相似度算法
- 上下文匹配：基于当前上下文的智能匹配
- 标签加权：标签匹配给予额外权重

**章节来源**
- [scoring_algorithms.py:27-397](file://cnaa/scoring_algorithms.py#L27-L397)

#### 评分数据模型
评分系统定义了完整的数据结构：

**MemoryScores类：**
- 包含五个维度的评分分数
- 支持复合分数计算
- 提供序列化和反序列化功能
- 支持自定义权重配置

**ScoreRanking类：**
- 按复合分数排序的记忆列表
- 支持Top-N查询
- 提供统计信息（平均分数、总数等）

**ScoreThresholds类：**
- 配置过滤阈值
- 支持多维度阈值设置
- 提供包含判断逻辑

**章节来源**
- [scoring.py:21-181](file://cnaa/scoring.py#L21-L181)

### 内存存储实现详解

#### InMemoryMemoryStore 增强功能
InMemoryMemoryStore 类提供了增强的内存存储功能，支持时间范围过滤、分页和高级查询：

**新增功能特性：**
- **时间范围过滤**：支持 `start_time` 和 `end_time` 参数进行精确的时间段查询
- **分页支持**：通过 `limit` 参数控制返回结果数量
- **排序控制**：`reverse` 参数支持按时间倒序或正序排列
- **多条件过滤**：支持类型过滤、标签过滤和时间范围过滤的组合查询
- **评分集成**：预留评分系统集成接口

```mermaid
flowchart TD
Query["查询请求"] --> Auth["认证检查"]
Auth --> FilterType{"类型过滤?"}
FilterType --> |是| TypeFilter["应用类型过滤"]
FilterType --> |否| FilterTags{"标签过滤?"}
TypeFilter --> FilterTags
FilterTags --> |是| TagFilter["应用标签过滤"]
FilterTags --> |否| FilterTime{"时间范围过滤?"}
TagFilter --> FilterTime
FilterTime --> |是| TimeFilter["应用时间范围过滤"]
FilterTime --> |否| Sort["排序处理"]
TimeFilter --> Sort
Sort --> Limit{"有分页限制?"}
Limit --> |是| ApplyLimit["应用分页限制"]
Limit --> |否| Return["返回结果"]
ApplyLimit --> Return
```

**图表来源**
- [memory_store.py:77-155](file://cloud/storage/memory_store.py#L77-L155)

**章节来源**
- [memory_store.py:77-155](file://cloud/storage/memory_store.py#L77-L155)

#### SQLite 存储后端
SQLiteMemoryStore 提供了轻量级的持久化存储解决方案：

**数据库设计：**
- 单文件存储，适合开发和测试环境
- 自动创建索引优化查询性能
- WAL模式启用以提高并发性能
- JSON序列化处理复杂数据类型

**查询优化：**
- 基于agent_id的复合索引
- 时间戳索引支持高效时间范围查询
- 类型索引加速类型过滤

**章节来源**
- [sqlite_memory_store.py:19-62](file://cloud/storage/sqlite_memory_store.py#L19-L62)
- [sqlite_memory_store.py:121-171](file://cloud/storage/sqlite_memory_store.py#L121-L171)

### 序列化与反序列化
- 序列化目标：
  - 跨语言兼容（如 JSON、Protocol Buffers）
  - 压缩与加密（可选）
  - 元数据与内容分离，便于索引与检索
- 反序列化流程：
  - 校验版本与完整性
  - 按需加载字段（懒加载）
  - 转换为目标对象并缓存热点数据

```mermaid
flowchart TD
Start(["开始"]) --> Serialize["序列化经验对象"]
Serialize --> Validate{"校验通过?"}
Validate --> |否| Error["抛出序列化错误"]
Validate --> |是| Write["写入存储"]
Write --> End(["结束"])
```

**图表来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

**章节来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

### 数据一致性保证
- 事务性写入：确保经验写入原子性，失败回滚
- 幂等接口：同一请求多次执行结果一致
- 冲突检测：多副本或多进程写入时检测并解决冲突
- 最终一致性：允许短暂不一致，但保证最终收敛

```mermaid
flowchart TD
Begin(["写入请求"]) --> Check["检查幂等键"]
Check --> Exists{"已存在?"}
Exists --> |是| Return["返回已有结果"]
Exists --> |否| TxBegin["开启事务"]
TxBegin --> Write["写入主存储"]
Write --> Sync["同步副本/索引"]
Sync --> Commit{"提交成功?"}
Commit --> |否| Rollback["回滚事务"]
Commit --> |是| TxEnd["结束事务"]
TxEnd --> Return
```

**图表来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

**章节来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

### 经验检索算法与缓存策略
- 检索算法：
  - 关键词匹配：基于标签与元数据快速过滤
  - 语义检索：向量相似度匹配（可选）
  - 时间窗口：按创建时间或有效期筛选
- 缓存策略：
  - LRU/LFU 缓存热点经验
  - 多级缓存：本地内存 + 分布式缓存
  - 预取策略：基于任务上下文预测可能需要的经验

```mermaid
flowchart TD
Query["检索请求"] --> Filter["元数据过滤"]
Filter --> Rank["排序与评分"]
Rank --> CacheHit{"命中缓存?"}
CacheHit --> |是| ReturnCache["返回缓存结果"]
CacheHit --> |否| Fetch["查询存储"]
Fetch --> UpdateCache["更新缓存"]
UpdateCache --> Return["返回结果"]
```

**图表来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

**章节来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

### 备份与恢复机制
- 备份：
  - 全量快照：定期导出完整状态
  - 增量备份：仅备份变更部分
- 恢复：
  - 选择时间点恢复
  - 校验数据完整性
  - 灰度切换至新状态

```mermaid
flowchart TD
BackupStart["开始备份"] --> Snapshot["生成快照"]
Snapshot --> Compress["压缩与加密"]
Compress --> Upload["上传至备份存储"]
Upload --> Verify["校验完整性"]
Verify --> BackupEnd["备份完成"]
RestoreStart["开始恢复"] --> Select["选择恢复点"]
Select --> Download["下载快照"]
Download --> Decrypt["解密与解压"]
Decrypt --> Apply["应用状态"]
Apply --> VerifyRestore["验证一致性"]
VerifyRestore --> RestoreEnd["恢复完成"]
```

**图表来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

**章节来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

### API 使用示例（概念性）
- 记录经验：
  - POST /experience
  - 请求体：{taskId, content, metadata}
  - 响应：{id, version}
- 读取经验：
  - GET /experience/{id}?version={n}
  - 响应：经验对象或空
- 列出经验（增强版）：
  - GET /experiences?taskId={id}&filters={...}
  - 支持参数：
    - memory_type: 经验类型过滤
    - tags: 标签数组过滤
    - start_time: 起始时间（ISO格式）
    - end_time: 结束时间（ISO格式）
    - limit: 返回数量限制
    - reverse: 是否倒序排列
  - 响应：经验列表

**章节来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

### 与不同存储后端的集成

#### 内存存储后端（InMemoryMemoryStore）
适用于开发、测试和临时场景：
- 零配置启动
- O(1) 查找复杂度
- 内存占用随数据量线性增长
- 不支持持久化

#### SQLite 存储后端（SQLiteMemoryStore）
适用于单机部署和生产环境：
- 单文件数据库，易于部署
- 支持并发读写（WAL模式）
- 自动索引优化查询性能
- 支持SQL查询语法

#### 配置选项建议：
- 连接池大小
- 超时与重试策略
- 加密与压缩开关
- 分片与副本策略

**章节来源**
- [memory_store.py:17-31](file://cloud/storage/memory_store.py#L17-L31)
- [sqlite_memory_store.py:19-31](file://cloud/storage/sqlite_memory_store.py#L19-L31)

## 依赖分析
- 内部依赖：
  - Experience Runtime SDK 依赖状态接口与记忆管理器
  - 记忆管理器依赖序列化器与版本控制器
- 外部依赖：
  - CNAA State Service 依赖存储后端（数据库、对象存储等）
  - 网络协议（MCP/HTTP）用于跨进程通信

```mermaid
graph LR
Agent["AI Agent"] --> Runtime["Experience Runtime SDK"]
Runtime --> Interface["状态接口"]
Runtime --> Manager["记忆管理器"]
Manager --> Serializer["序列化器"]
Manager --> Versioner["版本控制器"]
Runtime --> Service["CNAA State Service"]
Service --> Storage["持久化存储"]
```

**图表来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

**章节来源**
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-80)

## 性能考虑
- 读写分离：读多写少场景下，使用只读副本提升吞吐
- 批量操作：合并小写入，减少 I/O 次数
- 异步处理：非关键路径操作异步化，降低延迟
- 缓存命中率：优化缓存键与过期策略，提升命中率
- 索引优化：针对高频查询字段建立合适索引
- **时间范围查询优化**：利用时间戳索引加速时间段查询
- **分页查询优化**：避免大结果集传输，提升响应速度
- **评分计算优化**：增量更新而非全量重算，支持批量处理

[本节为通用性能建议，无需特定文件引用]

## 故障排查指南
- 常见问题：
  - 序列化失败：检查字段类型与版本兼容性
  - 写入冲突：查看并发写入日志与锁机制
  - 缓存不一致：清理缓存并重新加载
  - 备份恢复失败：校验备份文件完整性与权限
  - **时间范围查询无结果**：检查时间戳格式和时区设置
  - **分页查询异常**：验证limit参数范围和排序逻辑
  - **评分计算异常**：检查评分权重配置和数据完整性
  - **分布式评分同步问题**：验证评分后端连接和状态同步
- 诊断工具：
  - 启用详细日志
  - 监控关键指标（QPS、延迟、错误率）
  - 健康检查接口

[本节为通用故障排查建议，无需特定文件引用]

## 结论
CNAA 提出的"持久化经验记忆"将经验从临时上下文提升为独立运行时资源，通过 Experience Runtime SDK 与 CNAA State Service 的协作，实现了经验的持续积累、同步与复用。最新的分布式评分架构进一步增强了系统的智能化水平，通过多维度评分算法和增量更新机制，为经验的选择和重用提供了强有力的技术支持。

**重要更新**：新的分布式评分架构完全替代了旧的本地评分器，提供了更强大、更灵活的评分能力。评分系统支持五种不同的评分维度，能够综合考虑时效性、完成度、重要性、频率和相关性，为AI Agent提供更智能的经验推荐。

[本节为总结性内容，无需特定文件引用]

## 附录
- 术语表：
  - 经验（Experience）：任务执行过程中产生的可复用知识
  - 运行时（Runtime）：支撑经验管理的执行环境
  - 状态服务（State Service）：提供统一状态访问的后端服务
  - 时间范围过滤：基于时间戳的精确时间段查询
  - 分页查询：控制结果集大小的查询优化技术
  - 分布式评分：基于多维度的智能评分系统
  - 增量更新：高效的评分更新机制
- 参考链接：
  - [README.md](file://README.md)
  - [README_CN.md](file://README_CN.md)

[本节为补充信息，无需特定文件引用]