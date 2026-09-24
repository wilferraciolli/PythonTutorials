import {
  Component,
  DestroyRef,
  ElementRef,
  afterNextRender,
  computed,
  inject,
  input,
  signal,
  viewChild,
} from '@angular/core';

import { DayValue, compact, niceMax, shortDate } from '../../engagement.models';

const HEIGHT = 176;
const MARGIN = { top: 20, right: 8, bottom: 24, left: 36 };
const MAX_BAR = 24;
const GAP = 2;
const RADIUS = 4;

interface Bar {
  index: number;
  date: string;
  value: number;
  x: number;
  width: number;
  top: number;
  path: string;
}

// One metric per day as columns: a single series, so no legend (the title
// names it). Thin bars with a 4px rounded top on a shared baseline, hairline
// grid, the peak labelled. Hover or arrow keys read any day in a tooltip; the
// numbers are also in the page's table view, so nothing depends on hovering.
@Component({
  selector: 'app-daily-chart',
  templateUrl: './daily-chart.html',
  styleUrl: './daily-chart.scss',
})
export class DailyChart {
  readonly title = input.required<string>();
  readonly data = input.required<DayValue[]>();

  private readonly plot = viewChild.required<ElementRef<HTMLElement>>('plot');
  protected readonly width = signal(0);
  /** The day the tooltip is on: hovered, or chosen with the arrow keys. */
  protected readonly active = signal<number | null>(null);

  protected readonly height = HEIGHT;
  protected readonly left = MARGIN.left;
  private readonly baseline = HEIGHT - MARGIN.bottom;

  protected readonly top = computed(() => niceMax(Math.max(0, ...this.data().map((d) => d.value))));

  private readonly slot = computed(() => {
    const plotWidth = Math.max(0, this.width() - MARGIN.left - MARGIN.right);
    return this.data().length ? plotWidth / this.data().length : 0;
  });

  protected readonly bars = computed<Bar[]>(() => {
    const slot = this.slot();
    const width = Math.max(1, Math.min(MAX_BAR, slot - GAP));
    const scale = (this.baseline - MARGIN.top) / this.top();
    return this.data().map((day, index) => {
      const height = day.value * scale;
      const x = MARGIN.left + index * slot + (slot - width) / 2;
      const top = this.baseline - height;
      return {
        index,
        date: day.date,
        value: day.value,
        x,
        width,
        top,
        path: column(x, top, width, height, this.baseline),
      };
    });
  });

  protected readonly ticks = computed(() => {
    const top = this.top();
    const values = top % 2 === 0 ? [0, top / 2, top] : [0, top];
    const scale = (this.baseline - MARGIN.top) / top;
    return values.map((value) => ({
      value,
      label: compact(value),
      y: this.baseline - value * scale,
    }));
  });

  protected readonly xLabels = computed(() => {
    const bars = this.bars();
    if (!bars.length) return [];
    const picks = [...new Set([0, Math.floor((bars.length - 1) / 2), bars.length - 1])];
    return picks.map((i, n) => ({
      x: bars[i].x + bars[i].width / 2,
      label: shortDate(bars[i].date),
      anchor: n === 0 ? 'start' : n === picks.length - 1 ? 'end' : 'middle',
    }));
  });

  /** The tallest day, labelled on the chart (the first one on a tie). */
  protected readonly peak = computed(() => {
    const bars = this.bars();
    const best = bars.reduce<Bar | null>((a, b) => (!a || b.value > a.value ? b : a), null);
    return best && best.value > 0 ? best : null;
  });

  protected readonly total = computed(() => this.data().reduce((sum, d) => sum + d.value, 0));

  protected readonly summary = computed(() => {
    const data = this.data();
    if (!data.length) return `${this.title()}: no data`;
    const peak = this.peak();
    const range = `${shortDate(data[0].date)} to ${shortDate(data.at(-1)!.date)}`;
    return `${this.title()} per day, ${range}: ${compact(this.total())} in total${
      peak ? `, most on ${shortDate(peak.date)} (${compact(peak.value)})` : ''
    }. Use the arrow keys to read each day.`;
  });

  protected readonly tooltip = computed(() => {
    const index = this.active();
    const bar = index === null ? undefined : this.bars()[index];
    if (!bar) return null;
    const half = 44;
    const center = bar.x + bar.width / 2;
    return {
      value: compact(bar.value),
      date: shortDate(bar.date),
      left: Math.min(Math.max(center, half), Math.max(half, this.width() - half)),
      top: Math.min(bar.top, this.baseline) - 8,
      bandX: MARGIN.left + index! * this.slot(),
    };
  });

  protected readonly slotWidth = this.slot;
  protected readonly bandTop = MARGIN.top - 8;
  protected readonly bandHeight = this.baseline - MARGIN.top + 8;

  constructor() {
    const destroyRef = inject(DestroyRef);
    // Layout is in real pixels (crisp text, true 4px corners), so track the width.
    afterNextRender(() => {
      const element = this.plot().nativeElement;
      this.width.set(element.clientWidth);
      if (typeof ResizeObserver === 'undefined') return; // no layout engine (tests, server)
      const observer = new ResizeObserver(([entry]) => this.width.set(entry.contentRect.width));
      observer.observe(element);
      destroyRef.onDestroy(() => observer.disconnect());
    });
  }

  protected hover(event: PointerEvent): void {
    const box = this.plot().nativeElement.getBoundingClientRect();
    const index = Math.floor((event.clientX - box.left - MARGIN.left) / this.slot());
    this.active.set(index >= 0 && index < this.data().length ? index : null);
  }

  protected key(event: KeyboardEvent): void {
    const last = this.data().length - 1;
    const current = this.active() ?? last;
    const next =
      event.key === 'ArrowLeft'
        ? Math.max(0, current - 1)
        : event.key === 'ArrowRight'
          ? Math.min(last, current + 1)
          : event.key === 'Home'
            ? 0
            : event.key === 'End'
              ? last
              : null;
    if (next === null) return;
    event.preventDefault();
    this.active.set(next);
  }

  protected focus(): void {
    if (this.active() === null) this.active.set(this.data().length - 1);
  }
}

/** A column with a rounded top (square at the baseline). */
function column(x: number, top: number, width: number, height: number, baseline: number): string {
  if (height <= 0) return '';
  const r = Math.min(RADIUS, width / 2, height);
  return (
    `M${x},${baseline} V${top + r} Q${x},${top} ${x + r},${top} ` +
    `H${x + width - r} Q${x + width},${top} ${x + width},${top + r} V${baseline} Z`
  );
}
