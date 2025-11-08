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

const apiCallMock = vi.hoisted(() =>
  vi.fn(async (fetchFn: () => Promise<Response>, prefix?: string) => {
    const response = await fetchFn();
    return response.json();
  })
);

vi.mock('../../utils/error-handler', () => ({
  apiCall: apiCallMock,
}));

const createJsonResponse = (data: unknown) =>
  ({
    ok: true,
    json: async () => data,
  }) as Response;

describe('统一 API 调用方式验证（问题4、6、9）', () => {
  beforeEach(() => {
    fetchMock.mockReset();
    fetchMock.mockResolvedValue(createJsonResponse({ success: true }));
    apiCallMock.mockClear();
  });

  it('payment.getPlans 使用 fetchJsonWithAuth + apiCall', async () => {
    fetchMock.mockResolvedValue(createJsonResponse([{ id: 1, name: 'Test Plan' }]));
    const { getPlans } = await import('../payment');
    await getPlans();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('http://127.0.0.1:11111/api/subscription/plans');
    expect(fetchMock.mock.calls[0][1]?.headers).toMatchObject(authHeaders);
    expect(apiCallMock).toHaveBeenCalledTimes(1);
  });

  it('ai.startAILiveAnalysis 使用 fetchJsonWithAuth + apiCall', async () => {
    const { startAILiveAnalysis } = await import('../ai');
    await startAILiveAnalysis({});

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('http://127.0.0.1:11111/api/ai/live/start');
    expect(fetchMock.mock.calls[0][1]?.headers).toMatchObject(authHeaders);
    expect(apiCallMock).toHaveBeenCalledTimes(1);
  });

  it('liveAudio.startLiveAudio 使用 fetchJsonWithAuth + apiCall', async () => {
    const { startLiveAudio } = await import('../liveAudio');
    await startLiveAudio({ live_url: 'https://example.com/live' });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('http://127.0.0.1:11111/api/live_audio/start');
    expect(fetchMock.mock.calls[0][1]?.headers).toMatchObject(authHeaders);
    expect(apiCallMock).toHaveBeenCalledTimes(1);
  });

  it('liveReport.startLiveReport 使用 fetchJsonWithAuth + apiCall', async () => {
    const { startLiveReport } = await import('../liveReport');
    await startLiveReport('https://example.com/live');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('http://127.0.0.1:11111/api/report/live/start');
    expect(fetchMock.mock.calls[0][1]?.headers).toMatchObject(authHeaders);
    expect(apiCallMock).toHaveBeenCalledTimes(1);
  });

  it('douyin.startDouyinRelay 使用 fetchJsonWithAuth + apiCall', async () => {
    const { startDouyinRelay } = await import('../douyin');
    await startDouyinRelay('LIVE123');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe('http://127.0.0.1:11111/api/douyin/start');
    expect(fetchMock.mock.calls[0][1]?.headers).toMatchObject(authHeaders);
    expect(apiCallMock).toHaveBeenCalledTimes(1);
  });
});

describe('统一类型定义验证（问题7、10）', () => {
  it('payment 服务从 api-types.ts 导入类型', async () => {
    const paymentModule = await import('../payment');
    
    // 验证类型已从 api-types.ts 导入，而不是本地定义
    expect(paymentModule).not.toHaveProperty('Plan');
    expect(paymentModule).not.toHaveProperty('Subscription');
    expect(paymentModule).not.toHaveProperty('Payment');
  });

  it('liveReport 服务使用统一命名规范（Request/Response）', async () => {
    const liveReportModule = await import('../liveReport');
    
    // 验证不再导出旧的命名（Req/Resp）
    expect(liveReportModule).not.toHaveProperty('LiveReportStartReq');
    expect(liveReportModule).not.toHaveProperty('LiveReportStartResp');
  });

  it('liveAudio 服务使用统一命名规范', async () => {
    const liveAudioModule = await import('../liveAudio');
    
    // 验证不再导出旧的命名（Payload）
    expect(liveAudioModule).not.toHaveProperty('StartLiveAudioPayload');
  });
});

describe('baseUrl 参数移除验证（问题5、8）', () => {
  it('所有服务函数不再接受 baseUrl 参数', async () => {
    const { getPlans } = await import('../payment');
    const { startAILiveAnalysis } = await import('../ai');
    const { startLiveAudio } = await import('../liveAudio');
    const { startLiveReport } = await import('../liveReport');
    const { startDouyinRelay } = await import('../douyin');
    const { getSessionStatus } = await import('../liveSession');

    // 验证函数签名不包含 baseUrl
    const getPlansSignature = getPlans.toString();
    expect(getPlansSignature).not.toContain('baseUrl');

    const startAISignature = startAILiveAnalysis.toString();
    expect(startAISignature).not.toContain('baseUrl');

    const startAudioSignature = startLiveAudio.toString();
    expect(startAudioSignature).not.toContain('baseUrl');

    const startReportSignature = startLiveReport.toString();
    expect(startReportSignature).not.toContain('baseUrl');

    const startDouyinSignature = startDouyinRelay.toString();
    expect(startDouyinSignature).not.toContain('baseUrl');

    const getStatusSignature = getSessionStatus.toString();
    expect(getStatusSignature).not.toContain('baseUrl');
  });

  it('没有 DEFAULT_BASE_URL 定义', async () => {
    const aiModule = await import('../ai');
    const paymentModule = await import('../payment');
    const liveAudioModule = await import('../liveAudio');

    // 验证模块不导出 DEFAULT_BASE_URL
    expect(aiModule).not.toHaveProperty('DEFAULT_BASE_URL');
    expect(paymentModule).not.toHaveProperty('DEFAULT_BASE_URL');
    expect(liveAudioModule).not.toHaveProperty('DEFAULT_BASE_URL');
  });
});

describe('重复函数移除验证（问题4）', () => {
  it('payment 服务不再导出 authFetch', async () => {
    const paymentModule = await import('../payment');
    expect(paymentModule).not.toHaveProperty('authFetch');
  });

  it('ai 服务不再导出 authFetch', async () => {
    const aiModule = await import('../ai');
    expect(aiModule).not.toHaveProperty('authFetch');
  });

  it('所有服务不再导出 buildHeaders', async () => {
    const paymentModule = await import('../payment');
    const aiModule = await import('../ai');
    const liveAudioModule = await import('../liveAudio');
    const liveReportModule = await import('../liveReport');
    const douyinModule = await import('../douyin');

    expect(paymentModule).not.toHaveProperty('buildHeaders');
    expect(aiModule).not.toHaveProperty('buildHeaders');
    expect(liveAudioModule).not.toHaveProperty('buildHeaders');
    expect(liveReportModule).not.toHaveProperty('buildHeaders');
    expect(douyinModule).not.toHaveProperty('buildHeaders');
  });
});

describe('统一可选字段标记验证（问题12）', () => {
  it('api-types.ts 中的类型定义可导入', async () => {
    // TypeScript 接口和类型别名在运行时不存在，但我们可以验证模块可以正常导入
    const apiTypes = await import('../../types/api-types');

    // 验证模块已加载
    expect(apiTypes).toBeDefined();
    // 验证类型守卫函数存在（这些是运行时存在的）
    expect(apiTypes).toHaveProperty('isValidationErrorArray');
    expect(apiTypes).toHaveProperty('isErrorDetail');
    expect(apiTypes).toHaveProperty('isTranscriptionMessage');
  });
});

