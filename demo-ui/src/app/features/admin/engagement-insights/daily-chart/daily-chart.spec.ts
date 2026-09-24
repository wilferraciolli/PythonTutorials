import { TestBed } from '@angular/core/testing';

import { DailyChart } from './daily-chart';

const DAYS = [
  { date: '2026-09-22', value: 2 },
  { date: '2026-09-23', value: 0 },
  { date: '2026-09-24', value: 7 },
];

describe('DailyChart', () => {
  function render() {
    const fixture = TestBed.createComponent(DailyChart);
    fixture.componentRef.setInput('title', 'Posts');
    fixture.componentRef.setInput('data', DAYS);
    // jsdom has no layout: give the chart a width the way the ResizeObserver would.
    (fixture.componentInstance as unknown as { width: { set(v: number): void } }).width.set(336);
    fixture.detectChanges();
    return fixture;
  }

  it('draws a bar per non-empty day and labels only the peak', () => {
    const el = render().nativeElement as HTMLElement;
    expect(el.querySelectorAll('.DailyChart-bar')).toHaveLength(2);
    expect(el.querySelector('.DailyChart-peak')?.textContent?.trim()).toBe('7');
    expect(el.querySelector('figcaption')?.textContent).toBe('Posts');
  });

  it('puts clean ticks on the axis', () => {
    const el = render().nativeElement as HTMLElement;
    const ticks = Array.from(el.querySelectorAll('.DailyChart-axis')).map((t) =>
      t.textContent?.trim(),
    );
    expect(ticks.slice(0, 3)).toEqual(['0', '5', '10']);
  });

  it('summarises the series for screen readers', () => {
    const plot = (render().nativeElement as HTMLElement).querySelector('.DailyChart-plot')!;
    expect(plot.getAttribute('aria-label')).toBe(
      'Posts per day, Sep 22 to Sep 24: 9 in total, most on Sep 24 (7). Use the arrow keys to read each day.',
    );
  });

  it('reads each day with the keyboard, starting from the latest', () => {
    const fixture = render();
    const plot = (fixture.nativeElement as HTMLElement).querySelector<HTMLElement>(
      '.DailyChart-plot',
    )!;
    const tooltip = () =>
      (fixture.nativeElement as HTMLElement)
        .querySelector('.DailyChart-tooltip')
        ?.textContent?.trim();

    plot.dispatchEvent(new FocusEvent('focus'));
    fixture.detectChanges();
    expect(tooltip()).toContain('7');
    expect(tooltip()).toContain('Sep 24');

    plot.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft' }));
    fixture.detectChanges();
    expect(tooltip()).toContain('Sep 23');

    plot.dispatchEvent(new KeyboardEvent('keydown', { key: 'Home' }));
    fixture.detectChanges();
    expect(tooltip()).toContain('Sep 22');

    plot.dispatchEvent(new FocusEvent('blur'));
    fixture.detectChanges();
    expect(tooltip()).toBeUndefined();
  });
});
