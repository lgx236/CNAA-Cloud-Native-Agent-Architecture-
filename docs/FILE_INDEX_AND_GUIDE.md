# CNAA v0.2 - 完整文件索引与说明

> **Version**: 0.2.0 | **Date**: 2026-08-06  
> **Purpose**: 全面索引项目中的所有文件，提供清晰的导航和使用指南

---

## 📋 目录结构概览

```
CNAA-Cloud-Native-Agent-Architecture-/
│
├── 📚 README.md                    # 主入口文档（英文）
├── 📚 README_CN.md                 # 中文版主文档
├── 📚 pyproject.toml              # Python 包配置
├── 📚 .env.example                # 环境变量示例
├── 📚 server.py                   # Cloud Server 启动入口
├── 📚 mcp_stdio_server.py         # Stdio MCP Server 入口
│
├── 🗂️ cnaa/                       # Core Layer（核心层）
│   ├── models.py                  # 数据模型定义
│   ├── schemas.py                 # JSON Schema 定义
│   ├── tools.py                   # 13 个 MCP 工具定义
│   ├── security.py                # API Key 认证与安全
│   ├── interaction.py             # 交互协议处理
│   ├── lifecycle.py               # 任务生命周期管理
│   ├── memory_selector.py         # 记忆类型选择器
│   ├── scoring.py                 # 记忆评分系统
│   ├── scoring_algorithms.py      # 评分算法实现
│   │
│   └── adapters/                  # Agent Framework Adapters (v0.2 NEW!)
│       ├── __init__.py            # 适配器导出
│       ├── adapter_base.py        # BaseCNAAAdapter (抽象基类)
│       ├── langchain_adapter.py   # LangChain Mixin
│       ├── llamaindex_adapter.py  # LlamaIndex Mixin
│       ├── autogen_adapter.py     # AutoGen Mixin
│       └── crewai_adapter.py      # CrewAI Mixin
│
├── ☁️ cloud/                       # Cloud Layer（云端层）
│   ├── __init__.py
│   ├── agent.py                   # Cloud Agent 实现
│   ├── server/
│   │   ├── __init__.py
│   │   └── mcp_server.py          # MCP Server 实现（HTTP & Stdio）
│   │
│   └── storage/                   # Storage Backends
│       ├── __init__.py
│       ├── state_store.py         # State Store Interface
│       ├── memory_store.py        # Memory Store Interface
│       ├── sql_state_store.py     # SQLite State Backend
│       ├── sqlite_memory_store.py # SQLite Memory Backend
│       ├── sqlite_store.py        # SQLite Helper
│       └── scoring_backend.py     # Scoring Algorithm Backend
│
├── 💻 local/                      # Local Layer（本地层）
│   ├── __init__.py
│   ├── agent.py                   # Local Agent 实现
│   ├── client/
│   │   ├── __init__.py
│   │   ├── mcp_client.py          # Basic HTTP Client
│   │   └── mcp_client_real.py     # Production HTTP Client
│   │
│   ├── memory/                    # Instant Memory (Local Only)
│   │   ├── __init__.py
│   │   ├── instant_memory.py      # 即时记忆系统
│   │   └── slicer.py              # 记忆切片器
│   │
│   └── state/                     # Local State Cache
│       ├── __init__.py
│       └── state_cache.py         # 状态缓存
│
├── 🧪 tests/                      # 测试套件
│   ├── conftest.py                # Pytest fixtures
│   ├── __init__.py
│   │
│   ├── unit tests:
│   │   ├── test_models.py         # 数据模型测试
│   │   ├── test_scoring_system.py # 评分系统测试
│   │   ├── test_security.py       # 安全认证测试
│   │   ├── test_lifecycle.py      # 生命周期测试
│   │   └── test_micro_comprehensive.py # 单元测试汇总
│   │
│   ├── integration tests:
│   │   ├── test_local.py          # Local 集成测试
│   │   ├── test_cloud_storage.py  # Cloud 存储测试
│   │   └── test_integration.py    # 端到端集成测试
│   │
│   └── special tests:
│       ├── test_distributed_system.py     # 分布式系统测试
│       ├── test_real_openclaw_integration.py # 真实环境 OpenClaw 测试
│       ├── test_e2e_full_loop.py          # 完整端到端测试
│       ├── test_large_scale_performance.py # 大规模性能测试
│       ├── test_mcp_stdio_server.py       # MCP Stdio 测试
│       └── test_memory_slicing.py         # 记忆切片测试
│
├── 🌟 examples/                   # 使用示例
│   ├── README.md                  # 示例总览
│   ├── simple_agent_demo.py       # 简单智能体演示
│   ├── memory_scoring_demo.py     # 记忆评分演示
│   ├── memory_slicing_example.py  # 记忆切片示例
│   ├── openclaw_integration.py    # OpenClaw 集成示例
│   ├── multi_agent_framework_demo.py  # 多框架集成演示（NEW!）
│   ├── show_integration_patterns.py # 展示所有集成模式（NEW!）
│   │
│   └── cnaa_client/               # HTTP Clients（NEW!）
│       └── typescript/
│           └── cnaa_client.ts     # TypeScript/Node.js 客户端
│
├── 📖 docs/                       # 技术文档
│   ├── index.md                   # 文档中心
│   ├── README.md                  # 文档导航
│   ├── AGENT_ADAPTER_WORKING_PRINCIPLES.md  # 适配器原理详解（NEW!）
│   ├── AGENT_INTEGRATION_GUIDE.md   # 集成指南（NEW!）
│   ├── MULTI_AGENT_FRAMEWORK_INTEGRATION_COMPLETE.md # v0.2 总结（NEW!）
│   ├── SERVICE_TEST_REPORT.md       # 服务测试报告
│   ├── CLOUD_LOCAL_DUAL_ENDPOINT.md # 双端点架构说明
│   ├── DISTRIBUTED_TESTING_GUIDE.md # 分布式测试指南
│   ├── VALIDATION_REPORT.md         # 验证报告
│   ├── V02_FINAL_SUMMARY.md         # v0.2 最终总结
│   ├── v0.2_IMPLEMENTATION_SUMMARY.md # v0.2 实施摘要
│   ├── v0.2_ROADMAP.md              # v0.2 路线图
│   ├── api-reference.md             # API 参考
│   ├── architecture.md              # 架构文档
│   │
│   ├── deployment/                  # 部署文档
│   │   └── GUIDE.md                 # 部署指南
│   │
│   └── zh/                          # 中文文档
│       └── technical-implementation.md  # 技术实现细节
│
├── 🔧 scripts/                    # 脚本工具
│   ├── start.sh                   # 启动服务器
│   ├── stop.sh                    # 停止服务器
│   ├── status.sh                  # 查看状态
│   ├── run_distributed_tests.sh   # 运行分布式测试
│   ├── acceptance_test.sh         # 验收测试脚本（NEW!）
│   ├── backup.sh                  # 数据库备份
│   ├── build_docs.py              # 构建文档系统
│   └── check_v02_readiness.py     # v0.2 就绪检查
│
├── ⚡ plugins/                    # 插件系统
│   └── simple_algorithms.py       # 基础评分算法
│
├── 📦 Quick Start Guides
│   ├── QUICK_DEPLOY.md            # 快速部署指南
│   └── QUICK_START_V02.md         # v0.2 快速开始
│
└── 🔧 配置文件
    ├── pyproject.toml             # Python 项目配置
    ├── .env.example               # 环境变量模板
    ├── .gitignore                 # Git 忽略规则
    └── pytest.ini                 # pytest 配置

```

