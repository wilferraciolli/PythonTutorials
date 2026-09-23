import { DatePipe } from '@angular/common';
import { Component, input, output, signal, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink } from '@angular/router';

import { describeApiError } from '../../../core/api/api-error';
import { PostMedia } from '../post-media/post-media';
import { SocialActions } from '../social-actions';
import { Post } from '../social.models';

// One post in a list (timeline or group page): title, a preview of the body,
// counts, and a like toggle. Emits `changed` so the owning list reloads.
@Component({
  selector: 'app-post-card',
  imports: [DatePipe, RouterLink, MatButtonModule, MatCardModule, MatIconModule, PostMedia],
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
