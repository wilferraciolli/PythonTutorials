import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { CurrentUserStore } from '../../core/user/current-user.store';
import { ProfileMenu } from './profile-menu';

describe('ProfileMenu', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProfileMenu],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(ProfileMenu);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('falls back to an account icon until /me has loaded', () => {
    const fixture = TestBed.createComponent(ProfileMenu);
    fixture.detectChanges();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('.ProfileMenu-avatar')).toBeNull();
    expect(el.querySelector('.ProfileMenu-avatar-icon')).toBeTruthy();
  });

  it("shows the first letter of the user's name as the avatar", () => {
    const store = TestBed.inject(CurrentUserStore);
    Object.defineProperty(store, 'me', { value: () => ({ name: '  Wil Ferraciolli' }) });

    const fixture = TestBed.createComponent(ProfileMenu);
    fixture.detectChanges();
    const avatar = (fixture.nativeElement as HTMLElement).querySelector('.ProfileMenu-avatar');
    expect(avatar?.textContent?.trim()).toBe('W');
  });
});
