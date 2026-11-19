import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ManifestEntry, Prediction } from '../../src/types/Book';

// ---------------------------------------------------------------------------
// Mock window.Audio so no real audio is created
// ---------------------------------------------------------------------------
const mockAudioPlay = vi.fn().mockResolvedValue(undefined);
const mockAudioPause = vi.fn();

class MockAudio {
  src: string;
  volume: number = 1;
  currentTime: number = 0;
  duration: number = 300;
  private listeners: Record<string, Array<() => void>> = {};

  constructor(src = '') {
    this.src = src;
  }

  play = mockAudioPlay;
  pause = mockAudioPause;

  addEventListener(event: string, cb: () => void) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(cb);
  }

  removeEventListener() {}
}

vi.stubGlobal('Audio', MockAudio);

// ---------------------------------------------------------------------------
// Also stub timers used by crossfade (setInterval / setTimeout inside the hook)
// We leave real timers so the component mounts cleanly; Audio mock prevents sound.
// ---------------------------------------------------------------------------

import MusicPlayer from '../../src/components/music_player';

const MANIFEST: ManifestEntry[] = [
  { filename: 'track1.mp3', id: 'track-1', category: 'happy' },
  { filename: 'track2.mp3', id: 'track-2', category: 'sad' },
  { filename: 'neutral1.mp3', id: 'neutral-1', category: 'neutral' },
];

function renderPlayer(prediction: Prediction | null = null) {
  return render(
    <MusicPlayer
      prediction={prediction}
      manifest={MANIFEST}
      musicBase="http://localhost:8000"
    />
  );
}

describe('MusicPlayer', () => {
  beforeEach(() => {
    mockAudioPlay.mockClear();
    mockAudioPause.mockClear();
  });

  it('renders "Mood: —" and "Play" button when prediction is null', () => {
    renderPlayer(null);

    expect(screen.getByText('Mood: —')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Play' })).toBeInTheDocument();
  });

  it('shows the emotion label from prediction before playing', () => {
    const prediction: Prediction = { label: 'happy', certainty: 0.9 };
    renderPlayer(prediction);

    // The hook sets emotion to the label when not yet playing
    expect(screen.getByText('Mood: happy')).toBeInTheDocument();
  });

  it('Play button toggles to Pause after clicking', async () => {
    const user = userEvent.setup();
    renderPlayer(null);

    const playBtn = screen.getByRole('button', { name: 'Play' });
    await user.click(playBtn);

    expect(screen.getByRole('button', { name: 'Pause' })).toBeInTheDocument();
  });

  it('Pause button toggles back to Play', async () => {
    const user = userEvent.setup();
    renderPlayer(null);

    await user.click(screen.getByRole('button', { name: 'Play' }));
    await user.click(screen.getByRole('button', { name: 'Pause' }));

    expect(screen.getByRole('button', { name: 'Play' })).toBeInTheDocument();
  });

  it('renders a volume slider with aria-label="Volume"', () => {
    renderPlayer(null);

    const slider = screen.getByRole('slider', { name: 'Volume' });
    expect(slider).toBeInTheDocument();
    expect(slider).toHaveAttribute('type', 'range');
  });

  it('renders a "Next" button', () => {
    renderPlayer(null);

    expect(screen.getByRole('button', { name: 'Next' })).toBeInTheDocument();
  });

  it('shows "No track for" message when emotion has no matching manifest entry', () => {
    // prediction.label is "unknown" which is not in MANIFEST
    const prediction: Prediction = { label: 'unknown', certainty: 0.95 };
    renderPlayer(prediction);

    // Emotion displayed but no track found
    expect(screen.getByText(/No track for/)).toBeInTheDocument();
  });
});
