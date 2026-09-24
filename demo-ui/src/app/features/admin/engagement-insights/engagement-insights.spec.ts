import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_ORIGIN } from '@wiliamferraciolli/ngx-api-client';

import { EngagementInsights } from './engagement-insights';

const LINK = { href: '/api/admin/analytics/engagement' };

function engagement(days: number) {
  const daily = Array.from({ length: days }, (_, i) => ({
    date: `2026-09-${String(i + 1).padStart(2, '0')}`,
    groups: 0,
    posts: i === days - 1 ? 4 : 0,
    comments: 1,
    likes: 2,
  }));
  return {
    _data: {
      engagement: {
        from: daily[0].date,
        to: daily.at(-1)!.date,
        days,
        totals: { groups: 0, posts: 4, comments: days, likes: days * 2 },
        previousTotals: { groups: 0, posts: 2, comments: days, likes: days * 4 },
        daily,
      },
    },
  };
}

describe('EngagementInsights', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [EngagementInsights],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_ORIGIN, useValue: '' },
      ],
    }).compileComponents();
  });

  async function load(days = 7) {
    const fixture = TestBed.createComponent(EngagementInsights);
    fixture.componentRef.setInput('link', LINK);
    fixture.detectChanges();
    TestBed.tick();
    TestBed.inject(HttpTestingController)
      .expectOne(`/api/admin/analytics/engagement?days=30`)
      .flush(engagement(days));
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture;
  }

  it('shows a total and its change for each metric', async () => {
    const el = (await load()).nativeElement as HTMLElement;
    const tiles = Array.from(el.querySelectorAll('.EngagementInsights-tile')).map((t) => ({
      label: t.querySelector('.EngagementInsights-tile-label')?.textContent?.trim(),
      value: t.querySelector('.EngagementInsights-tile-value')?.textContent?.trim(),
      delta: t.querySelector('.EngagementInsights-tile-delta')?.textContent,
    }));
    expect(tiles.map((t) => t.label)).toEqual(['Groups created', 'Posts', 'Comments', 'Likes']);
    expect(tiles.map((t) => t.value)).toEqual(['0', '4', '7', '14']);
    expect(tiles[0].delta).toContain('No change');
    expect(tiles[1].delta).toContain('+100%');
    expect(tiles[3].delta).toContain('−50%');
    expect(el.querySelectorAll('.is-down')).toHaveLength(1);
  });

  it('draws one chart per metric and lists every day in the table', async () => {
    const el = (await load(7)).nativeElement as HTMLElement;
    expect(el.querySelectorAll('app-daily-chart')).toHaveLength(4);
    expect(el.querySelectorAll('tbody tr')).toHaveLength(7);
  });

  it('asks for the chosen period and keeps the last numbers while it loads', async () => {
    const fixture = await load();
    const el = fixture.nativeElement as HTMLElement;
    const ninety = Array.from(el.querySelectorAll('mat-button-toggle button')).find((b) =>
      b.textContent?.includes('90'),
    ) as HTMLButtonElement;
    ninety.click();
    fixture.detectChanges();
    TestBed.tick();

    expect(el.querySelector('.EngagementInsights-body')?.classList).toContain('is-refreshing');
    expect(el.querySelectorAll('app-daily-chart')).toHaveLength(4);
    TestBed.inject(HttpTestingController).expectOne('/api/admin/analytics/engagement?days=90');
  });

  it('says so when the numbers can’t be loaded', async () => {
    const fixture = TestBed.createComponent(EngagementInsights);
    fixture.componentRef.setInput('link', LINK);
    fixture.detectChanges();
    TestBed.tick();
    TestBed.inject(HttpTestingController)
      .expectOne('/api/admin/analytics/engagement?days=30')
      .flush({ message: 'Boom' }, { status: 500, statusText: 'Server Error' });
    await fixture.whenStable();
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('[role="alert"]')).toBeTruthy();
  });
});
