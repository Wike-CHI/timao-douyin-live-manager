import { describe, it, expect, vi, beforeEach } from 'vitest';

const fetchMock = vi.fn();
vi.stubGlobal('fetch', fetchMock);

const authHeaders = { Authorization: 'Bearer mock-token' };

vi.mock('../authService', () => ({
  default: {
    getAuthHeaders: vi.fn().mockResolvedValue(authHeaders),
  },
}));

const createResponse = (data: unknown) =>
  ({
    ok: true,
    json: async () => data,
  }) as Response;

describe('http helper utilities', () => {
  beforeEach(() => {
    fetchMock.mockReset();
    fetchMock.mockResolvedValue(createResponse({ success: true }));
  });

  it('buildJsonAuthHeaders 合并默认 JSON 头和鉴权头', async () => {
    const { buildJsonAuthHeaders } = await import('../http');

    const headers = await buildJsonAuthHeaders({ 'X-Test': '1' });

    expect(headers).toEqual({
      'Content-Type': 'application/json',
      Authorization: 'Bearer mock-token',
      'X-Test': '1',
    });
  });

  it('fetchJsonWithAuth 使用 buildServiceUrl 构造完整 URL 并附带 headers', async () => {
    const { fetchJsonWithAuth } = await import('../http');

    await fetchJsonWithAuth('main', '/api/demo', { method: 'POST', body: '{}' }, 'https://api.example');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('https://api.example/api/demo');
    expect(options?.headers).toEqual({
      'Content-Type': 'application/json',
      Authorization: 'Bearer mock-token',
    });
    expect(options?.method).toBe('POST');
    expect(options?.body).toBe('{}');
  });
});

