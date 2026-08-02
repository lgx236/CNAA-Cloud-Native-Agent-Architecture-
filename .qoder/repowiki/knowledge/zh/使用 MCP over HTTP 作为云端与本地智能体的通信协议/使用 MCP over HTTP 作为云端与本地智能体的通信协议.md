---
kind: design
name: 使用 MCP over HTTP 作为云端与本地智能体的通信协议
source: session
category: adr
---

# 使用 MCP over HTTP 作为云端与本地智能体的通信协议

_来源：966265f → 90cf9d3 提交周期内记录的编码计划——内容为规划时意图，实现可能滞后或有出入。_

**状态：** accepted

## 背景
CNAA 架构需要统一云端（单一 Server）与多个本地 Agent 实例之间的通信方式，要求支持多地同智能体共享同一云端状态。

## 决策驱动
- 协议统一性
- 跨进程/跨网络通信能力
- MCP 生态兼容性
- Streamable HTTP 的流式传输能力

## 备选方案
- **MCP over HTTP (Streamable HTTP)** — 优点：统一的 MCP 协议、支持流式传输、HTTP 天然跨网络、MCP SDK 原生支持
- **gRPC** _（已否决）_ — 优点：高性能、强类型契约、多语言支持；缺点：需要额外定义 proto schema、与 MCP 生态不兼容、增加实现复杂度
- **REST API** _（已否决）_ — 优点：简单直观、广泛支持；缺点：无流式能力、非 MCP 标准、无法复用 MCP 工具生态

## 决策
采用 MCP 协议的 Streamable HTTP 传输层，云端通过 MCP Server 暴露工具，本地 Agent 通过 MCP Client 调用，整条链路统一为 MCP 协议。

## 影响
所有云端-本地交互都遵循 MCP 规范，便于扩展新工具；但依赖 MCP Python SDK 的版本稳定性；Streamable HTTP 相比 gRPC 在性能上有所取舍。