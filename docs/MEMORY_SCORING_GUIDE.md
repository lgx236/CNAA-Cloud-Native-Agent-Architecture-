# CNAA 记忆评分系统集成指南

## 📋 概述

CNAA（Cloud-Native Agent Architecture）记忆评分系统通过多维度的智能评分机制，帮助 agent 选择最佳记忆。该系统基于简单、可靠、可扩展的算法设计原则。

### ✨ 核心特性

- **多维度评分**: 时效性、完成度、重要性、访问频率、上下文相关性
- **可配置权重**: 支持根据业务场景调整各维度权重
- **智能排序**: 自动按综合得分排序，优先展示高质量记忆
- **上下文感知**: 根据当前场景动态调整相关性评分
- **批量处理**: 高效处理大批量记忆的评分计算

---

## 🏗️ 架构设计

### 组件关系图

```
┌─────────────────────────────────────────────────────────────┐
│                    MemoryInterface                           │
│  (提供 get_memory_scores() 抽象接口)                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              InMemoryMemoryStore                             │
│         (存储实际记忆数据)                                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│           MemoryScoringBackend                               │
│   - batch_update_scores(): 批量计算评分                       │
│   - update_scores_for_memory(): 单条评分                     │
│   - get_scores_for_agent(): 获取已排序的记忆列表             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│          CompositeScorer                                     │
│   ┌──────────────┬──────────────┬──────────────┐            │
│   │ Recency      │ Completion   │ Importance   │            │
│   │ Scorer       │ Scorer       │ Scorer       │            │
│   ├──────────────┼──────────────┼──────────────┤            │
│   │ Frequency    │ Relevance    │              │            │
│   │ Scorer       │ Scorer       │              │            │
│   └──────────────┴──────────────┴──────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 使用场景

### 1. 基础用法 - 获取 Top N 记忆

```python
from cnaa.memory_selector import create_scored_selector
from cloud.storage.memory_store import InMemoryMemoryStore
from cnaa.models import Memory, MemoryType
from datetime import datetime, timedelta

# 创建存储和 selector
store = InMemoryMemoryStore()
selector = create_scored_selector(store)

# 存储一些记忆
memory = Memory(
    memory_id="task-001",
    agent_id="my-agent",
    type=MemoryType.LONG_TERM,
    content={"task": "Completed successfully"},
    tags=["important", "success"],
    completion_score=1.0,
    timestamp=datetime.now()
)
store.store_memory(memory)

# 获取 Top 3 最高分记忆
top_memories = selector.get_top_n("my-agent", n=3)

for mem, score in top_memories:
    print(f"{mem.memory_id}: {score:.3f}")
```

### 2. 上下文相关记忆检索

```python
# 根据用户查询找到最相关的记忆
query_context = {"keywords": ["python", "programming"]}
best_match = selector.find_best_match(
    "my-agent",
    query_context=query_context,
    threshold=0.5
)

if best_match:
    mem, score = best_match
    print(f"推荐记忆：{mem.content} (相关度：{score:.3f})")
```

### 3. 仅筛选重要记忆

```python
# 获取重要性评分 > 0.8 的记忆
important_memories = selector.get_important_memories(
    "my-agent",
    min_importance=0.8,
    top_n=5
)

for mem, importance_score in important_memories:
    print(f"{mem.memory_id}: 重要性={importance_score:.3f}")
```

### 4. 过滤特定分数阈值的记忆

```python
# 获取综合分数 >= 0.6 的记忆
filtered = selector.filter_by_threshold(
    "my-agent",
    min_composite=0.6,
    access_counts={"mem-001": 10, "mem-002": 5}  # 可选：访问次数
)
```

---

## 🔧 评分算法详解

### 五大评分维度

| 维度 | 说明 | 计算方式 | 默认权重 |
|------|------|---------|----------|
| **Recency** (时效性) | 时间越近分数越高 | 指数衰减公式 | 20% |
| **Completion** (完成度) | 任务完成情况 | 直接映射 completion_score | 25% |
| **Importance** (重要性) | 关键词匹配程度 | 标签关键词加权 | 30% |
| **Frequency** (频率) | 访问频率高低 | 对数缩放 | 15% |
| **Relevance** (相关性) | 与上下文的匹配度 | 文本相似度 | 10% |

### 复合分数计算

```python
composite = (
    recency * 0.20 +
    completion * 0.25 +
    importance * 0.30 +
    frequency * 0.15 +
    relevance * 0.10
)
```

### 自定义权重

```python
# 创建自定义评分器
custom_weights = {
    "recency": 0.1,      # 降低时效性权重
    "completion": 0.3,   # 提高完成度权重
    "importance": 0.4,   # 强调重要性
    "frequency": 0.1,
    "relevance": 0.1,
}

