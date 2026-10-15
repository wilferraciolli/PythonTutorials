import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { SystemSettingsPage } from './system-settings-page';

describe('SystemSettingsPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SystemSettingsPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(SystemSettingsPage);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
