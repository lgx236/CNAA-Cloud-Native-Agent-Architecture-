---
kind: design
name: 采用 MCP over HTTP 作为云端与本地运行时通信协议
source: session
category: adr
---

# 采用 MCP over HTTP 作为云端与本地运行时通信协议

_来源：461fe1c → 966265f 提交周期内记录的编码计划——内容为规划时意图，实现可能滞后或有出入。_

**状态：** accepted

## 背景
CNAA 需要支持多 Agent 实例（本地）与单一云端服务之间的记忆和状态同步。传统 RPC 或自定义协议会增加实现复杂度，且不利于跨语言扩展。

## 决策驱动
- 统一协议降低集成成本
- MCP 官方 SDK 成熟度
- Streamable HTTP 传输的标准化
- 多地同智能体共享云端状态的架构需求

## 备选方案
- **MCP over HTTP (Streamable HTTP)** — 优点：官方标准协议、JSON in/out 哑服务原则、天然支持多客户端、HTTP 生态成熟
- **gRPC/Protobuf** _（已否决）_ — 优点：高性能、强类型契约；缺点：需要额外依赖、跨语言转换复杂、不符合 CNAA 的 JSON 数据模型设计
- **自定义 REST API** _（已否决）_ — 优点：简单直接；缺点：缺乏标准化工具链、版本管理复杂、无法复用 MCP 生态

## 决策
采用 MCP Python SDK 实现 Streamable HTTP 传输，云端暴露 cnaa_store_memory、cnaa_get_memory、cnaa_list_memories、cnaa_tag_short_term、cnaa_get_state、cnaa_update_state、cnaa_get_preference、cnaa_update_preference、cnaa_get_environment、cnaa_update_environment 等工具，本地通过 MCP Client 调用。

## 影响
所有云端-本地交互统一为 MCP 协议，简化了客户端实现；但增加了 MCP 协议栈的依赖；工具定义成为核心交付物，需要严格维护 schema 一致性。