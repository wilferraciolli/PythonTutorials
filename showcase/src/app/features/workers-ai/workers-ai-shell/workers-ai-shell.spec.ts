import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { WorkersAiShell } from './workers-ai-shell';

describe('WorkersAiShell', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkersAiShell],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(WorkersAiShell);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
