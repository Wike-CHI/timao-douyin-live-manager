import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const fetchMock = vi.fn();

const apiCallMock = vi.hoisted(() =>
  vi.fn(async (fetchFn: () => Promise<Response>, prefix?: string) => {
    const response = await fetchFn();
    // 模拟真实 apiCall 行为，返回解析后的 JSON
    return response.json();
  })
);

vi.stubGlobal('fetch', fetchMock);

vi.mock('../../utils/error-handler', () => ({
  apiCall: apiCallMock,
}));

const authHeaders = { Authorization: 'Bearer mock-token', 'Content-Type': 'application/json' };

vi.mock('../authService', () => ({
  default: {
    getAuthHeaders: vi.fn().mockResolvedValue(authHeaders),
  },
}));

describe('liveAudio service with unified error handling', () => {
  beforeEach(() => {
    fetchMock.mockReset();
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true }),
    } as Response);
    apiCallMock.mockClear();
  });

  afterEach(() => {
    vi.resetModules();
  });

  it('startLiveAudio 仍然按预期发送请求并通过 apiCall 处理响应', async () => {
    const { startLiveAudio } = await import('../liveAudio');

    const payload = {
      live_url: 'https://douyin.example/live/123',
      chunk_duration: 0.8,
      vad_min_silence_sec: 0.4,
    };

    const result = await startLiveAudio(payload);

    expect(result).toEqual({ success: true });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('http://127.0.0.1:11111/api/live_audio/start');
    expect(options?.method).toBe('POST');
    expect(options?.headers).toMatchObject(authHeaders);

    const requestBody = JSON.parse(String(options?.body));
    expect(requestBody).toMatchObject({
      live_url: payload.live_url,
      chunk_duration: payload.chunk_duration,
      vad_min_silence_sec: payload.vad_min_silence_sec,
    });

    expect(apiCallMock).toHaveBeenCalledTimes(1);
    expect(apiCallMock.mock.calls[0][1]).toBe('启动实时转写');
  });

  it('stopLiveAudio 使用统一错误处理，调用 POST /stop', async () => {
    const { stopLiveAudio } = await import('../liveAudio');

    await stopLiveAudio();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('http://127.0.0.1:11111/api/live_audio/stop');
    expect(options?.method).toBe('POST');
    expect(options?.headers).toMatchObject(authHeaders);

    expect(apiCallMock).toHaveBeenCalledTimes(1);
    expect(apiCallMock.mock.calls[0][1]).toBe('停止实时转写');
  });
});

