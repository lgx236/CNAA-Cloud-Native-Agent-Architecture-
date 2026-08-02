---
kind: design
name: State 采用三层分类：Preference / State / Environment
source: session
category: adr
---

# State 采用三层分类：Preference / State / Environment

_来源：966265f → 90cf9d3 提交周期内记录的编码计划——内容为规划时意图，实现可能滞后或有出入。_

**状态：** accepted

## 背景
Agent 需要持久化不同类型的数据：重要记忆沉淀、短期知识积累、环境上下文信息，这些数据的更新频率和语义各不相同。

## 决策驱动
- 数据语义清晰性
- 更新策略差异化
- 查询效率
- 知识沉淀路径明确

## 备选方案
- **三层分类（Preference/State/Environment）** — 优点：语义明确、不同类别可独立管理生命周期、支持差异化更新策略
- **扁平键值存储** _（已否决）_ — 优点：实现简单；缺点：缺乏语义区分、难以实施差异化策略、查询不够精确
- **单一文档模型** _（已否决）_ — 优点：原子更新、事务简单；缺点：部分更新复杂、不同语义数据耦合在一起

## 决策
将 Agent 状态分为 Preference（重要记忆沉淀，高重要性）、State（短期知识沉淀，中等重要性）、Environment（环境上下文，低重要性），每类有独立的 CRUD 接口和更新策略。

## 影响
知识沉淀路径清晰：近期记忆 → 根据重要性决定沉淀到 Preference 还是 State；Environment 独立管理外部上下文；三类数据可独立演化和管理。