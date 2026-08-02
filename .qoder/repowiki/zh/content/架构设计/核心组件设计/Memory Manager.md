# Memory Manager 详细文档

<cite>
**本文档中引用的文件**
- [README.md](file://README.md)
- [README_CN.md](file://README_CN.md)
- [slicer.py](file://local/memory/slicer.py)
- [scoring_algorithms.py](file://cnaa/scoring_algorithms.py)
- [scoring_backend.py](file://cloud/storage/scoring_backend.py)
- [lifecycle.py](file://cnaa/lifecycle.py)
- [models.py](file://cnaa/models.py)
- [memory_slicing_example.py](file://examples/memory_slicing_example.py)
- [test_memory_slicing.py](file://tests/test_memory_slicing.py)
</cite>

## 更新摘要
**所做更改**
- 新增内存切片基础设施章节，详细介绍 SimpleMemorySlicer 和知识压缩功能
- 更新评分系统架构，集成 CompositeScorer 和 MemoryScoringBackend
- 增强生命周期管理，添加 SimpleTimeBasedCondensationPlugin
- 扩展存储后端抽象，支持智能评分和索引优化
- 新增配置示例和性能调优建议，包含切片策略和评分权重配置

## 目录
1. [简介](#简介)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构总览](#架构总览)
5. [详细组件分析](#详细组件分析)
6. [依赖关系分析](#依赖关系分析)
7. [性能考量](#性能考量)
8. [故障排查指南](#故障排查指南)
9. [结论](#结论)
10. [附录](#附录)

## 简介
本文件围绕 CNAA 中的 Memory Manager（记忆管理）进行系统化说明，聚焦以下目标：
- 持久化记忆管理的核心算法、存储策略与缓存机制
- **新增**：智能内存切片基础设施，支持时间序列分割和标签提取
- 经验数据的组织结构、索引设计与检索优化
- 数据版本控制、增量更新与冲突解决策略
- 存储后端抽象接口设计，支持多种数据库与文件系统实现
- **新增**：多维度评分系统和知识压缩机制
- 内存缓存策略、数据压缩与传输优化技术
- 数据迁移工具、备份恢复机制与监控指标
- 配置示例与性能调优建议

CNAA 定位为"面向 AI Agent 的持久化记忆运行时框架"，强调将"经验"沉淀为独立于 Prompt 的持久资源，并通过统一的 State Interface 暴露给上层 Experience Runtime SDK。

章节来源
- [README.md:11-41](file://README.md#L11-L41)
- [README_CN.md:11-49](file://README_CN.md#L11-L49)

## 项目结构
当前仓库以 README 为主，docs 目录为空，表明该项目处于早期规划阶段。从架构描述可知，Memory Manager 位于 Experience Runtime SDK 内部，向上对接 Agent，向下通过 MCP/HTTP 访问 CNAA State Service，负责经验的持久化、同步与生命周期管理。

```mermaid
graph TB
subgraph "Experience Runtime SDK"
SI["State Interface"]
MM["Memory Manager"]
TL["Task Lifecycle"]
AA["Agent Adapter"]
MS["Memory Slicer"]
SC["Scoring System"]
end
subgraph "外部服务"
SVC["CNAA State Service"]
end
AG["AI Agent"] --> SI
SI --> MM
MM --> TL
MM --> AA
MM --> MS
MM --> SC
MM --> |MCP / HTTP| SVC
```

图表来源
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-L80)

章节来源
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-L80)

## 核心组件
- State Interface：统一状态读写接口，屏蔽底层存储差异
- Memory Manager：经验数据的组织、索引、缓存、版本与同步
- **新增**：Memory Slicer：智能内存切片和时间序列管理
- **新增**：Scoring System：多维度评分和重要性评估
- Task Lifecycle：任务级上下文与经验的生命周期绑定
- Agent Adapter：适配不同 Agent 的经验写入/读取协议
- **新增**：Knowledge Condenser：知识压缩和偏好提取
- CNAA State Service：集中式状态服务，提供跨进程/跨实例的状态同步

章节来源
- [README.md:61-72](file://README.md#L61-L72)
- [README_CN.md:69-80](file://README_CN.md#L69-L80)

## 架构总览
Memory Manager 在整体架构中的职责包括：
- 接收来自 State Interface 的读写请求
- **新增**：对大型记忆进行智能切片和时间序列分割
- 对经验数据进行结构化组织与索引构建
- **新增**：计算多维度评分（时效性、完成度、重要性、频率、相关性）
- 维护本地内存缓存与远端一致性
- 处理版本控制、增量更新与冲突合并
- **新增**：执行知识压缩和偏好提取
- 通过 MCP/HTTP 与 CNAA State Service 交互，完成持久化与同步

```mermaid
sequenceDiagram
participant Agent as "AI Agent"
participant SI as "State Interface"
participant MM as "Memory Manager"
participant MS as "Memory Slicer"
participant SC as "Scoring System"
participant Cache as "本地缓存"
participant SVC as "CNAA State Service"
Agent->>SI : "写入/读取经验"
SI->>MM : "转发请求"
MM->>MS : "智能切片大记忆"
MS-->>MM : "返回切片和索引"
MM->>SC : "计算多维评分"
SC-->>MM : "返回评分结果"
MM->>Cache : "检查缓存命中"
alt 缓存命中
Cache-->>MM : "返回数据"
MM-->>SI : "返回结果"
else 缓存未命中
MM->>SVC : "查询/写入远端"
SVC-->>MM : "返回数据/确认写入"
MM->>Cache : "更新缓存"
MM-->>SI : "返回结果"
end
```

图表来源
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-L80)

## 详细组件分析

### 智能内存切片基础设施

**新增**：SimpleMemorySlicer 提供了强大的内存切片和时间序列管理能力。

#### 核心数据结构
- **MemorySlice**：单个切片单元，包含内容、时间戳、标签和摘要
- **MemoryIndex**：按时间排序的记忆索引，支持时间范围和标签查询
- **SimpleMemorySlicer**：主要切片器类，处理大型记忆的自动分割

#### 切片算法特性
- **时间序列分割**：自动识别事件数组并按时间顺序分割
- **智能标签提取**：基于关键词匹配自动提取重要性和类别标签
- **自动生成摘要**：从内容中提取关键信息生成人类可读摘要
- **灵活的内容处理**：支持嵌套结构和多种数据格式

```mermaid
classDiagram
class MemorySlice {
+slice_id : str
+memory_id : str
+parent_memory_id : str
#index : int
+content : dict
+start_time : datetime
+end_time : datetime
+summary : str
+extracted_tags : str[]
}
class MemoryIndex {
+agent_id : str
+index_id : str
+memories : dict[]
+created_at : datetime
+updated_at : datetime
+add_memory()
+get_by_time_range()
+get_by_tags()
+get_latest_n()
}
class SimpleMemorySlicer {
+agent_id : str
+_slices : dict
+_parent_slices : dict
+_index : MemoryIndex
+slice_memory()
+build_index()
+query_by_time_range()
+query_by_tags()
+get_latest_n()
}
MemoryIndex --> MemorySlice : "引用"
SimpleMemorySlicer --> MemoryIndex : "管理"
SimpleMemorySlicer --> MemorySlice : "创建"
```

图表来源
- [slicer.py:29-111](file://local/memory/slicer.py#L29-L111)

#### 标签提取算法
系统实现了智能标签提取，支持多种重要性级别：
- **高重要性**：critical, important, essential, urgent (权重 1.0)
- **中高重要性**：high priority, must, require (权重 0.8)
- **中等重要性**：priority, key, major (权重 0.6)
- **低重要性**：note, reminder, reference (权重 0.4)
- **信息性**：info, background (权重 0.2)

章节来源
- [slicer.py:113-555](file://local/memory/slicer.py#L113-L555)

### 多维度评分系统

**新增**：CompositeScorer 提供了全面的记忆评分能力，支持五个维度的评分计算。

#### 评分维度
1. **时效性评分 (Recency)**：基于指数衰减的时间敏感性评分
2. **完成度评分 (Completion)**：基于任务完成状态的评分
3. **重要性评分 (Importance)**：基于关键词匹配的重要性检测
4. **频率评分 (Frequency)**：基于访问频率的评分
5. **相关性评分 (Relevance)**：基于上下文匹配的评分

#### 评分算法实现
- **指数衰减模型**：`score = 2^(-t/half_life)`，支持可配置的半衰期
- **线性衰减模型**：简单可预测的线性衰减算法
- **关键词加权**：预定义的重要性关键词权重系统
- **对数缩放**：防止高频访问导致评分过高

```mermaid
flowchart TD
A[输入 Memory] --> B[时效性评分]
A --> C[完成度评分]
A --> D[重要性评分]
A --> E[频率评分]
A --> F[相关性评分]
B --> G[加权组合]
C --> G
D --> G
E --> G
F --> G
G --> H[综合评分]
H --> I[评分排名]
```

图表来源
- [scoring_algorithms.py:399-510](file://cnaa/scoring_algorithms.py#L399-L510)

章节来源
- [scoring_algorithms.py:1-510](file://cnaa/scoring_algorithms.py#L1-L510)

### 知识压缩和偏好提取

**新增**：SimpleTimeBasedCondensationPlugin 实现了基于时间的知识压缩功能。

#### 核心功能
- **时间窗口过滤**：只处理指定时间范围内的记忆
- **标签筛选**：根据重要性标签过滤相关记忆
- **偏好提取**：自动识别用户偏好和行为模式
- **知识积累**：从学习相关记忆中提取知识点

#### 提取规则
- **偏好识别**：识别 like/prefer/favorite/habit 等关键词
- **知识提取**：从 learning/knowledge 标签的记忆中提取
- **重要性判断**：基于关键词和内容分析确定重要性

章节来源
- [lifecycle.py:583-782](file://cnaa/lifecycle.py#L583-L782)

### 经验数据结构与索引设计
- 经验实体模型
  - 标识：全局唯一 ID（如 UUID），用于去重与定位
  - 元数据：时间戳、来源 Agent、任务 ID、标签、权重等
  - 内容：结构化片段（键值、向量嵌入、文本摘要等）
  - 版本：版本号或哈希，支持增量与回滚
- **新增**：切片索引
  - 主键索引：按经验 ID 快速定位
  - 复合索引：按任务 ID + 时间戳排序，便于时序检索
  - 语义索引：向量嵌入索引，支持相似度检索
  - 标签索引：按标签聚合，支持过滤与分组
  - **时间序列索引**：按时间范围快速检索
- 检索优化
  - 预取与分页：热点经验预加载，避免大结果集
  - 近似最近邻（ANN）：向量检索加速
  - 缓存分层：热数据 L1（内存）、温数据 L2（本地磁盘）、冷数据 L3（远端）

章节来源
- [README.md:19-41](file://README.md#L19-L41)
- [README_CN.md:19-49](file://README_CN.md#L19-L49)

### 存储策略与后端抽象
- 存储后端抽象接口
  - Read(key, options): 读取指定键的数据
  - Write(key, value, options): 写入数据并返回结果
  - Delete(key, options): 删除数据
  - Scan(prefix, filter, limit): 范围扫描与过滤
  - Batch(ops): 批量操作事务
  - Versioning(key, version): 版本管理与冲突检测
- **新增**：评分集成
  - ScoreUpdate(memory, access_count): 更新记忆评分
  - GetRankedMemories(agent_id, filters): 获取评分排序的记忆列表
  - BatchScoreUpdate(memories): 批量评分计算
- 支持的实现
  - 关系型数据库：MySQL/PostgreSQL（强一致、事务）
  - NoSQL：Redis/Memcached（低延迟缓存）、MongoDB（文档存储）
  - 对象存储：S3/OSS（冷数据归档）
  - 文件系统：本地磁盘（轻量部署）
- 选择策略
  - 热路径优先使用内存缓存与 KV 存储
  - 写放大场景采用 WAL 与异步落盘
  - 读多写少场景启用多级缓存与只读副本

章节来源
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-L80)

### 缓存机制与内存管理
- 缓存层级
  - L1：进程内缓存（LRU/LFU 淘汰策略）
  - L2：本地磁盘缓存（页式存储，按需加载）
  - L3：远端服务缓存（分布式缓存集群）
- 一致性策略
  - 写穿（Write-through）：写入同时更新缓存
  - 写回（Write-back）：延迟落盘，提升吞吐
  - 失效策略：TTL、事件驱动失效、版本号校验
- 内存控制
  - 容量上限与软限制
  - 自动分片与冷热分离
  - 背压与限流保护

章节来源
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-L80)

### 数据版本控制、增量更新与冲突解决
- 版本模型
  - 乐观锁：基于版本号或 ETag 的并发控制
  - 向量差分：仅传输变更部分
  - 快照与增量日志：WAL 记录变更轨迹
- 冲突解决
  - 最后写入获胜（LWW）：适用于非关键数据
  - 自定义合并策略：按权重、时间、来源优先级
  - 人工仲裁：冲突标记与审计日志
- 回滚与恢复
  - 时间点恢复（PITR）
  - 分支合并与回溯

章节来源
- [README.md:19-41](file://README.md#L19-L41)
- [README_CN.md:19-49](file://README_CN.md#L19-L49)

### 数据压缩与传输优化
- 压缩策略
  - 文本：ZSTD/LZ4 高压缩比与低延迟
  - 向量：量化（INT8/FP16）与稀疏编码
  - 元数据：Protobuf/MessagePack 二进制序列化
- 传输优化
  - 增量同步：仅传输变更块
  - 批处理：合并小请求，降低网络开销
  - 流式传输：大对象分块上传/下载

章节来源
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-L80)

### 数据迁移工具、备份恢复与监控指标
- 迁移工具
  - Schema 演进：向后兼容字段映射
  - 数据清洗：去重、格式标准化
  - 灰度切换：双写与流量切分
- 备份恢复
  - 全量快照：定期导出冷数据
  - 增量备份：基于 WAL 的连续备份
  - 恢复演练：自动化验证与回滚
- 监控指标
  - 命中率：L1/L2/L3 缓存命中率
  - 延迟：P95/P99 读写延迟
  - 吞吐：QPS、带宽占用
  - 错误率：超时、重试、失败比例
  - 一致性：版本冲突次数、合并成功率
  - **新增**：评分准确率：评分与实际重要性的相关性
  - **新增**：切片效率：平均切片时间和大小分布

章节来源
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-L80)

### 配置示例与性能调优建议
- 配置项建议
  - 缓存大小：L1=256MB~2GB，L2=10GB+，L3 按集群规模
  - TTL：热数据 5~30min，温数据 1~6h，冷数据 7d+
  - 并发：读写线程池、连接池大小
  - 压缩：默认开启 ZSTD，向量量化 INT8
  - 一致性：默认乐观锁，关键数据可降级为强一致
  - **新增**：切片配置：max_tokens_per_chunk=1000，auto_timestamps=True
  - **新增**：评分权重：recency=0.2, completion=0.25, importance=0.30, frequency=0.15, relevance=0.10
  - **新增**：压缩窗口：knowledge_condensation_window=24h
- 调优建议
  - 热点数据预热：启动时加载高频键
  - 索引优化：合理设置复合索引与向量维度
  - 批处理合并：提高吞吐，降低锁竞争
  - 监控告警：阈值触发扩容与降级
  - **新增**：切片策略：根据记忆大小动态调整切片粒度
  - **新增**：评分校准：定期重新计算评分以适应数据变化
  - **新增**：知识压缩：设置合适的压缩阈值避免过度压缩

章节来源
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-L80)

## 依赖关系分析
Memory Manager 依赖 State Interface 提供的统一能力，并与 CNAA State Service 通信。其内部模块耦合度较低，职责清晰：
- 对外：State Interface
- 对内：缓存层、索引层、版本层、传输层
- **新增**：切片层：Memory Slicer 和索引管理
- **新增**：评分层：CompositeScorer 和评分后端
- 下游：存储后端抽象（DB/KV/FS/S3）

```mermaid
classDiagram
class StateInterface {
+Read(key, options)
+Write(key, value, options)
+Delete(key, options)
+Scan(prefix, filter, limit)
}
class MemoryManager {
-cache LayeredCache
-index IndexManager
-version VersionControl
-transport TransportLayer
-slicer MemorySlicer
-scoring ScoringBackend
+Read(key)
+Write(key, value)
+Sync()
+Migrate()
}
class MemorySlicer {
-simple SimpleMemorySlicer
-index MemoryIndex
-tags TagExtractor
+slice_memory()
+build_index()
+query_by_time_range()
+query_by_tags()
}
class ScoringBackend {
-composite CompositeScorer
-access_counts AccessTracker
+update_scores()
+get_ranked_memories()
+batch_update()
}
class StorageBackend {
<<interface>>
+Read(key)
+Write(key, value)
+Delete(key)
+Scan(prefix, filter)
}
class CNAAStateService {
+MCP/HTTP API
+ConsistencyProtocol
}
StateInterface <.. MemoryManager : "调用"
MemoryManager --> MemorySlicer : "切片管理"
MemoryManager --> ScoringBackend : "评分计算"
MemoryManager --> StorageBackend : "抽象依赖"
MemoryManager --> CNAAStateService : "远程同步"
```

图表来源
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-L80)

章节来源
- [README.md:55-72](file://README.md#L55-L72)
- [README_CN.md:63-80](file://README_CN.md#L63-L80)

## 性能考量
- 读写路径优化
  - 短路径：缓存命中直接返回
  - 长路径：远端同步与落盘
- 并发与锁
  - 无锁数据结构（ConcurrentHashMap）
  - 细粒度锁与分段锁
- I/O 与网络
  - 异步 I/O 与零拷贝
  - 连接复用与超时控制
- 资源隔离
  - 多租户配额与隔离
  - 动态扩缩容
- **新增**：切片性能
  - 批量切片：支持大规模记忆的并行处理
  - 增量索引：只更新变化的索引条目
  - 懒加载：按需构建和更新索引
- **新增**：评分性能
  - 增量评分：只重新计算变化的维度
  - 缓存评分：避免重复计算相同评分
  - 批量评分：支持大规模记忆的批量评分

## 故障排查指南
- 常见问题
  - 缓存穿透：空值缓存与布隆过滤器
  - 缓存雪崩：随机 TTL 与熔断
  - 数据不一致：版本冲突与补偿事务
  - 性能抖动：慢查询与索引缺失
  - **新增**：切片异常：处理无效内容和格式错误
  - **新增**：评分偏差：检查关键词匹配和权重配置
  - **新增**：知识压缩失败：验证标签和格式正确性
- 诊断手段
  - 日志追踪：请求链路 ID
  - 指标采集：Prometheus/Grafana
  - 采样分析：APM 与火焰图
  - **新增**：切片统计：监控切片数量和大小分布
  - **新增**：评分分析：跟踪评分分布和变化趋势
- 恢复流程
  - 回滚到稳定版本
  - 重建索引与缓存
  - 数据校验与修复
  - **新增**：重建评分索引
  - **新增**：重新切片历史数据

## 结论
Memory Manager 作为 CNAA 的核心组件，承担经验数据的持久化、同步与生命周期管理职责。通过抽象存储后端、多级缓存、版本控制与冲突解决，能够在保证一致性的前提下提供高性能与可扩展性。**新增的智能切片基础设施和评分系统**进一步增强了系统的智能化水平，能够自动处理大型记忆、提取重要信息和计算多维评分。建议在落地时结合业务特征选择合适的存储与缓存策略，并完善监控与运维体系。

## 附录
- 术语表
  - 经验（Experience）：任务执行过程中沉淀的可复用知识
  - 状态（State）：Agent 运行时的上下文与记忆集合
  - 版本控制（Versioning）：数据变更的版本管理与冲突处理
  - **新增**：内存切片（Memory Slicing）：将大型记忆分割为可管理的时间序列片段
  - **新增**：知识压缩（Knowledge Condensation）：从记忆中提取偏好和知识的过程
  - **新增**：评分系统（Scoring System）：多维度评估记忆重要性的机制
- 参考链接
  - 文档导航见 README 中的文档列表
  - **新增**：示例代码：examples/memory_slicing_example.py
  - **新增**：测试用例：tests/test_memory_slicing.py