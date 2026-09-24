import { TestBed } from '@angular/core/testing';

import { RelativeTimePipe } from './relative-time.pipe';

describe('RelativeTimePipe', () => {
  const now = new Date('2026-09-24T12:00:00Z').getTime();
  const ago = (seconds: number) => new Date(now - seconds * 1000).toISOString();
  let pipe: RelativeTimePipe;

  beforeEach(() => {
    pipe = TestBed.runInInjectionContext(() => new RelativeTimePipe());
  });

  it('says "just now" for the last few seconds', () => {
    expect(pipe.transform(ago(10), now)).toBe('just now');
  });

  it('counts minutes, hours and days for the past week', () => {
    expect(pipe.transform(ago(5 * 60), now)).toBe('5 minutes ago');
    expect(pipe.transform(ago(3 * 3600), now)).toBe('3 hours ago');
    expect(pipe.transform(ago(26 * 3600), now)).toBe('yesterday');
    expect(pipe.transform(ago(3 * 86400), now)).toBe('3 days ago');
  });

  it('falls back to a short date after a week, with the year only when it differs', () => {
    expect(pipe.transform('2026-09-01T12:00:00Z', now)).toBe('Sep 1');
    expect(pipe.transform('2025-12-25T12:00:00Z', now)).toBe('Dec 25, 2025');
  });

  it('is blank for a missing or unreadable date', () => {
    expect(pipe.transform(null, now)).toBe('');
    expect(pipe.transform('not a date', now)).toBe('');
  });
});
