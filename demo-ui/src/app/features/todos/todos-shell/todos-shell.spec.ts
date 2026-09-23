import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { TodosShell } from './todos-shell';

describe('TodosShell', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TodosShell],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(TodosShell);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
