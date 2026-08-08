# CNAA - Cloud-Native Agent Architecture

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.12+-blue)

## 🌐 通用 Agent 记忆基础设施

**CNAA (Cloud-Native Agent Architecture)** 是一个语言无关的分布式记忆系统，为**任意 Agent 框架**提供云端经验存储和共享能力。

[📖 完整文档](docs/) • [🚀 快速开始](#快速开始) • [🔧 集成指南](docs/AGENT_INTEGRATION_GUIDE.md) • [🎯 工作原理](docs/AGENT_ADAPTER_WORKING_PRINCIPLES.md)

</div>

---

## ⚡ 一句话介绍

**CNAA 让任何 Agent（无论用 Python、TypeScript、Go 还是其他语言编写）都能通过简单的 HTTP API，将工作经验持久化存储到云端，供所有 Agent 共享和学习！**

---

## 🎯 核心功能

### ✅ 主要特性

- **🌍 语言无关性**: 支持 Python, TypeScript, Go, Java 等任何 HTTP 支持的语言
- **🤝 多框架兼容**: 原生支持 LangChain, LlamaIndex, AutoGen, CrewAI 等主流框架
- **☁️ 云端存储**: 基于 SQLite 或 ChromaDB 的持久化记忆存储
- **🔒 安全认证**: API Key + Bearer Token 双重认证机制
- **⚡ 高性能**: HTTP/JSON 标准化协议，低延迟响应
- **🔌 可插拔架构**: 易于扩展新的 Agent 框架和存储后端

### 🚀 使用场景

| 场景 | 描述 | 价值 |
|------|------|------|
| **跨 Agent 协作** | 不同 Agent 共享经验和知识 | 避免重复学习，提升整体效率 |
| **长期记忆** | Agent 保留历史交互信息 | 持续改进，积累专业领域知识 |
| **分布式部署** | Agent 运行在多个机器/云环境 | 独立部署，统一记忆管理 |
| **框架迁移** | 从一个框架迁移到另一个框架 | 保持记忆连续性，无缝切换 |
| **多语言 Agent** | Python + TypeScript + Go 混合部署 | 利用各语言优势，统一记忆层 |

---

## 🏗️ 架构概览

```
┌──────────────────────────────────────────────┐
│           YOUR AGENT APPLICATIONS            │
│                                              │
│  ┌─────────┐  ┌─────────┐  ┌────────────┐  │
│  │LangChain│  │LlamaIndex│ │ AutoGen    │  │
│  │ (Python)│  │(Python) │  │(Python)    │  │
│  └────┬────┘  └────┬────┘  └─────┬──────┘  │
│       │            │              │         │
│  ┌────┴────────────┴──────────────┴────────┐│
│  │          CNAA Adapter Mixins             ││
│  │  • LangChainCNAAMixin                   ││
│  │  • LlamaIndexCNAAMixin                  ││
│  │  • AutoGencNAAAMixin                    ││
│  └───────────────┬────────────────────────┘│
└──────────────────┼─────────────────────────┘
                   │ HTTP POST /mcp
                   ▼
┌──────────────────────────────────────────────┐
│           CNAA CLOUD SERVER                  │
│                                              │
│  • MCP Router                        🔒      │
│  • Authentication (API Key)                  │
│  • Storage Backends:                         │
│    - SQLite (default)                        │
│    - ChromaDB (optional)                     │
└──────────────────────────────────────────────┘

Works with TypeScript, Go, Java and ANY language via HTTP!
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
# Copy example config
cp .env.example .env

# Edit configuration
nano .env
```

**.env 示例**:
```ini
# Server Configuration
CNAA_SERVER_PORT=8080
CNAA_SERVER_HOST=0.0.0.0

# Memory Storage (SQLite default)
MEMORY_STORAGE_TYPE=sqlite
MEMORY_STORAGE_PATH=./cnaa_memories.db

# State Storage
STATE_STORAGE_TYPE=sqlite
STATE_STORAGE_PATH=./cnaa_states.db

# Security (Optional)
API_KEY_ENABLED=true
API_KEYS=admin,developer,test
```

### Step 3: 启动服务器

```bash
# Quick start
./scripts/start.sh

# Or manually
python server.py --host 0.0.0.0 --port 8080
```

**验证服务**:
```bash
curl http://localhost:8080/health
# Returns: {"status": "healthy"}
```

---

## 🤖 与你的 Agent 集成

### Option A: Python Frameworks (Recommended)

#### 使用 LangChain

```python
# Install: pip install langchain openai
from langchain.agents import AgentExecutor
from cnaa.adapters.langchain import LangChainCNAAMixin

class MyAgent(LangChainCNAAMixin, AgentExecutor):
    agent_id = "my-langchain-agent"
    
    def _call(self, inputs, *args, **kwargs):
        # Run original logic
        result = super()._call(inputs, *args, **kwargs)
        
        # Store experience automatically
        self.on_task_complete(
            agent_id=self.agent_id,
            task_result=result,
            tags=["langchain"],
            completion_score=0.95
        )
        
        return result

# Usage
agent = MyAgent.from_llm_and_tools(llm, tools)
response = agent.run("Analyze sales data")
```

#### 使用 LlamaIndex

```python
from llama_index.agent import OpenAIAgent
from cnaa.adapters.llamaindex import LlamaIndexCNAAMixin

class MyChatAgent(LlamaIndexCNAAMixin, OpenAIAgent):
    agent_id = "my-llama-agent"
    
    def chat(self, message: str):
        response = super().chat(message)
        
        # Log conversation
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
    agent_id = "my-autogen-agent"
    
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

**更简单的用法 - 自定义基础类**:

```python
from cnaa.adapters import BaseCNAAAdapter

class CustomAgent(BaseCNAAAdapter):
    agent_id = "custom-agent"
    
    def process_request(self, request):
        result = self.execute(request)
        
        # Automatically store in CNAA
        self.on_task_complete(agent_id=self.agent_id, task_result=result)
        
        return result
```

👉 **[更多示例和模式](docs/AGENT_INTEGRATION_GUIDE.md)**

---

### Option B: TypeScript/Node.js

```typescript
// Install: npm install node-fetch
import { CNAAClient } from './examples/cnaa_client/typescript/cnaa_client';

const cnaa = new CNAAClient({
  serverUrl: 'http://localhost:8080',
});

// Store memory from any TypeScript agent
await cnaa.storeMemory({
  agentId: 'typescript-agent',
  memoryId: 'task-' + Date.now(),
  type: 'long_term',
  content: { 
    task: 'Data processing', 
    success: true,
    details: { rows: 100, errors: 0 }
  },
  completionScore: 0.95,
  tags: ['data-processing'],
});

console.log('Memory stored successfully!');
```

---

### Option C: Any Language (via HTTP)

```bash
# Send raw HTTP request (any language that supports HTTP)
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "tool": "cnaa_store_memory",
    "arguments": {
      "agent_id": "java-agent",
      "memory_id": "mem-001",
      "type": "long_term",
      "content": { "description": "Memory from Java agent" },
      "completion_score": 1.0
    }
  }'
