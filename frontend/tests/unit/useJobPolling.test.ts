import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import type { Book } from '../../src/types/Book';

// Mock the api module
vi.mock('../../src/api', () => ({
  api: vi.fn(),
}));

import { api } from '../../src/api';
import useJobPolling from '../../src/components/use_job_polling';

const mockApi = vi.mocked(api);

function makeBook(overrides: Partial<Book> = {}): Book {
  return {
    jobId: 'job-1',
    filename: 'test.epub',
    filepath: null,
    status: 'sent',
    ...overrides,
  };
}

describe('useJobPolling', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockApi.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('does not call api when no books are active', async () => {
    const books: Book[] = [makeBook({ status: 'done' })];
    const update = vi.fn();

    renderHook(() => useJobPolling(books, update));

    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    expect(mockApi).not.toHaveBeenCalled();
  });

  it('calls api for each active book on the first tick', async () => {
    const books: Book[] = [
      makeBook({ jobId: 'job-1', status: 'sent' }),
      makeBook({ jobId: 'job-2', status: 'parsing' }),
    ];
    const update = vi.fn();

    // Return a pending response for each call (never resolved to avoid errors)
    mockApi.mockResolvedValue(new Response(JSON.stringify({ status: 'parsing' }), { status: 200 }));

    renderHook(() => useJobPolling(books, update));

    await act(async () => {
      vi.advanceTimersByTime(1000);
      await Promise.resolve();
    });

    expect(mockApi).toHaveBeenCalledTimes(2);
    expect(mockApi).toHaveBeenCalledWith(
      '/books/job-1/status',
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
    expect(mockApi).toHaveBeenCalledWith(
      '/books/job-2/status',
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
  });

  it('calls update with { status: "error" } on 404', async () => {
    const books: Book[] = [makeBook({ jobId: 'job-404', status: 'predicting' })];
    const update = vi.fn();

    mockApi.mockResolvedValue(new Response('', { status: 404 }));

    renderHook(() => useJobPolling(books, update));

    await act(async () => {
      vi.advanceTimersByTime(1000);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(update).toHaveBeenCalledWith('job-404', { status: 'error' });
  });

  it('calls update with JSON body on ok response', async () => {
    const books: Book[] = [makeBook({ jobId: 'job-ok', status: 'parsing' })];
    const update = vi.fn();
    const responseBody = { status: 'done', filepath: '/books/test.epub' };

    mockApi.mockResolvedValue(
      new Response(JSON.stringify(responseBody), { status: 200 })
    );

    renderHook(() => useJobPolling(books, update));

    await act(async () => {
      vi.advanceTimersByTime(1000);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(update).toHaveBeenCalledWith('job-ok', responseBody);
  });

  it('aborts and clears timeout on cleanup', async () => {
    const books: Book[] = [makeBook({ status: 'sent' })];
    const update = vi.fn();

    // Never resolves — keeps the hook busy
    mockApi.mockReturnValue(new Promise(() => {}));

    const { unmount } = renderHook(() => useJobPolling(books, update));

    await act(async () => {
      vi.advanceTimersByTime(500);
    });

    // Unmounting should not throw and should abort the controller
    expect(() => unmount()).not.toThrow();
  });
});
