import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { ProfileEditPage } from './profile-edit-page';

describe('ProfileEditPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProfileEditPage],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(ProfileEditPage);
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
  });
});
