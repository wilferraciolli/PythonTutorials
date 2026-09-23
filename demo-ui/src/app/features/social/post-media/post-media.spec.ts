import { TestBed } from '@angular/core/testing';

import { PostMedia as Media, youtubeId } from '../social.models';
import { PostMedia } from './post-media';

let rerender = () => {};

function render(media: Media, deferVideo = false): HTMLElement {
  const fixture = TestBed.createComponent(PostMedia);
  fixture.componentRef.setInput('media', media);
  fixture.componentRef.setInput('deferVideo', deferVideo);
  fixture.detectChanges();
  rerender = () => fixture.detectChanges();
  return fixture.nativeElement as HTMLElement;
}

describe('PostMedia', () => {
  it('shows an Unsplash photo with the photographer credit', () => {
    const el = render({
      type: 'UNSPLASH',
      id: 'abc',
      url: 'https://images.unsplash.com/regular',
      title: 'a red bike',
      authorName: 'Ana Lens',
      authorUrl: 'https://unsplash.com/@ana?utm_source=wiltech&utm_medium=referral',
    });
    const img = el.querySelector('img')!;
    expect(img.getAttribute('src')).toBe('https://images.unsplash.com/regular');
    expect(img.getAttribute('alt')).toBe('a red bike');
    expect(el.textContent?.replace(/\s+/g, ' ')).toContain('Photo by Ana Lens on Unsplash');
    const [author, unsplash] = Array.from(el.querySelectorAll('figcaption a'));
    expect(author.getAttribute('href')).toBe(
      'https://unsplash.com/@ana?utm_source=wiltech&utm_medium=referral',
    );
    expect(unsplash.getAttribute('href')).toBe(
      'https://unsplash.com/?utm_source=wiltech&utm_medium=referral',
    );
  });

  it('embeds a YouTube video, or shows its thumbnail until played in a list', () => {
    const video: Media = {
      type: 'YOUTUBE',
      id: 'dQw4w9WgXcQ',
      url: null,
      authorName: null,
      authorUrl: null,
    };
    expect(render(video).querySelector('iframe')?.src).toContain(
      'youtube-nocookie.com/embed/dQw4w9WgXcQ',
    );

    const deferred = render(video, true);
    expect(deferred.querySelector('iframe')).toBeNull();
    expect(deferred.querySelector('img')?.getAttribute('src')).toContain(
      'i.ytimg.com/vi/dQw4w9WgXcQ',
    );
    (deferred.querySelector('button') as HTMLButtonElement).click();
    rerender();
    expect(deferred.querySelector('iframe')?.src).toContain('autoplay=1');
  });

  it('shows a GIF as a still frame and animates it only while hovered', () => {
    const el = render({
      type: 'GIPHY',
      id: 'gif42',
      url: 'https://media.giphy.com/media/gif42/giphy.webp',
      authorName: null,
      authorUrl: null,
    });
    const img = () => el.querySelector('img')!.getAttribute('src');
    const button = el.querySelector('button') as HTMLButtonElement;
    expect(img()).toBe('https://media.giphy.com/media/gif42/giphy_s.gif');
    expect(el.textContent).toContain('GIF');

    button.dispatchEvent(new Event('mouseenter'));
    rerender();
    expect(img()).toBe('https://media.giphy.com/media/gif42/giphy.webp');

    button.dispatchEvent(new Event('mouseleave'));
    rerender();
    expect(img()).toBe('https://media.giphy.com/media/gif42/giphy_s.gif');

    button.click(); // tap on touch screens
    rerender();
    expect(img()).toBe('https://media.giphy.com/media/gif42/giphy.webp');
  });

  it('never embeds an id that is not a YouTube id', () => {
    const el = render({
      type: 'YOUTUBE',
      id: '"><script>',
      url: null,
      authorName: null,
      authorUrl: null,
    });
    expect(el.querySelector('iframe')).toBeNull();
  });
});

describe('youtubeId', () => {
  it('reads the id from an id or the usual links', () => {
    for (const text of [
      'dQw4w9WgXcQ',
      'https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42',
      'youtube.com/watch?v=dQw4w9WgXcQ',
      'https://youtu.be/dQw4w9WgXcQ?si=x',
      'https://m.youtube.com/shorts/dQw4w9WgXcQ',
      'https://www.youtube.com/embed/dQw4w9WgXcQ',
    ]) {
      expect(youtubeId(text)).toBe('dQw4w9WgXcQ');
    }
    expect(youtubeId('https://vimeo.com/dQw4w9WgXcQ')).toBeNull();
    expect(youtubeId('short')).toBeNull();
  });
});