```

---

## 🛠️ 核心组件

| 模块 | 说明 | 路径 |
|------|------|------|
| **Adapter Layer** | Agent framework adapters (mix-ins) | `cnaa/adapters/` |
| **HTTP Client** | Language-agnostic HTTP client | `local/client/` |
| **Cloud Server** | CNAA MCP Server implementation | `cloud/server/` |
| **Storage** | SQLite/ChromaDB backends | `cloud/storage/` |
| **Security** | API Key authentication | `cnaa/security.py` |
| **Tools** | 13 MCP tool definitions | `cnaa/tools.py` |
| **Examples** | Integration examples | `examples/` |

---

## 📊 支持的 Agent 框架

| Framework | Status | Integration Type | Example |
|-----------|--------|------------------|---------|
| **LangChain** | ✅ Complete | Mix-in pattern | [`show_integration_patterns.py`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/examples/show_integration_patterns.py) |
| **LlamaIndex** | ✅ Complete | Mix-in pattern | See guide |
| **AutoGen** | ✅ Complete | Mix-in pattern | See guide |
| **CrewAI** | ✅ Complete | Mix-in pattern | See guide |
| **TypeScript/Node.js** | ✅ Complete | HTTP Client | [`cnaa_client.ts`](file:///root/CNAA-Cloud-Native-Agent-Architecture-/examples/cnaa_client/typescript/cnaa_client.ts) |
| **Custom Agents** | ✅ Supported | Extend BaseCNAAAdapter | See guide |
| **Any Language** | ✅ Supported | HTTP API Directly | curl/fetch/custom |

---

## 🔍 API Reference

### MCP Tools

| Tool | Description | Permissions |
|------|-------------|-------------|
| `cnaa_store_memory` | Store a new memory | write |
| `cnaa_get_memory` | Retrieve specific memory | read |
| `cnaa_list_memories` | List memories with filters | read |
| `cnaa_delete_memory` | Delete a memory | write |
| `cnaa_update_state` | Update knowledge state | write |
| `cnaa_get_state` | Get all states | read |
| `cnaa_update_preference` | Update preference | write |
| `cnaa_get_preference` | Get preferences | read |
| `cnaa_get_environment` | Get environment context | read |
| `cnaa_update_environment` | Update environment | write |
| `cnaa_list_tags` | List available tags | read |
| `cnaa_analyze_experience` | Analyze experiences | read |
| `cnaa_recall_relevant` | Recall relevant memories | read |

👉 **[完整工具列表](docs/API_REFERENCE_SCORING.md)**

---

## 🧪 测试与验证

### 运行所有测试

```bash
# Acceptance test (recommended)
./scripts/acceptance_test.sh

