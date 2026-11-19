import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock the api module
vi.mock('../../src/api', () => ({
  api: vi.fn(),
}));

import { api } from '../../src/api';
import FileUpload from '../../src/components/file_upload';

const mockApi = vi.mocked(api);

function makeEpubFile(name = 'my-book.epub', sizeKb = 100): File {
  const content = new Uint8Array(sizeKb * 1024);
  return new File([content], name, { type: 'application/epub+zip' });
}

describe('FileUpload', () => {
  beforeEach(() => {
    mockApi.mockReset();
  });

  it('renders "Choose EPUB file" label and a disabled Upload button initially', () => {
    render(<FileUpload onUploaded={vi.fn()} />);

    expect(screen.getByText('Choose EPUB file')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Upload' })).toBeDisabled();
  });

  it('shows filename + size and enables Upload button after selecting a file', async () => {
    const user = userEvent.setup();
    render(<FileUpload onUploaded={vi.fn()} />);

    const input = screen.getByRole('button', { name: 'Upload' }).closest('div')!
      .querySelector('input[type="file"]') as HTMLInputElement;

    const file = makeEpubFile('my-book.epub', 50);
    await user.upload(input, file);

    expect(screen.getByText(/my-book\.epub/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Upload' })).toBeEnabled();
  });

  it('calls onUploaded with correct jobId and formatted filename on success', async () => {
    const user = userEvent.setup();
    const onUploaded = vi.fn();

    mockApi.mockResolvedValueOnce(
      new Response(JSON.stringify({ job_id: 'abc-123' }), { status: 200 })
    );

    render(<FileUpload onUploaded={onUploaded} />);

    const input = screen.getByRole('button', { name: 'Upload' }).closest('div')!
      .querySelector('input[type="file"]') as HTMLInputElement;

    await user.upload(input, makeEpubFile('lord-of-the-rings.epub'));
    await user.click(screen.getByRole('button', { name: 'Upload' }));

    await waitFor(() => {
      expect(onUploaded).toHaveBeenCalledWith({
        jobId: 'abc-123',
        filename: 'Lord Of The Rings',
        filepath: '',
        status: 'sent',
      });
    });
  });

  it('clears the file display after a successful upload', async () => {
    const user = userEvent.setup();

    mockApi.mockResolvedValueOnce(
      new Response(JSON.stringify({ job_id: 'xyz' }), { status: 200 })
    );

    render(<FileUpload onUploaded={vi.fn()} />);

    const input = screen.getByRole('button', { name: 'Upload' }).closest('div')!
      .querySelector('input[type="file"]') as HTMLInputElement;

    await user.upload(input, makeEpubFile('test-book.epub'));
    await user.click(screen.getByRole('button', { name: 'Upload' }));

    await waitFor(() => {
      // After upload, file display should be gone and button should be disabled again
      expect(screen.getByRole('button', { name: 'Upload' })).toBeDisabled();
    });
  });

  it('displays an error message when API returns a non-ok response', async () => {
    const user = userEvent.setup();

    mockApi.mockResolvedValueOnce(new Response('', { status: 500 }));

    render(<FileUpload onUploaded={vi.fn()} />);

    const input = screen.getByRole('button', { name: 'Upload' }).closest('div')!
      .querySelector('input[type="file"]') as HTMLInputElement;

    await user.upload(input, makeEpubFile());
    await user.click(screen.getByRole('button', { name: 'Upload' }));

    await waitFor(() => {
      expect(screen.getByText(/Error: 500/)).toBeInTheDocument();
    });
  });

  it('shows "Uploading..." text during the request', async () => {
    const user = userEvent.setup();

    // Never resolves to keep the loading state active
    let resolveUpload!: (v: Response) => void;
    const neverSettled = new Promise<Response>((res) => { resolveUpload = res; });
    mockApi.mockReturnValueOnce(neverSettled);

    render(<FileUpload onUploaded={vi.fn()} />);

    const input = screen.getByRole('button', { name: 'Upload' }).closest('div')!
      .querySelector('input[type="file"]') as HTMLInputElement;

    await user.upload(input, makeEpubFile());
    
    // Click Upload — this triggers the async upload which never resolves
    await user.click(screen.getByRole('button', { name: 'Upload' }));

    // After clicking, the button should immediately show "Uploading..." and be disabled
    expect(screen.getByRole('button', { name: 'Uploading...' })).toBeDisabled();

    // Cleanup: resolve the promise to avoid test leaks — wrap in act to suppress warnings
    await act(async () => {
      resolveUpload(new Response(JSON.stringify({ job_id: 'x' }), { status: 200 }));
      await new Promise((r) => setTimeout(r, 0));
    });
  });
});
