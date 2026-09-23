import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

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
});
