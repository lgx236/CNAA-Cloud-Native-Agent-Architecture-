# CNAA - 云原生智能体架构 (Cloud-Native Agent Architecture)

<div align="center">

![版本](https://img.shields.io/badge/version-0.2.0-blue)
![许可证](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.12+-blue)

## 🌐 通用智能体记忆基础设施

**CNAA (Cloud-Native Agent Architecture)** 是一个语言无关的分布式记忆系统，为**任意智能体框架**提供云端经验存储和共享能力。

[📖 完整文档](docs/) • [🚀 快速开始](#快速开始) • [🔧 集成指南](docs/AGENT_INTEGRATION_GUIDE.md) • [🎯 工作原理](docs/AGENT_ADAPTER_WORKING_PRINCIPLES.md)

</div>

---

## ⚡ 一句话介绍

**CNAA 让任何智能体（无论用 Python、TypeScript、Go 还是其他语言编写）都能通过简单的 HTTP API，将工作经验持久化存储到云端，供所有智能体共享和学习！**

---

## 🎯 核心功能

### ✅ 主要特性

- **🌍 语言无关**: 支持 Python、TypeScript、Go、Java 等任何 HTTP 支持的语言
- **🤝 多框架兼容**: 原生支持 LangChain、LlamaIndex、AutoGen、CrewAI 等主流框架
- **☁️ 云端存储**: 基于 SQLite 或 ChromaDB 的持久化记忆存储
- **🔒 安全认证**: API Key + Bearer Token 双重认证机制
- **⚡ 高性能**: HTTP/JSON 标准化协议，低延迟响应
- **🔌 可插拔架构**: 易于扩展新的智能体框架和存储后端

### 🚀 使用场景

| 场景 | 描述 | 价值 |
|------|------|------|
| **跨智能体协作** | 不同智能体共享经验和知识 | 避免重复学习，提升整体效率 |
| **长期记忆** | 智能体保留历史交互信息 | 持续改进，积累专业领域知识 |
| **分布式部署** | 智能体运行在多个机器/云环境 | 独立部署，统一记忆管理 |
| **框架迁移** | 从一个框架迁移到另一个框架 | 保持记忆连续性，无缝切换 |
| **多语言智能体** | Python + TypeScript + Go 混合部署 | 利用各语言优势，统一记忆层 |

---

## 🏗️ 架构概览

```
┌──────────────────────────────────────────────┐
│         你的智能体应用 (YOUR AGENTS)          │
│                                              │
│  ┌─────────┐  ┌─────────┐  ┌────────────┐   │
│  │LangChain│  │LlamaIndex│ │ AutoGen    │   │
│  │(Python) │  │(Python) │  │(Python)    │   │
│  └────┬────┘  └────┬────┘  └─────┬──────┘   │
│       │            │              │          │
│  ┌────┴────────────┴──────────────┴────────┐ │
│  │      CNAA 适配器 Mix-ins                  │ │
│  │  • LangChainCNAAMixin                   │ │
│  │  • LlamaIndexCNAAMixin                  │ │
│  │  • AutoGencNAAAMixin                    │ │
│  └───────────────┬────────────────────────┘ │
└──────────────────┼─────────────────────────┘
                   │ HTTP POST /mcp
                   ▼
┌──────────────────────────────────────────────┐
│           CNAA 云端服务                        │
│                                              │
│  • MCP Router                        🔒     │
│  • 身份认证 (API Key)                         │
│  • 存储后端:                                 │
│    - SQLite (默认)                           │
│    - ChromaDB (可选)                         │
└──────────────────────────────────────────────┘

支持与 TypeScript、Go、Java 以及任何支持 HTTP 的语言通信！
```

---

## 🚀 快速开始

### Step 1: 克隆项目

```bash
git clone https://github.com/your-org/CNAA.git
cd CNAA-Cloud-Native-Agent-Architecture-
```

### Step 2: 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
nano .env
```

**.env 示例**:
```ini
# 服务器配置
CNAA_SERVER_PORT=8080
CNAA_SERVER_HOST=0.0.0.0

# 记忆存储（SQLite 默认）
MEMORY_STORAGE_TYPE=sqlite
MEMORY_STORAGE_PATH=./cnaa_memories.db

# 状态存储
STATE_STORAGE_TYPE=sqlite
STATE_STORAGE_PATH=./cnaa_states.db

# 安全选项（可选）
API_KEY_ENABLED=true
API_KEYS=admin,developer,test
```

### Step 3: 启动服务

```bash
# 快速启动
./scripts/start.sh

# 或者手动启动
python server.py --host 0.0.0.0 --port 8080
```

**验证服务**:
```bash
curl http://localhost:8080/health
# 返回：{"status": "healthy"}
```

---

## 🤖 与你的智能体集成

### Option A: Python 框架（推荐）

#### 使用 LangChain

```python
# 安装：pip install langchain openai
from langchain.agents import AgentExecutor
from cnaa.adapters.langchain import LangChainCNAAMixin

class MyAgent(LangChainCNAAMixin, AgentExecutor):
    agent_id = "我的-langchain 智能体"
    
    def _call(self, inputs, *args, **kwargs):
        # 运行原有逻辑
        result = super()._call(inputs, *args, **kwargs)
        
        # 自动存储经验
        self.on_task_complete(
            agent_id=self.agent_id,
            task_result=result,
            tags=["langchain"],
            completion_score=0.95
        )
        
        return result

# 使用
agent = MyAgent.from_llm_and_tools(llm, tools)
response = agent.run("分析销售数据")
```

#### 使用 LlamaIndex

```python
from llama_index.agent import OpenAIAgent
from cnaa.adapters.llamaindex import LlamaIndexCNAAMixin

class MyChatAgent(LlamaIndexCNAAMixin, OpenAIAgent):
    agent_id = "我的-llama 智能体"
    
    def chat(self, message: str):
        response = super().chat(message)
        
        # 记录对话
        self.on_query_complete(
            query=message,
            response=response.response,
            tags=["llamaindex"]
        )
        
        return response
```

#### 使用 AutoGen

```python
from autogen import ConversableAgent
from cnaa.adapters.autogen import AutoGencNAAAMixin

class MyMultiAgent(AutoGencNAAAMixin, ConversableAgent):
    agent_id = "我的-autogen 智能体"
    
    def generate_reply(self, messages, sender=None):
        reply = super().generate_reply(messages, sender)
        self.on_response_generated(response=reply)
        return reply
```

#### 使用 CrewAI

```python
from crewai import Agent
from cnaa.adapters.crewai import CrewAICNAAAMixin

class MyCrewAgent(CrewAICNAAAMixin, Agent):
    def run(self, task_input: str):
        result = super().run(task_input)
        self.on_task_complete(result=result, task_context={"input": task_input})
        return result
```

**更简单的用法 - 继承基础类**:

```python
from cnaa.adapters import BaseCNAAAdapter

class CustomAgent(BaseCNAAAdapter):
    agent_id = "自定义智能体"
    
    def process_request(self, request):
        result = self.execute(request)
        
        # 自动存储到 CNAA
        self.on_task_complete(agent_id=self.agent_id, task_result=result)
        
        return result
```

👉 **[更多示例和模式](docs/AGENT_INTEGRATION_GUIDE.md)**

---

### Option B: TypeScript/Node.js

```typescript
// 安装：npm install node-fetch
import { CNAAClient } from './examples/cnaa_client/typescript/cnaa_client';

const cnaa = new CNAAClient({
  serverUrl: 'http://localhost:8080',
});

// 从任何 TypeScript 智能体存储记忆
await cnaa.storeMemory({
  agentId: 'typescript-智能体',
  memoryId: '任务-' + Date.now(),
  type: 'long_term',
  content: { 
    task: '数据处理', 
    success: true,
    details: { rows: 100, errors: 0 }
  },
  completionScore: 0.95,
  tags: ['数据处理'],
});

console.log('记忆存储成功!');
```

---

### Option C: 任何语言（通过 HTTP）

```bash
# 发送原始 HTTP 请求（任何支持 HTTP 的语言）
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "tool": "cnaa_store_memory",
    "arguments": {
      "agent_id": "java-智能体",
      "memory_id": "mem-001",
      "type": "long_term",
      "content": { "description": "来自 Java 智能体的记忆" },
      "completion_score": 1.0
    }
  }'
```

---

## 🛠️ 核心组件

| 模块 | 说明 | 路径 |
|------|------|------|
| **适配器层** | 智能体框架适配器 (mix-ins) | `cnaa/adapters/` |
| **HTTP 客户端** | 语言无关的 HTTP 客户端 | `local/client/` |
| **云端服务** | CNAA MCP Server 实现 | `cloud/server/` |
| **存储** | SQLite/ChromaDB 后端 | `cloud/storage/` |
| **安全** | API Key 认证 | `cnaa/security.py` |
| **工具** | 13 个 MCP 工具定义 | `cnaa/tools.py` |
| **示例** | 集成示例代码 | `examples/` |

---

## 📊 支持的智能体框架

| 框架 | 状态 | 集成方式 | 示例 |
|------|------|---------|------|
| **LangChain** | ✅ 完成 | Mix-in 模式 | [`show_integration_patterns.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/examples/show_integration_patterns.py) |
| **LlamaIndex** | ✅ 完成 | Mix-in 模式 | 参见指南 |
| **AutoGen** | ✅ 完成 | Mix-in 模式 | 参见指南 |
| **CrewAI** | ✅ 完成 | Mix-in 模式 | 参见指南 |
| **TypeScript/Node.js** | ✅ 完成 | HTTP 客户端 | [`cnaa_client.ts`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/examples/cnaa_client/typescript/cnaa_client.ts) |
| **自定义智能体** | ✅ 支持 | 继承 BaseCNAAAdapter | 参见指南 |
| **任何语言** | ✅ 支持 | 直接 HTTP API | curl/fetch/自定义 |