---

## 🔑 核心模块详解

### 1️⃣ cnaa/ — 核心层

**职责**: 定义接口契约、协议规范和安全机制

| 文件 | 行数 | 作用 | 关键内容 |
|------|------|------|---------|
| `models.py` | ~500 | 数据模型 | `Memory`, `State`, `Preference`, `Environment` dataclasses |
| `schemas.py` | ~300 | JSON Schema | JSON Schema 定义，用于请求/响应验证 |
| `tools.py` | ~400 | MCP Tools | 13 个 MCP 工具元数据和权限映射 |
| `security.py` | ~200 | 认证授权 | API Key 验证、读写权限控制 |
| `interaction.py` | ~200 | 协议处理 | JSON-RPC 2.0 消息处理逻辑 |
| `lifecycle.py` | ~300 | 生命周期 | Task Point 从分配到完成的状态流转 |
| `memory_selector.py` | ~150 | 记忆选择 | 短期/长期记忆选择策略 |
| `scoring.py` | ~200 | 评分系统 | 记忆优先级计算逻辑 |
| `scoring_algorithms.py` | ~200 | 评分算法 | Recency, Composite Scoring 等算法 |

#### 🆕 `cnaa/adapters/` — Agent Framework Adapters (v0.2 NEW!)

| 文件 | 行数 | 作用 | 关键内容 |
|------|------|------|---------|
| `__init__.py` | 47 | 导出公共 API | `BaseCNAAAdapter`, Mixins 等 |
| `adapter_base.py` | 616 | **核心抽象基类** | `BaseCNAAAdapter`, `CNAAMemoryMixin`, 数据配置类 |
| `langchain_adapter.py` | 209 | LangChain 适配 | `LangChainCNAAMixin` |
| `llamaindex_adapter.py` | 115 | LlamaIndex 适配 | `LlamaIndexCNAAMixin` |
| `autogen_adapter.py` | 136 | AutoGen 适配 | `AutoGencNAAAMixin` |
| `crewai_adapter.py` | 153 | CrewAI 适配 | `CrewAICNAAAMixin` |

