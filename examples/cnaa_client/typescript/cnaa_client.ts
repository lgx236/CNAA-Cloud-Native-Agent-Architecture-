/**
 * CNAA Client - TypeScript/Node.js Implementation
 * 
 * This is a production-ready HTTP client for interacting with CNAA Cloud Server.
 * Works with any JavaScript/TypeScript agent framework (OpenClaw, LangChain.js, etc.)
 * 
 * Installation:
 *   npm install node-fetch
 *   
 * Usage:
 *   import { CNAAClient } from './cnaa_client';
 *   
 *   const cnaa = new CNAAClient({
 *     serverUrl: 'http://localhost:8080',
 *     apiKey: 'your-api-key' // optional
 *   });
 *   
 *   // Store memory
 *   await cnaa.storeMemory({
 *     agentId: 'my-agent',
 *     memoryId: 'task-001',
 *     type: 'long_term',
 *     content: { task: 'data processing', success: true },
 *     completionScore: 0.95
 *   });
 */

import fetch from 'node-fetch';

export interface StoreMemoryRequest {
  agentId: string;
  memoryId: string;
  type: 'long_term' | 'short_term';
  content: Record<string, any>;
  tags?: string[];
  completionScore: number;
  metadata?: Record<string, any>;
}

export interface MemoryResponse {
  status: string;
  memoryId?: string;
  memories?: Array<{
    memory_id: string;
    type: string;
    content: Record<string, any>;
    timestamp: string;
  }>;
  [key: string]: any;
}

export interface CNAAClientOptions {
  serverUrl?: string;
  apiKey?: string;
  timeout?: number;
}

export class CNAAClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;

  constructor(options: CNAAClientOptions = {}) {
    this.baseUrl = options.serverUrl || 'http://localhost:8080';
    this.apiKey = options.apiKey;
    this.timeout = options.timeout || 30000;
  }

  private async request<T>(method: string, endpoint: string, data?: any): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const response = await fetch(url, {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined,
      signal: AbortSignal.timeout(this.timeout),
    });

    return response.json();
  }

  /**
   * Store a memory in CNAA cloud
   */
  async storeMemory(request: StoreMemoryRequest): Promise<MemoryResponse> {
    return this.request<MemoryResponse>('POST', '/mcp', {
      tool: 'cnaa_store_memory',
      arguments: {
        agent_id: request.agentId,
        memory_id: request.memoryId,
        type: request.type,
        content: request.content,
        tags: request.tags || [],
        completion_score: request.completionScore,
        metadata: request.metadata || {},
      },
    });
  }

  /**
   * Retrieve a specific memory
   */
  async getMemory(agentId: string, memoryId: string): Promise<MemoryResponse> {
    return this.request<MemoryResponse>('POST', '/mcp', {
      tool: 'cnaa_get_memory',
      arguments: { agent_id: agentId, memory_id: memoryId },
    });
  }

  /**
   * List memories for an agent
   */
  async listMemories(
    agentId: string,
    filters?: {
      type?: 'long_term' | 'short_term';
      tags?: string[];
      limit?: number;
    }
  ): Promise<MemoryResponse> {
    return this.request<MemoryResponse>('POST', '/mcp', {
      tool: 'cnaa_list_memories',
      arguments: {
        agent_id: agentId,
        ...(filters?.type && { type: filters.type }),
        ...(filters?.tags && { tags: filters.tags }),
        ...(filters?.limit !== undefined && { limit: filters.limit }),
      },
    });
  }

  /**
   * Delete a memory
   */
  async deleteMemory(agentId: string, memoryId: string): Promise<MemoryResponse> {
    return this.request<MemoryResponse>('POST', '/mcp', {
      tool: 'cnaa_delete_memory',
      arguments: { agent_id: agentId, memory_id: memoryId },
    });
  }

  /**
   * Update knowledge state
   */
  async updateState(
    agentId: string,
    stateId: string,
    category: 'knowledge' | 'preference' | 'environment',
    content: Record<string, any>
  ): Promise<MemoryResponse> {
    return this.request<MemoryResponse>('POST', '/mcp', {
      tool: 'cnaa_update_state',
      arguments: {
        agent_id: agentId,
        state_id: stateId,
        category,
        content,
      },
    });
  }

  /**
   * Get all states for an agent
   */
  async getState(agentId: string): Promise<MemoryResponse> {
    return this.request<MemoryResponse>('POST', '/mcp', {
      tool: 'cnaa_get_state',
      arguments: { agent_id: agentId },
    });
  }

  /**
   * Update preference
   */
  async updatePreference(
    agentId: string,
    preferenceId: string,
    key: string,
    value: Record<string, any>,
    importance: number = 0.0
  ): Promise<MemoryResponse> {
    return this.request<MemoryResponse>('POST', '/mcp', {
      tool: 'cnaa_update_preference',
      arguments: {
        agent_id: agentId,
        preference_id: preferenceId,
        key,
        value,
        importance,
      },
    });
  }

  /**
   * Get environment context
   */
  async getEnvironment(agentId: string): Promise<MemoryResponse> {
    return this.request<MemoryResponse>('POST', '/mcp', {
      tool: 'cnaa_get_environment',
      arguments: { agent_id: agentId },
    });
  }

  /**
   * Update environment context
   */
  async updateEnvironment(
    agentId: string,
    envId: string,
    context: Record<string, any>
  ): Promise<MemoryResponse> {
    return this.request<MemoryResponse>('POST', '/mcp', {
      tool: 'cnaa_update_environment',
      arguments: { agent_id: agentId, env_id: envId, context },
    });
  }

  /**
   * Check server health
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      return response.status === 200;
    } catch {
      return false;
    }
  }
}

// Example usage
if (require.main === module) {
  (async () => {
    const cnaa = new CNAAClient({
      serverUrl: 'http://localhost:8080',
    });

    // Check connection
    if (await cnaa.healthCheck()) {
      console.log('Connected to CNAA Cloud!');
    } else {
      console.log('Cannot connect to CNAA Cloud');
      process.exit(1);
    }

    // Store a memory
    const result = await cnaa.storeMemory({
      agentId: 'typescript-agent-001',
      memoryId: 'task-' + Date.now(),
      type: 'long_term',
      content: {
        task: 'Processed user data',
        success: true,
        details: { rows: 100, errors: 0 },
      },
      tags: ['data-processing'],
      completionScore: 0.95,
    });

    console.log('Stored memory:', result);

    // List memories
    const memories = await cnaa.listMemories('typescript-agent-001');
    console.log('Memories:', memories);
  })();
}

export default CNAAClient;
