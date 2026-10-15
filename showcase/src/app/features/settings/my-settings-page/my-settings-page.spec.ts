import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { MySettingsPage } from './my-settings-page';

describe('MySettingsPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MySettingsPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(MySettingsPage);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