**工作原理**:
```python
# Layer 1: Abstract Base Class (adapter_base.py)
class BaseCNAAAdapter(ABC):
    def __init__(self, server_url, api_key, timeout):
        self._client = CNAA_MCPClient(server_url, api_key, timeout)  # Layer 2
    
    def store_memory(self, agent_id, memory_id, content, ...):
        # Data transformation
        config = MemoryConfig(...)
        # Delegate to HTTP client
        return self._client.store_memory(**config.to_dict())

# Layer 2: Framework-specific Mix-ins
class LangChainCNAAMixin(BaseCNAAAdapter):
    """Add CNAA memory to LangChain agents via mix-in pattern"""
    
    def on_task_complete(self, agent_id, task_result):
        self.store_memory(agent_id=agent_id, ...)  # Uses inherited method
```

👉 **[详细原理](docs/AGENT_ADAPTER_WORKING_PRINCIPLES.md)**

---

### 2️⃣ cloud/ — 云端层

**职责**: 提供服务端实现，包括 MCP Server 和持久化存储

| 文件 | 行数 | 作用 | 关键内容 |
|------|------|------|---------|
| `server/mcp_server.py` | ~800 | MCP Server | HTTP POST /mcp 端点实现，路由到对应工具 |
| `agent.py` | ~200 | Cloud Agent | 云端智能体接口实现 |
| `storage/state_store.py` | ~150 | State 存储接口 | ABC 定义的接口契约 |
| `storage/memory_store.py` | ~150 | Memory 存储接口 | ABC 定义的接口契约 |
| `storage/sqlite_store.py` | ~300 | SQLite 实现 | 存储 CRUD 操作 |
| `storage/scoring_backend.py` | ~200 | 评分后端 | 调用评分算法 |

**架构图**:
```
User Request → server.py → CNAA_MCPServer
                           ├─ handle_store_memory()
                           ├─ handle_get_memory()
                           ├─ handle_update_state()
                           └─ Storage Backends (SQLite/ChromaDB)
```

---

### 3️⃣ local/ — 本地层

**职责**: 提供本地运行时，作为 HTTP Client 连接云端

| 文件 | 行数 | 作用 | 关键内容 |
|------|------|------|---------|
| `client/mcp_client_real.py` | ~400 | HTTP Client | 生产级 HTTP 客户端，发送 JSON-RPC 请求 |
| `agent.py` | ~200 | Local Agent | 本地智能体接口（转发到云端） |
| `memory/instant_memory.py` | ~300 | 即时记忆 | 本地临时记忆，快速访问 |
| `memory/slicer.py` | ~200 | 记忆切片 | 将大记忆拆分为小块 |
| `state/state_cache.py` | ~200 | 状态缓存 | 本地状态缓存减少网络请求 |

**工作流程**:
```
Agent Code → Local Agent → MCP Client
                             ↓
                       HTTP POST /mcp
                             ↓
                        Cloud Server
```

---

### 4️⃣ tests/ — 测试体系

#### 🎯 单元测试（Unit Tests）

