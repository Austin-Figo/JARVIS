// Configurable API base URL - can be overridden at runtime via window.__JARVIS_CONFIG__
const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined' && window.__JARVIS_CONFIG__?.apiBaseUrl) {
    return window.__JARVIS_CONFIG__.apiBaseUrl;
  }
  return import.meta.env.VITE_JARVIS_API_URL ?? 'http://127.0.0.1:8765';
};

export interface CommandResult {
  ok: boolean;
  message: string;
  action: 'scan' | 'status' | 'time' | 'settings' | 'apps' | 'gesture' | 'help' | null;
  data?: {
    scan_results?: ScanResult[];
    [key: string]: unknown;
  };
  requires_confirmation?: boolean;
  confirmation?: { title: string; message: string; action: string; target: string };
}

export interface ScanResult {
  category: string;
  value: string;
  status: 'optimal' | 'good' | 'secure' | 'info' | 'warning' | 'critical';
}

export interface SystemMetrics {
  cpu_percent: number;
  memory_percent: number;
  memory_used_bytes: number;
  memory_total_bytes: number;
  uptime_seconds: number;
  network_percent: number | null;
  network_mbps: number | null;
  network_receive_mbps: number | null;
  network_send_mbps: number | null;
  gpu_percent: number | null;
  temperature_celsius: number | null;
  processes: { name: string; cpu: number | null; memory: number | null }[];
}

export interface HealthResponse {
  ok: boolean;
  status: string;
  name: string;
}

export interface VoiceControlResponse {
  ok: boolean;
  listening: boolean;
  message: string;
}

export interface SettingsResponse {
  ok: boolean;
  settings?: Record<string, unknown>;
  message?: string;
}

export interface MemoryItem {
  id: string;
  title: string;
  content: string;
  tags: string[];
  timestamp: number;
  synced: boolean;
}

export interface MemoryListResponse {
  ok: boolean;
  memories: MemoryItem[];
}

export interface MemoryResponse {
  ok: boolean;
  memory: MemoryItem;
}

export interface TagsResponse {
  ok: boolean;
  tags: string[];
}

interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  shouldRetry?: (error: Error) => boolean;
}

async function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function requestWithRetry<T>(
  path: string,
  init?: RequestInit,
  options: RetryOptions = {}
): Promise<T> {
  const {
    maxRetries = 3,
    baseDelay = 500,
    maxDelay = 5000,
    shouldRetry = (error: Error) => error.name === 'TypeError' || error.message.includes('network')
  } = options;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(`${getApiBaseUrl()}${path}`, {
        ...init,
        headers: { 'Content-Type': 'application/json', ...init?.headers },
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message ?? 'JARVIS service request failed.');
      return payload as T;
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      if (attempt < maxRetries && shouldRetry(lastError)) {
        const delay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
        await sleep(delay);
        continue;
      }
      throw lastError;
    }
  }

  throw lastError;
}

export async function checkHealth(): Promise<HealthResponse> {
  return requestWithRetry<HealthResponse>('/api/health', { method: 'GET' }, {
    maxRetries: 10,
    baseDelay: 1000,
    maxDelay: 3000,
  });
}

export function sendCommand(command: string, source = 'console') {
  return requestWithRetry<CommandResult>('/api/commands', {
    method: 'POST',
    body: JSON.stringify({ command, source }),
  });
}

export interface ChatResult {
  ok: boolean;
  message: string;
  action: 'scan' | 'status' | 'time' | 'settings' | 'apps' | 'gesture' | 'help' | null;
  data?: unknown;
  requires_confirmation?: boolean;
  confirmation?: { title: string; message: string; action: string; target: string };
}

export function sendChatMessage(message: string, history?: { role: string; content: string }[], source = 'voice') {
  return requestWithRetry<ChatResult>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, history, source }),
  });
}

export function confirmCommand(action: string, target: string, source = 'console') {
  return requestWithRetry<CommandResult>('/api/commands/confirm', { method: 'POST', body: JSON.stringify({ action, target, source }) });
}

export function cancelCommand(action: string, target: string, source = 'console') {
  return requestWithRetry<{ ok: boolean; message: string }>('/api/commands/cancel', { method: 'POST', body: JSON.stringify({ action, target, source }) });
}

export function getSystemMetrics() {
  return requestWithRetry<SystemMetrics>('/api/system/metrics');
}

export function startVoiceRecognition() {
  return requestWithRetry<VoiceControlResponse>('/api/voice/start', { method: 'POST' });
}

export function stopVoiceRecognition() {
  return requestWithRetry<VoiceControlResponse>('/api/voice/stop', { method: 'POST' });
}

export async function getSettings() {
  return requestWithRetry<SettingsResponse>('/api/settings', { method: 'GET' });
}

export async function saveSettings(settings: Record<string, unknown>) {
  return requestWithRetry<SettingsResponse>('/api/settings', {
    method: 'POST',
    body: JSON.stringify(settings),
  });
}

export async function getMemories() {
  return requestWithRetry<MemoryListResponse>('/api/memory', { method: 'GET' });
}

export async function getMemory(id: string) {
  return requestWithRetry<MemoryResponse>(`/api/memory/${id}`, { method: 'GET' });
}

export async function createMemory(title: string, content: string, tags: string[] = [], synced = false) {
  return requestWithRetry<MemoryResponse>('/api/memory', {
    method: 'POST',
    body: JSON.stringify({ title, content, tags, synced }),
  });
}

export async function updateMemory(id: string, updates: Partial<MemoryItem>) {
  return requestWithRetry<MemoryResponse>(`/api/memory/${id}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export async function deleteMemory(id: string) {
  return requestWithRetry<{ ok: boolean; message: string }>(`/api/memory/${id}`, {
    method: 'DELETE',
  });
}

export async function getMemoryTags() {
  return requestWithRetry<TagsResponse>('/api/memory/tags', { method: 'GET' });
}

export async function speakText(text: string, rate?: number, volume?: number) {
  return requestWithRetry<{ ok: boolean; message: string }>('/api/voice/speak', {
    method: 'POST',
    body: JSON.stringify({ text, rate, volume }),
  });
}

export async function stopSpeech() {
  return requestWithRetry<{ ok: boolean; message: string }>('/api/voice/stop_speech', {
    method: 'POST',
  });
}

export async function getWakeStatus() {
  return requestWithRetry<{ ok: boolean; running: boolean; phrase: string }>('/api/wake/status', {
    method: 'GET',
  });
}

export async function startWakeDetection() {
  return requestWithRetry<{ ok: boolean; message: string }>('/api/wake/start', {
    method: 'POST',
  });
}

export async function stopWakeDetection() {
  return requestWithRetry<{ ok: boolean; message: string }>('/api/wake/stop', {
    method: 'POST',
  });
}

// Export for testing/configuration
export { getApiBaseUrl };