---

## 🔍 API 参考

### MCP 工具列表

| 工具 | 描述 | 权限 |
|------|------|------|
| `cnaa_store_memory` | 存储新记忆 | write |
| `cnaa_get_memory` | 检索特定记忆 | read |
| `cnaa_list_memories` | 列出记忆（带过滤） | read |
| `cnaa_delete_memory` | 删除记忆 | write |
| `cnaa_update_state` | 更新知识状态 | write |
| `cnaa_get_state` | 获取所有状态 | read |
| `cnaa_update_preference` | 更新偏好 | write |
| `cnaa_get_preference` | 获取偏好 | read |
| `cnaa_get_environment` | 获取环境上下文 | read |
| `cnaa_update_environment` | 更新环境 | write |
| `cnaa_list_tags` | 列出可用标签 | read |
| `cnaa_analyze_experience` | 分析经验 | read |
| `cnaa_recall_relevant` | 检索相关记忆 | read |

👉 **[完整工具列表](docs/API_REFERENCE_SCORING.md)**

---

## 🧪 测试与验证

### 运行所有测试

```bash
# 验收测试（推荐）
./scripts/acceptance_test.sh

# 全面测试套件
pytest tests/ -v

# 分布式系统测试
./scripts/run_distributed_tests.sh all

# OpenClaw 集成测试
python tests/test_real_openclaw_integration.py
```