# Comprehensive test suite
pytest tests/ -v

# Distributed system tests
./scripts/run_distributed_tests.sh all

# OpenClaw integration test
python tests/test_real_openclaw_integration.py
```

### 集成演示

```bash
# Show all integration patterns
python examples/show_integration_patterns.py

# Multi-framework demo
python examples/multi_agent_framework_demo.py

# Simple agent demo
python examples/simple_agent_demo.py
```

---

## 📚 文档索引

| 文档 | 用途 | 链接 |
|------|------|------|
| **集成指南** | 如何集成各种 Agent 框架 | [`docs/AGENT_INTEGRATION_GUIDE.md`](docs/AGENT_INTEGRATION_GUIDE.md) |
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
Agent 只需添加 5-20 行代码即可启用 CNAA 记忆

### 5️⃣ **可插拔架构**
易于扩展新的存储后端、算法和 Agent 框架

---

## 🔒 安全特性

- ✅ **API Key 认证**: Bearer Token 方式验证身份
- ✅ **权限控制**: Read/Write 分离
- ✅ **请求验证**: JSON Schema 格式校验
- ✅ **日志记录**: 所有操作可追踪审计

---

## 🔄 更新日志

### v0.2.0 (2026-08-06)
- ✨ **新增**: Universal Agent Framework Adapters (LangChain, LlamaIndex, AutoGen, CrewAI)
- ✨ **新增**: Multi-language HTTP Clients (TypeScript, Go, Java ready)
- ✨ **新增**: Mix-in Pattern for easy integration
- ✨ **新增**: Comprehensive integration guides and documentation
- 🐛 **修复**: HTTP communication format matching
- 🐛 **修复**: Syntax errors in adapter implementations
- 📚 **文档**: Complete rewrite with detailed architecture explanations

### v0.1.0 (Initial Release)
- Basic MCP Server implementation
- Memory, State, Preference storage
- API Key authentication
- Local/Cloud dual deployment

---

## 🚀 下一步

### 生产部署

```bash
# 1. Configure environment
cp .env.production .env
nano .env

# 2. Enable HTTPS
# Use nginx/Apache as reverse proxy

# 3. Setup database backup
./scripts/backup.sh

# 4. Monitor health
./scripts/status.sh

# 5. Deploy to cloud
# Docker/Kubernetes support coming soon
```

### 贡献开发

```bash
# 1. Fork repository
git fork https://github.com/your-org/CNAA.git

# 2. Create feature branch
git checkout -b feature/amazing-feature

# 3. Make changes and test
pytest tests/ -v

# 4. Submit PR
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

**Made with ❤️ by the CNAA Team**

⭐ **Star this project** if it helps you build better agents!

</div>
