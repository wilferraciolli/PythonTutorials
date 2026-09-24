// The engagement analytics API (fastapi-ai: GET /api/admin/analytics/engagement,
// linked from the admin hub as `engagementAnalytics`).

export type Metric = 'groups' | 'posts' | 'comments' | 'likes';

export const METRICS: readonly Metric[] = ['groups', 'posts', 'comments', 'likes'];

export type MetricCounts = Record<Metric, number>;

export interface EngagementDay extends MetricCounts {
  /** YYYY-MM-DD, UTC. */
  date: string;
}

export interface Engagement {
  from: string;
  to: string;
  days: number;
  totals: MetricCounts;
  /** The same totals for the `days` before `from`, for comparison. */
  previousTotals: MetricCounts;
  daily: EngagementDay[];
}

/** One bar of a daily chart. */
export interface DayValue {
  date: string;
  value: number;
}

export type Trend = 'up' | 'down' | 'flat';

export interface Delta {
  trend: Trend;
  /** "+25%", "−40%", "Up from 0", "No change". */
  label: string;
}

/** How the current total compares with the previous period's. */
export function delta(current: number, previous: number): Delta {
  if (current === previous) return { trend: 'flat', label: 'No change' };
  if (previous === 0) return { trend: 'up', label: 'Up from 0' };
  const change = Math.round(((current - previous) / previous) * 100);
  if (change === 0) return { trend: current > previous ? 'up' : 'down', label: '<1%' };
  return change > 0
    ? { trend: 'up', label: `+${change}%` }
    : { trend: 'down', label: `−${Math.abs(change)}%` };
}

/** 1,284 / 12.9K / 1.2M. */
export function compact(value: number): string {
  return new Intl.NumberFormat('en', {
    notation: value >= 10_000 ? 'compact' : 'standard',
    maximumFractionDigits: 1,
  }).format(value);
}

/** A clean axis top at or above `max`: 1, 2, 5 or 10 times a power of ten (at least 1). */
export function niceMax(max: number): number {
  if (max <= 1) return 1;
  const power = 10 ** Math.floor(Math.log10(max));
  const step = [1, 2, 5, 10].find((m) => m * power >= max)!;
  return step * power;
}

/** "Sep 24" from "2026-09-24", read as a UTC date. */
export function shortDate(isoDate: string): string {
  return new Date(`${isoDate}T00:00:00Z`).toLocaleDateString('en', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  });
}
