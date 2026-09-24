import { compact, delta, niceMax, shortDate } from './engagement.models';

describe('engagement helpers', () => {
  it('describes the change against the previous period', () => {
    expect(delta(12, 12)).toEqual({ trend: 'flat', label: 'No change' });
    expect(delta(5, 0)).toEqual({ trend: 'up', label: 'Up from 0' });
    expect(delta(15, 12)).toEqual({ trend: 'up', label: '+25%' });
    expect(delta(6, 10)).toEqual({ trend: 'down', label: '−40%' });
    expect(delta(1001, 1000)).toEqual({ trend: 'up', label: '<1%' });
  });

  it('rounds the axis top up to 1, 2 or 5 times a power of ten', () => {
    expect(niceMax(0)).toBe(1);
    expect(niceMax(3)).toBe(5);
    expect(niceMax(12)).toBe(20);
    expect(niceMax(50)).toBe(50);
    expect(niceMax(51)).toBe(100);
  });

  it('keeps small numbers exact and shortens big ones', () => {
    expect(compact(1284)).toBe('1,284');
    expect(compact(12900)).toBe('12.9K');
  });

  it('reads the API day as a UTC date', () => {
    expect(shortDate('2026-09-01')).toBe('Sep 1');
  });
});