from cnaa.scoring_algorithms import CompositeScorer
scorer = CompositeScorer(weights=custom_weights)
```

---

## 📊 评分标准

### Importance 评分规则

| 标签关键词 | 权重 | 说明 |
|-----------|------|------|
| critical, important, essential, urgent | 1.0 | 最高优先级 |
| high priority, must, require | 0.8 | 高优先级 |
| priority, key, major | 0.6 | 中等优先级 |
| note, reminder | 0.4 | 提醒事项 |
| info, background | 0.2 | 参考信息 |

### Recency 评分曲线

- **新记忆 (0 天)**: 1.0
- **7 天 (半衰期)**: 0.5
- **14 天**: 0.25
- **30 天**: < 0.1
- **90 天**: ≈ 0.0

### Frequency 评分示例

| 访问次数 | 分数 | 说明 |
|---------|------|------|
| 0 | 0.0 | 从未访问 |
| 5 | ~0.33 | 偶尔访问 |
| 20 | ~0.67 | 频繁访问 |
| 100 | ~0.90 | 非常频繁 |

---

## 🚀 性能优化

### 批量评分

对于大量记忆，使用批量评分更高效：

```python
from cloud.storage.scoring_backend import MemoryScoringBackend

backend = MemoryScoringBackend()
memories = [...]  # 多个 Memory 对象

# 一次性计算所有记忆的评分
scores = backend.batch_update_scores(memories)

# 结果已经是按分数排序的
ranked = backend.get_scores_for_agent("agent-001", top_n=10)
```

### 缓存策略

```python
# 可以缓存访问计数以减少重复计算
access_cache = {}

def get_access_count(memory_id):
    return access_cache.get(memory_id, 0)
```

---

## 🧪 测试验证

### 运行测试套件

```bash
cd /root/CNAA-Cloud-Native-Agent-Architecture-
python3 -m pytest tests/test_scoring_system.py -v
```

### 运行完整演示

```bash
python3 examples/memory_scoring_demo.py
```

---

## 🔍 故障排查

### 常见问题

**Q1: 所有记忆都得到相同的分数？**
- 检查是否正确初始化了 `InMemoryMemoryStore`
- 确认记忆有正确的 `tags` 和 `completion_score` 字段

**Q2: 为什么某些记忆没有被包含在结果中？**
- 检查是否达到了最小阈值 (`min_composite`)
- 查看记忆的时间戳是否超过最大年龄限制

**Q3: 如何调试评分计算过程？**
```python
# 查看详细评分详情
print(f"Recency: {scores.recency_score:.3f}")
print(f"Completion: {scores.completion_score:.3f}")
print(f"Importance: {scores.importance_score:.3f}")
print(f"Composite: {scores.composite:.3f}")
```

---

## 📈 扩展指南

### 添加新的评分维度

1. 创建新的 scorer 类继承自基类或直接实现评分函数
2. 修改 `CompositeScorer.score_memory()` 方法调用新的评分器
3. 在 `ScoreThresholds` 中添加新的阈值配置
4. 更新权重分配

### 自定义评分后端

```python
class MyCustomScoringBackend(MemoryScoringBackend):
    def update_scores_for_memory(self, memory, access_count, context):
        # 自定义评分逻辑
        base_scores = super().update_scores_for_memory(memory, access_count, context)
        
        # 添加领域特定的分数调整
        if self._is_critical_domain(memory):
            base_scores.composite_score *= 1.2
        
        return base_scores
```

---

## 🎓 最佳实践

### 1. 权重配置建议

- **开发环境**: 偏向 Recency (最新信息更重要)
- **生产环境**: 偏向 Importance (关键信息优先)
- **学习场景**: 偏向 Completion (已完成知识更可靠)

### 2. 记忆质量维护

- 为重要记忆添加适当标签：`["important"]`, `["critical"]`
- 及时更新 `completion_score`
- 定期清理过期或无效记忆

### 3. 性能调优

- 对于大规模系统，考虑引入缓存层
- 批量操作优于单条操作
- 避免频繁刷新同一批记忆

---

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| [`cnaa/scoring.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/cnaa/scoring.py) | 评分数据结构定义 |
| [`cnaa/scoring_algorithms.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/cnaa/scoring_algorithms.py) | 评分算法实现 |
| [`cnaa/memory_selector.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/cnaa/memory_selector.py) | 记忆选择工具 |
| [`cloud/storage/scoring_backend.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/cloud/storage/scoring_backend.py) | 评分后端服务 |
| [`tests/test_scoring_system.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/tests/test_scoring_system.py) | 完整测试套件 |
| [`examples/memory_scoring_demo.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/examples/memory_scoring_demo.py) | 完整演示脚本 |

---

## ✅ 验收标准

- [x] 所有评分算法已通过单元测试
- [x] 支持批量评分操作
- [x] 提供易用的高级接口 (`ScoredMemorySelector`)
- [x] 代码清晰可读，注释完善
- [x] 算法复杂度 O(1)，适合高性能场景
- [x] 支持自定义权重配置
- [x] 完整的集成文档和示例

---

## 🎉 总结

CNAA 记忆评分系统通过简单的数学公式实现了高质量的记忆选择机制。系统设计遵循"简洁、可靠、可扩展"的原则，适合各种 AI 代理应用场景。

**核心理念**: 
- 用简单的方式解决复杂的问题
- 保持透明度和可解释性
- 提供灵活的配置选项

开始使用评分系统，让你的 AI agent 更智能地选择和利用记忆！🚀
