import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { InsightsPage } from './insights-page';

describe('InsightsPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [InsightsPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(InsightsPage);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