| 文件 | 覆盖范围 | 测试要点 |
|------|---------|---------|
| `test_models.py` | models.py | 数据模型验证、边界条件 |
| `test_scoring_system.py` | scoring/*.py | 评分算法正确性、性能 |
| `test_security.py` | security.py | API Key 认证、权限隔离 |
| `test_lifecycle.py` | lifecycle.py | 状态流转完整性 |

#### 🔄 集成测试（Integration Tests）

| 文件 | 场景 | 描述 |
|------|------|------|
| `test_local.py` | Local 功能 | 本地记忆、缓存等功能 |
| `test_cloud_storage.py` | Cloud 存储 | SQLite/InMemory 存储正确性 |
| `test_integration.py` | End-to-End | 完整工作流测试 |

#### 🌐 分布式测试（Distributed Tests）

| 文件 | 目的 | 关键测试点 |
|------|------|-----------|
| `test_distributed_system.py` | **分布式架构验证** | • Cloud 与 Local 独立运行<br>• HTTP 通信无直接耦合<br>• 多 Agent 并发访问<br>• 网络故障优雅降级 |
| `test_real_openclaw_integration.py` | **真实环境集成** | • TypeScript 客户端与 Python 服务端通信<br>• 跨语言内存共享验证 |

**运行命令**:
```bash
# 所有测试
pytest tests/ -v

# 仅分布式测试
./scripts/run_distributed_tests.sh all

# 真实环境集成测试
python tests/test_real_openclaw_integration.py
```

---

### 5️⃣ examples/ — 使用示例

| 文件 | 难度 | 适用人群 | 说明 |
|------|------|---------|------|
| `simple_agent_demo.py` | ⭐ | 初学者 | 最简化的 Agent 集成示例 |
| `memory_scoring_demo.py` | ⭐⭐ | 中级 | 展示记忆评分系统如何工作 |
| `memory_slicing_example.py` | ⭐⭐ | 中级 | 大记忆分片存储演示 |
| `openclaw_integration.py` | ⭐⭐⭐ | 高级 | OpenClaw TypeScript 框架集成 |
| `multi_agent_framework_demo.py` | ⭐⭐⭐ | 进阶 | 演示 6+ 框架集成 |
| `show_integration_patterns.py` | ⭐⭐ | 通用 | 展示所有集成模式和架构 |

---

### 6️⃣ docs/ — 技术文档

#### 📖 文档体系

| 文档 | 受众 | 关键内容 |
|------|------|---------|
| `index.md` | 所有人 | 文档导航和资源索引 |
| `README.md` | 新用户 | 文档总览和使用指南 |
| `architecture.md` | 架构师 | 三层正交架构设计 |
| `api-reference.md` | 开发者 | 完整 API 接口定义 |
| `technical-implementation.md` | 开发者 | 技术细节和实现原理 |

#### 🆕 v0.2 新增文档

| 文档 | 页数 | 目标 |
|------|------|------|
| `AGENT_ADAPTER_WORKING_PRINCIPLES.md` | 843 | 深入解析 Mix-in 模式、三层架构、HTTP 协议 |
| `AGENT_INTEGRATION_GUIDE.md` | 688 | 所有框架集成指南（LangChain, LlamaIndex, AutoGen, CrewAI） |
| `MULTI_AGENT_FRAMEWORK_INTEGRATION_COMPLETE.md` | 452 | v0.2 集成工作总结 |

---

### 7️⃣ scripts/ — 自动化脚本

| 脚本 | 用途 | 关键功能 |
|------|------|---------|
| `start.sh` | 启动服务器 | 读取.env，启动 Cloud Server（端口 8080） |
| `stop.sh` | 停止服务 | 根据 PID 文件终止进程 |
| `status.sh` | 查看状态 | 检查进程、端口、日志 |
| `run_distributed_tests.sh` | 运行测试 | 自动启动/停止测试环境，执行分布式测试 |
| `acceptance_test.sh` | 验收测试 | 完整的服务验收流程 |
| `backup.sh` | 备份数据 | SQLite 数据库备份和清理 |
| `build_docs.py` | 构建文档 | 生成静态文档站 |

---

## 🔍 快速查找文件

### 我想了解……

#### **Agent 如何集成 CNAA？**
→ [`cnaa/adapters/adapter_base.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/cnaa/adapters/adapter_base.py)  
→ [`docs/AGENT_INTEGRATION_GUIDE.md`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/docs/AGENT_INTEGRATION_GUIDE.md)

#### **Mix-in 模式如何工作？**
→ [`docs/AGENT_ADAPTER_WORKING_PRINCIPLES.md`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/docs/AGENT_ADAPTER_WORKING_PRINCIPLES.md)

#### **HTTP 通信格式是什么？**
→ [`local/client/mcp_client_real.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/local/client/mcp_client_real.py)  
→ [`cloud/server/mcp_server.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/cloud/server/mcp_server.py)

#### **记忆数据结构长什么样？**
→ [`cnaa/models.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/cnaa/models.py)

#### **API Key 认证如何实现？**
→ [`cnaa/security.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/cnaa/security.py)

#### **如何启动服务？**
→ [`scripts/start.sh`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/scripts/start.sh)

#### **如何运行测试？**
→ [`scripts/acceptance_test.sh`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/scripts/acceptance_test.sh)

#### **TypeScript 客户端如何使用？**
→ [`examples/cnaa_client/typescript/cnaa_client.ts`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/examples/cnaa_client/typescript/cnaa_client.ts)

---

## 📊 文件大小统计

| 类别 | 文件数 | 总代码行 | 占比 |
|------|--------|----------|------|
| **Core Layer (cnaa/)** | 12 | ~3,000 | 25% |
| **Cloud Layer** | 8 | ~1,800 | 15% |
| **Local Layer** | 7 | ~900 | 8% |
| **Tests** | 13 | ~4,500 | 37% |
| **Examples** | 6 | ~1,600 | 13% |
| **Docs** | 20+ | 15,000+ | N/A |

---

## ✅ 文件检查清单

### 所有核心文件都应有：

- [x] **清晰的 docstring** — 每个 public function/class 都有说明
- [x] **类型注解** — 函数参数和返回值都有类型标注
- [x] **示例代码** — 复杂功能有 usage example
- [x] **测试覆盖** — 核心功能有单元测试 + 集成测试
- [x] **文档链接** — 在文件开头引用相关文档
- [x] **错误处理** — 异常处理和日志记录
- [x] **导入说明** — 依赖项有明确声明

### 所有公共 API 都应有：

- [x] **Public API 导出** — `__all__` 列表或显式 import
- [x] **版本兼容性** — 如有变更需注明
- [x] **性能考虑** — 时间/空间复杂度说明
- [x] **安全提示** — 敏感操作需警告

---

## 🏷️ 命名约定

### Python 文件
- **Module**: snake_case.py (如 `memory_store.py`)
- **Class**: PascalCase (如 `CNAA_MCPServer`)
- **Function**: snake_case (如 `store_memory()`)
- **Constant**: UPPER_SNAKE_CASE (如 `API_KEY_ENABLED`)

### TypeScript 文件
- **Module**: camelCase.ts (如 `cnaa_client.ts`)
- **Class**: PascalCase (如 `CNAAClient`)
- **Function**: camelCase (如 `storeMemory()`)

### 测试文件
- Format: `test_<module_name>.py`
- Test Function: `test_<scenario>()`

---

## 📝 代码注释规范

### 必须注释的情况
1. **公共 API** — 所有导出的函数/类必须有 docstring
2. **复杂逻辑** — 超过 10 行的非直观逻辑需要注释
3. **边界情况** — 特殊处理的边缘条件
4. **外部依赖** — 引入第三方库的特定用法

### 可选注释
1. **简单的 getter/setter**
2. **明显的变量名** (如 `user_id`, `api_key`)
3. **Python 标准库调用**

### 不应有的注释
1. **"显而易见的"注释** — 不要写 `i += 1 # increment i`
2. **过期的 TODO** — 及时更新或删除
3. **内部实现的冗余说明** — 代码应该自解释

---

## 🔧 代码风格要求

遵循 **PEP 8** 和 **Google Style Guide**:

- [x] **缩进**: 4 spaces (not tabs)
- [x] **行宽**: 最大 120 characters
- [x] **空行**: 函数间 2 行，方法间 1 行
- [x] **导入顺序**: stdlib → third-party → local
- [x] **注释**: 每行不超过 79 characters
- [x] **字符串**: 使用 f-string (Python 3.6+)

**格式化命令**:
```bash
# Auto-format with black
black .

# Sort imports with isort
isort .
```

---

## 🚀 下一步维护建议

### 新开发者入门路径

1. **阅读文档**: [`README.md`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/README.md) → [`QUICK_START_V02.md`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/QUICK_START_V02.md)
2. **理解架构**: [`docs/architecture.md`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/docs/architecture.md)
3. **运行示例**: `python examples/simple_agent_demo.py`
4. **阅读核心代码**: [`cnaa/adapters/adapter_base.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/cnaa/adapters/adapter_base.py)
5. **编写第一个测试**: `pytest tests/test_models.py -v`

### 贡献者指南

1. Fork 仓库
2. 创建 feature branch
3. 修改代码（添加测试！）
4. 运行完整测试套件
5. 提交 PR

---

## 📞 联系与支持

- 📖 **文档问题**: 查阅 [`docs/`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/docs/)
- 🐛 **Bug 报告**: GitHub Issues
- 💬 **功能讨论**: Pull Requests
- 📧 **邮件支持**: [github.com/lgx236/CNAA](https://github.com/lgx236/CNAA-Cloud-Native-Agent-Architecture-)

---

**Last Updated**: 2026-08-06  
**Maintained By**: CNAA Development Team
