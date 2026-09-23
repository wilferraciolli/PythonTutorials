import { HttpErrorResponse, HttpResourceRequest, httpResource } from '@angular/common/http';
import { Component, computed, inject, output, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { ApiClientService, CollectionEnvelope } from '@wiliamferraciolli/ngx-api-client';

import { describeApiError } from '../../../core/api/api-error';
import { CurrentUserStore } from '../../../core/user/current-user.store';
import { environment } from '../../../../environments/environment';
import { MediaSearchResult, MediaSelection, MediaType, youtubeId } from '../social.models';

const GIPHY_SEARCH = 'https://api.giphy.com/v1/gifs/search';
const GIPHY_LIMIT = 24;
const GIPHY_RATING = 'pg-13';

/** The bits of Giphy's search response the picker uses. */
interface GiphySearch {
  data: { id: string; title?: string; images?: Record<string, { url?: string } | undefined> }[];
}

interface Query {
  type: MediaType;
  q: string;
}

// Pick one piece of media for a post:
// - Unsplash: searched through our API (the profile's `searchUnsplash` link;
//   the server holds that key).
// - Giphy: searched straight from the browser with Giphy's client key
//   (environment.giphyApiKey). The server only gets the GIF id.
// - YouTube: a pasted link or video id, no search.
// Emits the pick; the parent decides when to save it.
@Component({
  selector: 'app-media-picker',
  imports: [
    MatButtonModule,
    MatButtonToggleModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
  ],
  templateUrl: './media-picker.html',
  styleUrl: './media-picker.scss',
})
export class MediaPicker {
  readonly picked = output<MediaSelection>();
  readonly cancelled = output<void>();

  private readonly api = inject(ApiClientService);
  private readonly currentUser = inject(CurrentUserStore);
  private readonly giphyKey = environment.giphyApiKey;

  /** Only the providers that are set up (no Unsplash link or Giphy key hides the tab). */
  protected readonly tabs = computed(() =>
    (['UNSPLASH', 'GIPHY', 'YOUTUBE'] as MediaType[]).filter((type) =>
      type === 'UNSPLASH'
        ? !!this.currentUser.link('searchUnsplash')
        : type === 'GIPHY'
          ? !!this.giphyKey
          : true,
    ),
  );
  protected readonly tab = signal<MediaType>('UNSPLASH');
  protected readonly activeTab = computed(() =>
    this.tabs().includes(this.tab()) ? this.tab() : this.tabs()[0],
  );

  protected readonly draft = signal('');
  // Searches run on submit, not on every keystroke (both providers rate-limit).
  private readonly query = signal<Query | null>(null);
  private readonly unsplashQuery = computed(() =>
    this.query()?.type === 'UNSPLASH' ? this.query()!.q : null,
  );
  private readonly giphyQuery = computed(() =>
    this.query()?.type === 'GIPHY' ? this.query()!.q : null,
  );

  private readonly unsplashResource = httpResource<CollectionEnvelope<'media', MediaSearchResult>>(
    () => {
      const q = this.unsplashQuery();
      const url = q && this.api.resolve(this.currentUser.link('searchUnsplash'));
      return url ? `${url}?q=${encodeURIComponent(q)}` : undefined;
    },
  );

  private readonly giphyResource = httpResource<GiphySearch>(
    (): HttpResourceRequest | undefined => {
      const q = this.giphyQuery();
      return q
        ? {
            url: GIPHY_SEARCH,
            params: { api_key: this.giphyKey, q, limit: GIPHY_LIMIT, rating: GIPHY_RATING },
          }
        : undefined;
    },
  );

  private readonly activeResource = computed(() =>
    this.activeTab() === 'GIPHY' ? this.giphyResource : this.unsplashResource,
  );

  protected readonly results = computed<MediaSearchResult[]>(() => {
    if (this.query()?.type !== this.activeTab()) return [];
    return this.activeTab() === 'GIPHY'
      ? (this.giphyResource.value()?.data ?? []).map(toGiphyResult).filter((r) => !!r.previewUrl)
      : (this.unsplashResource.value()?._data['media'] ?? []);
  });
  protected readonly searching = computed(() => this.activeResource().isLoading());
  protected readonly searchError = computed(() => {
    const error = this.activeResource().error();
    if (!error) return null;
    if (this.activeTab() === 'GIPHY' && error instanceof HttpErrorResponse) {
      if (error.status === 429) return "Giphy's search limit has been reached. Try again later.";
      if (error.status === 401 || error.status === 403) return 'Giphy rejected the API key.';
    }
    return describeApiError(error, "Couldn't search right now.");
  });
  protected readonly searched = computed(() => this.query()?.type === this.activeTab());

  protected readonly videoId = computed(() => youtubeId(this.draft()));

  protected selectTab(type: MediaType): void {
    this.tab.set(type);
    this.draft.set('');
  }

  protected search(): void {
    const q = this.draft().trim();
    if (q) this.query.set({ type: this.activeTab(), q });
  }

  protected pick(result: MediaSearchResult): void {
    this.picked.emit({
      ref: { type: result.type, id: result.id },
      previewUrl: result.previewUrl,
      label: result.type === 'UNSPLASH' ? `Photo by ${result.authorName ?? 'unknown'}` : 'GIF',
    });
  }

  protected pickVideo(): void {
    const id = this.videoId();
    if (!id) return;
    this.picked.emit({
      ref: { type: 'YOUTUBE', id },
      previewUrl: `https://i.ytimg.com/vi/${id}/mqdefault.jpg`,
      label: `YouTube video ${id}`,
    });
  }

  protected tabLabel(type: MediaType): string {
    return { UNSPLASH: 'Unsplash', GIPHY: 'GIF', YOUTUBE: 'YouTube' }[type];
  }
}

function toGiphyResult(gif: GiphySearch['data'][number]): MediaSearchResult {
  const image = (...names: string[]) =>
    names.map((name) => gif.images?.[name]?.url).find((url) => !!url) ?? '';
  return {
    type: 'GIPHY',
    id: gif.id,
    title: gif.title || null,
    previewUrl: image('fixed_width', 'fixed_height', 'downsized', 'original'),
    url: image('downsized_medium', 'original'),
    authorName: null,
    authorUrl: null,
  };
}
