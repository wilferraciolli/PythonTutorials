import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { BedBoardShell } from './bed-board-shell';

describe('BedBoardShell', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BedBoardShell],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(BedBoardShell);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
