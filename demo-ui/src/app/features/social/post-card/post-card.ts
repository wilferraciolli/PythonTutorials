import { Component, input, output, signal, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink } from '@angular/router';

import { describeApiError } from '../../../core/api/api-error';
import { PostByline } from '../post-byline/post-byline';
import { PostMedia } from '../post-media/post-media';
import { SocialActions } from '../social-actions';
import { Post } from '../social.models';

// One post in a list (timeline or group page), as a card: byline, title, a
// preview of the body, media, counts and a like toggle. The whole card opens
// the post. Emits `changed` so the owning list reloads.
@Component({
  selector: 'app-post-card',
  imports: [RouterLink, MatButtonModule, MatIconModule, PostByline, PostMedia],
  templateUrl: './post-card.html',
  styleUrl: './post-card.scss',
})
export class PostCard {
  readonly post = input.required<Post>();
  readonly showGroup = input(true);
  readonly changed = output<void>();

  private readonly actions = inject(SocialActions);
  protected readonly busy = signal(false);
  protected readonly error = signal<string | null>(null);

  protected async toggleLike(): Promise<void> {
    this.busy.set(true);
    this.error.set(null);
    try {
      await this.actions.togglePostLike(this.post());
      this.changed.emit();
    } catch (err) {
      this.error.set(describeApiError(err, "Couldn't update the like."));
    } finally {
      this.busy.set(false);
    }
  }

  protected canLike(): boolean {
    const links = this.post().links;
    return !!(links['like'] || links['unlike']);
  }
}
