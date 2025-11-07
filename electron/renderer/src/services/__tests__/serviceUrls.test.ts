import { describe, it, expect, vi, beforeEach } from 'vitest';

const fetchMock = vi.fn();
vi.stubGlobal('fetch', fetchMock);

const authHeaders = {
  Authorization: 'Bearer test-token',
  'Content-Type': 'application/json',
};

vi.mock('../authService', () => ({
  default: {
    getAuthHeaders: vi.fn().mockResolvedValue(authHeaders),
    ensureValidToken: vi.fn().mockResolvedValue('mock-token'),
  },
}));

const createJsonResponse = (data: unknown) =>
  ({
    ok: true,
    json: async () => data,
  }) as Response;

describe('buildServiceUrl 基础能力', () => {
  it('支持覆盖 baseUrl 并处理多余斜杠', async () => {
    const { buildServiceUrl } = await import('../apiConfig');

    expect(buildServiceUrl('main', '/health')).toBe('http://127.0.0.1:9030/health');
    expect(buildServiceUrl('main', 'health')).toBe('http://127.0.0.1:9030/health');
    expect(buildServiceUrl('main', '/api/test', 'https://api.example/')).toBe('https://api.example/api/test');
    expect(buildServiceUrl('douyin', 'status', 'https://relay.example')).toBe('https://relay.example/status');
  });
});

describe('服务调用统一使用 buildServiceUrl', () => {
  beforeEach(() => {
    fetchMock.mockReset();
    fetchMock.mockResolvedValue(createJsonResponse({ success: true }));
  });

  it('payment.getPlan 使用主服务域名构造 URL', async () => {
    const { getPlan } = await import('../payment');

    await getPlan('42');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('http://127.0.0.1:9030/api/payment/plans/42');
  });

  it('douyin.startDouyinRelay 支持外部覆盖 baseUrl', async () => {
    const { startDouyinRelay } = await import('../douyin');

    await startDouyinRelay('LIVE123', 'cookie', 'https://relay.example');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('https://relay.example/api/douyin/start');
  });

  it('liveReport.startLiveReport 支持外部覆盖 baseUrl', async () => {
    const { startLiveReport } = await import('../liveReport');

    await startLiveReport('https://douyin.example/live', 15, 'https://report.example');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('https://report.example/api/report/live/start');
  });

  it('liveSession.getSessionStatus 默认使用主服务域名', async () => {
    const { getSessionStatus } = await import('../liveSession');

    await getSessionStatus();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('http://127.0.0.1:9030/api/live_session/status');
  });

  it('ai.startAILiveAnalysis 支持覆盖 baseUrl', async () => {
    const { startAILiveAnalysis } = await import('../ai');

    await startAILiveAnalysis({}, 'https://ai.example');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('https://ai.example/api/ai/live/start');
  });
});

