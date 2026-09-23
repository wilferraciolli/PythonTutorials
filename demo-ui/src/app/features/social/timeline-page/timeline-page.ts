import { httpResource } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { ApiClientService, CollectionEnvelope } from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../../core/api/api-error';
import { CurrentUserStore } from '../../../core/user/current-user.store';
import { PostCard } from '../post-card/post-card';
import { Post, TimelineType } from '../social.models';

const TABS: { type: TimelineType; label: string; link: string; empty: string }[] = [
  { type: 'ALL', label: 'All', link: 'timelineAll', empty: 'No posts in the last year yet.' },
  {
    type: 'FOLLOWING',
    label: 'Following',
    link: 'timelineFollowing',
    empty: 'Nothing here yet. Follow some groups and their posts will show up here.',
  },
  { type: 'POPULAR', label: 'Popular', link: 'timelinePopular', empty: 'No popular posts yet.' },
];

// Your feed: the three timeline links from the user profile, one per tab.
@Component({
  selector: 'app-timeline-page',
  imports: [MatButtonToggleModule, PostCard],
  templateUrl: './timeline-page.html',
  styleUrl: './timeline-page.scss',
})
export class TimelinePage {
  private readonly api = inject(ApiClientService);
  private readonly currentUser = inject(CurrentUserStore);

  protected readonly tabs = TABS;
  protected readonly type = signal<TimelineType>('ALL');
  protected readonly tab = computed(() => TABS.find((t) => t.type === this.type())!);

  private readonly feed = httpResource<CollectionEnvelope<'posts', Post>>(() =>
    this.api.resolve(this.currentUser.link(this.tab().link)),
  );

  protected readonly posts = computed(() => this.feed.value()?._data['posts'] ?? []);
  protected readonly isLoading = computed(() => this.feed.isLoading());
  protected readonly errorMessage = computed(() => {
    const error = this.feed.error();
    return error ? describeApiError(error, "Couldn't load your timeline.") : null;
  });
  protected readonly available = computed(
    () => !this.currentUser.profile() || !!this.currentUser.link('timelineAll'),
  );

  protected select(type: TimelineType): void {
    this.type.set(type);
  }

  protected reload(): void {
    this.feed.reload();
  }
}
