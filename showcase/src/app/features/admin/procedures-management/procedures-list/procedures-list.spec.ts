import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { ProceduresManagementStore } from '../procedures-management.store';
import { ProceduresList } from './procedures-list';

describe('ProceduresList', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProceduresList],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        ProceduresManagementStore,
      ],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(ProceduresList);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
