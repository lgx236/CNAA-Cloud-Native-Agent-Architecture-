---
kind: design
name: 使用 dataclass + ABC 构建轻量级接口契约层
source: session
category: adr
---

# 使用 dataclass + ABC 构建轻量级接口契约层

_来源：461fe1c → 966265f 提交周期内记录的编码计划——内容为规划时意图，实现可能滞后或有出入。_

**状态：** accepted

## 背景
CNAA V0.1 需要快速迭代，同时保持清晰的模块边界和可扩展性。复杂的 ORM 或框架会引入不必要的依赖和耦合。

## 决策驱动
- 轻量级依赖
- Python 原生特性
- 清晰的接口契约
- 易于测试和替换

## 备选方案
- **dataclass + ABC 抽象基类** — 优点：标准库支持、无额外依赖、类型提示友好、易于单元测试
- **Pydantic models** _（已否决）_ — 优点：强大的验证能力；缺点：增加运行时开销、V0.1 不需要复杂验证、与 dataclass 功能重叠
- **SQLAlchemy ORM** _（已否决）_ — 优点：数据库映射强大；缺点：过度工程、V0.1 使用内存存储、学习成本高

## 决策
所有数据模型使用 dataclass 定义（Memory、TaskCheckpoint、InstantMemory、State、Preference、Environment），接口使用 ABC 抽象基类（MemoryInterface、StateInterface），确保 V0.1 的简洁性和后续扩展性。

## 影响
代码简洁、依赖最小化、易于理解和维护；但缺少自动验证，需要在应用层处理数据校验；后续如需持久化可直接替换存储实现而不影响上层。