import { formatDate } from '@angular/common';
import { LOCALE_ID, Pipe, PipeTransform, inject } from '@angular/core';

// "just now", "5 minutes ago", "yesterday", "3 days ago", then a short date
// ("Sep 12", or "Sep 12, 2025" in another year). Feeds read better with a
// relative time; put the full timestamp in a `title` for anyone who needs it.
// Pure, so it is computed once per value — a page left open doesn't tick over.
@Pipe({ name: 'relativeTime' })
export class RelativeTimePipe implements PipeTransform {
  private readonly locale = inject(LOCALE_ID);

  transform(value: string | Date | null | undefined, now: number = Date.now()): string {
    if (!value) return '';
    const then = new Date(value).getTime();
    if (Number.isNaN(then)) return '';

    const seconds = Math.round((then - now) / 1000);
    const abs = Math.abs(seconds);
    if (abs < 45) return 'just now';

    const format = new Intl.RelativeTimeFormat(this.locale, { numeric: 'auto' });
    if (abs < 3600) return format.format(Math.round(seconds / 60), 'minute');
    if (abs < 86400) return format.format(Math.round(seconds / 3600), 'hour');
    if (abs < 7 * 86400) return format.format(Math.round(seconds / 86400), 'day');

    const sameYear = new Date(then).getFullYear() === new Date(now).getFullYear();
    return formatDate(then, sameYear ? 'MMM d' : 'MMM d, y', this.locale);
  }
}
