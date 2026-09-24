import { DatePipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { RelativeTimePipe } from '../../../shared/relative-time.pipe';

// Who posted, where and when, as the header of a post: an avatar with the
// author's initial, their name, then the group (a link, when shown) and a
// relative time with the full timestamp on hover.
@Component({
  selector: 'app-post-byline',
  imports: [DatePipe, RouterLink, RelativeTimePipe],
  templateUrl: './post-byline.html',
  styleUrl: './post-byline.scss',
})
export class PostByline {
  readonly author = input<string | null>(null);
  readonly date = input.required<string>();
  /** Both set: the group is shown and links to its page. */
  readonly groupId = input<string | null>(null);
  readonly groupName = input<string | null>(null);
  /** When the post was last edited, if it was. */
  readonly editedDate = input<string | null>(null);

  protected readonly name = computed(() => this.author()?.trim() || 'Unknown');
  protected readonly initial = computed(() => this.author()?.trim().charAt(0) || '?');
}
