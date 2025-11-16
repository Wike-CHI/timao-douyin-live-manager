import { buildServiceUrl } from "./apiConfig";
import { fetchJsonWithAuth } from "./http";
import { apiCall } from "../utils/error-handler";
import type {
  DouyinRelayStatus,
  DouyinRelayResponse,
  DouyinStreamEvent,
  StartDouyinRequest,
} from "../types/api-types";

// Re-export types for convenience
export type { DouyinRelayStatus, DouyinStreamEvent } from "../types/api-types";

export interface DouyinStreamHandlers {
  onEvent?: (event: DouyinStreamEvent) => void;
  onError?: (event: Event) => void;
  onOpen?: (event: Event) => void;
}

export const startDouyinRelay = async (
  liveId: string,
  cookie?: string,
): Promise<DouyinRelayResponse> => {
  const body: StartDouyinRequest = { live_id: liveId };
  if (cookie) {
    body.cookie = cookie;
  }

  return apiCall(
    () =>
      fetchJsonWithAuth("douyin", "/api/douyin/start", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    "启动抖音中继",
  );
};

export const stopDouyinRelay = async (): Promise<DouyinRelayResponse> => {
  return apiCall(
    () =>
      fetchJsonWithAuth("douyin", "/api/douyin/stop", {
        method: "POST",
      }),
    "停止抖音中继",
  );
};

export const getDouyinRelayStatus = async (): Promise<DouyinRelayStatus> => {
  return apiCall(
    () =>
      fetchJsonWithAuth("douyin", "/api/douyin/status", {
        method: "GET",
      }),
    "获取抖音中继状态",
  );
};

export const openDouyinStream = (
  handlers: DouyinStreamHandlers,
): EventSource => {
  const streamUrl = buildServiceUrl("douyin", "/api/douyin/stream");
  const source = new EventSource(streamUrl);

  if (handlers.onOpen) {
    source.onopen = handlers.onOpen;
  }
  if (handlers.onError) {
    source.onerror = handlers.onError;
  }
  source.onmessage = (event) => {
    if (!handlers.onEvent) {
      return;
    }
    try {
      const data = JSON.parse(event.data) as DouyinStreamEvent;
      handlers.onEvent(data);
    } catch (error) {
      console.error("解析 Douyin SSE 消息失败:", error);
    }
  };

  return source;
};

export const updateDouyinPersist = async (payload: {
  persist_enabled?: boolean;
  persist_root?: string;
}) => {
  return apiCall(
    () =>
      fetchJsonWithAuth("douyin", "/api/douyin/web/persist", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    "更新抖音持久化配置",
  );
};