### 集成演示

```bash
# 显示所有集成模式
python examples/show_integration_patterns.py

# 多框架演示
python examples/multi_agent_framework_demo.py

# 简单智能体演示
python examples/simple_agent_demo.py
```

---

## 📚 文档索引

| 文档 | 用途 | 链接 |
|------|------|------|
| **集成指南** | 如何集成各种智能体框架 | [`docs/AGENT_INTEGRATION_GUIDE.md`](docs/AGENT_INTEGRATION_GUIDE.md) |
| **工作原理** | 深入理解适配器机制 | [`docs/AGENT_ADAPTER_WORKING_PRINCIPLES.md`](docs/AGENT_ADAPTER_WORKING_PRINCIPLES.md) |
| **服务测试报告** | 验证测试报告 | [`docs/SERVICE_TEST_REPORT.md`](docs/SERVICE_TEST_REPORT.md) |
| **API 参考** | 完整的工具定义和 schema | [`docs/api-reference-v0.1.md`](docs/api-reference-v0.1.md) |
| **技术实现** | 详细的技术实现说明 | [`docs/technical-implementation.md`](docs/technical-implementation.md) |
| **版本总结** | v0.2 实现总结 | [`docs/V02_FINAL_SUMMARY.md`](docs/V02_FINAL_SUMMARY.md) |

