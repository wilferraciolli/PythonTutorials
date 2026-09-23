import { Component, computed, inject, input, signal } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

import { PostMedia as Media, YOUTUBE_ID } from '../social.models';

// Shows a post's media: an Unsplash photo (with the photographer credit
// Unsplash asks for), a Giphy GIF, or a YouTube video. With `deferVideo`
// (lists) a video starts as its thumbnail and only loads the player on click,
// so a timeline doesn't load dozens of iframes.
@Component({
  selector: 'app-post-media',
  imports: [MatIconModule],
  templateUrl: './post-media.html',
  styleUrl: './post-media.scss',
})
export class PostMedia {
  readonly media = input.required<Media>();
  readonly deferVideo = input(false);
  /** Fill the width at 16:9, cropping to fit — the shape a feed card wants. */
  readonly fill = input(false);

  private readonly sanitizer = inject(DomSanitizer);
  protected readonly playing = signal(false);

  // Only ever built from an id that passed the 11-character check, so it's
  // safe to hand the iframe (Angular requires the explicit trust call).
  protected readonly youtubeId = computed(() => {
    const media = this.media();
    return media.type === 'YOUTUBE' && YOUTUBE_ID.test(media.id) ? media.id : null;
  });
  protected readonly embedUrl = computed<SafeResourceUrl | null>(() => {
    const id = this.youtubeId();
    return id
      ? this.sanitizer.bypassSecurityTrustResourceUrl(
          `https://www.youtube-nocookie.com/embed/${id}${this.deferVideo() ? '?autoplay=1' : ''}`,
        )
      : null;
  });
  protected readonly thumbnailUrl = computed(() => {
    const id = this.youtubeId();
    return id ? `https://i.ytimg.com/vi/${id}/hqdefault.jpg` : null;
  });
  protected readonly showPlayer = computed(() => !this.deferVideo() || this.playing());

  // GIFs show Giphy's full-size still frame and only animate while hovered,
  // focused or tapped (quieter feeds, less data, kinder to motion-sensitive users).
  protected readonly animating = signal(false);
  protected readonly gifStillUrl = computed(() => {
    const media = this.media();
    return media.type === 'GIPHY' ? `https://media.giphy.com/media/${media.id}/giphy_s.gif` : null;
  });

  protected readonly unsplashUrl = 'https://unsplash.com/?utm_source=wiltech&utm_medium=referral';
}
