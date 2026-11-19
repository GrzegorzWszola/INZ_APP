import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Set env before importing module
vi.stubEnv('VITE_API_URL', 'http://localhost:8000');

// Dynamically import after env stub so import.meta.env is set
const { api, initSession } = await import('../../src/api');

describe('api()', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('calls fetch with the correct full URL', async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(new Response('{}', { status: 200 }));

    await api('/test');

    expect(mockFetch).toHaveBeenCalledOnce();
    const [url] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/test');
  });

  it('always passes credentials: include', async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(new Response('{}', { status: 200 }));

    await api('/test');

    const [, opts] = mockFetch.mock.calls[0];
    expect(opts).toMatchObject({ credentials: 'include' });
  });

  it('merges extra options', async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(new Response('{}', { status: 200 }));

    await api('/books/upload', { method: 'POST' });

    const [, opts] = mockFetch.mock.calls[0];
    expect(opts).toMatchObject({ method: 'POST', credentials: 'include' });
  });
});

describe('initSession()', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('POSTs to /session/init', async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(new Response('{}', { status: 200 }));

    await initSession();

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toBe('http://localhost:8000/session/init');
    expect(opts).toMatchObject({ method: 'POST' });
  });

  it('throws when response is not ok', async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce(new Response('', { status: 500 }));

    await expect(initSession()).rejects.toThrow('Session init failed: 500');
  });
});