---

## 🎯 核心设计原则

### 1️⃣ **语言无关性**
通过纯 HTTP/JSON 协议，支持任何编程语言

### 2️⃣ **Mix-in 模式**
无需修改继承关系即可添加记忆功能

### 3️⃣ **双端点架构**
云端服务和本地客户端完全分离，独立部署

### 4️⃣ **最小变化原则**
智能体只需添加 5-20 行代码即可启用 CNAA 记忆

### 5️⃣ **可插拔架构**
易于扩展新的存储后端、算法和智能体框架

---

## 🔒 安全特性

- ✅ **API Key 认证**: Bearer Token 方式验证身份
- ✅ **权限控制**: Read/Write 分离
- ✅ **请求验证**: JSON Schema 格式校验
- ✅ **日志记录**: 所有操作可追踪审计

---

## 🔄 更新日志

### v0.2.0 (2026-08-06)
- ✨ **新增**: 通用智能体框架适配器 (LangChain, LlamaIndex, AutoGen, CrewAI)
- ✨ **新增**: 多语言 HTTP 客户端 (TypeScript、Go、Java 就绪)
- ✨ **新增**: Mix-in 模式轻松集成
- ✨ **新增**: 综合集成指南和文档
- 🐛 **修复**: HTTP 通信格式匹配问题
- 🐛 **修复**: 适配器实现的语法错误
- 📚 **文档**: 完整重写，包含详细的架构解释

### v0.1.0 (初始版本)
- 基础 MCP Server 实现
- 记忆、状态、偏好存储
- API Key 认证
- 本地/云端双部署

---

## 🚀 下一步

### 生产部署

```bash
# 1. 配置环境
cp .env.production .env
nano .env

# 2. 启用 HTTPS
# 使用 nginx/Apache 作为反向代理

# 3. 设置数据库备份
./scripts/backup.sh

# 4. 监控健康状态
./scripts/status.sh

# 5. 部署到云端
# Docker/Kubernetes 支持即将推出
```

### 贡献开发

```bash
# 1. Fork 仓库
git fork https://github.com/your-org/CNAA.git

# 2. 创建功能分支
git checkout -b feature/amazing-feature

# 3. 进行修改并测试
pytest tests/ -v

# 4. 提交 PR
git push origin feature/amazing-feature
```

---

## 🤝 社区与支持

- 📖 **[完整文档](docs/)** - 所有技术文档和资源
- 💬 **[GitHub Issues](https://github.com/your-org/CNAA/issues)** - 报告问题或请求功能
- 🌟 **[Star 项目](https://github.com/your-org/CNAA)** - 支持我们发展

---

## 📄 许可证

MIT License - 开源自由使用

---

<div align="center">

**由 CNAA 团队用心 ❤️ 制作**

⭐ **Star 这个项目**如果它帮助你构建更好的智能体！

</div>
