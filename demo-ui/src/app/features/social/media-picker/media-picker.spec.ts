import { signal } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_ORIGIN, ILink } from '@wiliamferraciolli/ngx-api-client';

import { CurrentUserStore } from '../../../core/user/current-user.store';
import { environment } from '../../../../environments/environment';
import { MediaSelection } from '../social.models';
import { MediaPicker } from './media-picker';

const links: Record<string, ILink> = {
  searchUnsplash: { href: '/api/media/unsplash/search' },
};

function tabButton(el: HTMLElement, label: string): HTMLButtonElement {
  return Array.from(el.querySelectorAll('mat-button-toggle button')).find((b) =>
    b.textContent?.includes(label),
  ) as HTMLButtonElement;
}

describe('MediaPicker', () => {
  const profileLinks = signal<Record<string, ILink>>(links);

  beforeEach(async () => {
    profileLinks.set(links);
    await TestBed.configureTestingModule({
      imports: [MediaPicker],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_ORIGIN, useValue: 'http://api' },
        { provide: CurrentUserStore, useValue: { link: (name: string) => profileLinks()[name] } },
      ],
    }).compileComponents();
  });

  function setup() {
    const fixture = TestBed.createComponent(MediaPicker);
    const picked: MediaSelection[] = [];
    fixture.componentInstance.picked.subscribe((p) => picked.push(p));
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    const type = (text: string) => {
      const input = el.querySelector('input') as HTMLInputElement;
      input.value = text;
      input.dispatchEvent(new Event('input'));
      fixture.detectChanges();
    };
    const submit = () => {
      el.querySelector('form')!.dispatchEvent(new Event('submit'));
      fixture.detectChanges();
    };
    return { fixture, el, picked, type, submit };
  }

  it('searches Unsplash through the profile link on submit and picks a result', async () => {
    const { fixture, el, picked, type, submit } = setup();
    type('bike');
    TestBed.inject(HttpTestingController).expectNone(() => true); // not while typing
    submit();

    TestBed.inject(HttpTestingController)
      .expectOne('http://api/api/media/unsplash/search?q=bike')
      .flush({
        _data: {
          media: [
            {
              type: 'UNSPLASH',
              id: 'abc',
              title: 'red bike',
              previewUrl: 'https://img/small',
              url: 'https://img/regular',
              authorName: 'Ana',
              authorUrl: null,
            },
          ],
        },
      });
    await fixture.whenStable();
    fixture.detectChanges();

    (el.querySelector('.MediaPicker-result') as HTMLButtonElement).click();
    expect(picked[0].ref).toEqual({ type: 'UNSPLASH', id: 'abc' });
    expect(picked[0].label).toBe('Photo by Ana');
  });

  it('picks a YouTube video from a pasted link, without any API call', () => {
    const { el, picked, type, submit } = setup();
    tabButton(el, 'YouTube').click();
    type('https://youtu.be/dQw4w9WgXcQ');
    submit();

    expect(picked[0].ref).toEqual({ type: 'YOUTUBE', id: 'dQw4w9WgXcQ' });
    TestBed.inject(HttpTestingController).verify();
  });

  it('searches Giphy straight from the browser and sends only the GIF id', async () => {
    const { fixture, el, picked, type, submit } = setup();
    tabButton(el, 'GIF').click();
    fixture.detectChanges();
    type('dance');
    submit();

    const http = TestBed.inject(HttpTestingController);
    const req = http.expectOne((r) => r.url === 'https://api.giphy.com/v1/gifs/search');
    expect(req.request.params.get('q')).toBe('dance');
    expect(req.request.params.get('api_key')).toBe(environment.giphyApiKey);
    expect(req.request.params.get('rating')).toBe('pg-13');
    req.flush({
      data: [
        {
          id: 'gif42',
          title: 'Happy dance',
          images: { fixed_width: { url: 'https://media.giphy.com/fixed.gif' } },
        },
      ],
    });
    await fixture.whenStable();
    fixture.detectChanges();

    expect(el.textContent).toContain('Powered by GIPHY');
    (el.querySelector('.MediaPicker-result') as HTMLButtonElement).click();
    expect(picked[0]).toEqual({
      ref: { type: 'GIPHY', id: 'gif42' },
      previewUrl: 'https://media.giphy.com/fixed.gif',
      label: 'GIF',
    });
  });

  it('hides Unsplash when the profile has no search link for it', () => {
    profileLinks.set({});
    const { el } = setup();
    const text = el.textContent ?? '';
    expect(text).not.toContain('Unsplash');
    expect(text).toContain('GIF');
    expect(text).toContain('YouTube');
  });
});
