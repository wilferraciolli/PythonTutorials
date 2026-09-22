import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { ProceduresManagementStore } from '../procedures-management.store';
import { ProcedureForm } from './procedure-form';

describe('ProcedureForm', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProcedureForm],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        ProceduresManagementStore,
      ],
    }).compileComponents();
  });

  it('creates in create mode (no id)', () => {
    const fixture = TestBed.createComponent(ProcedureForm);
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('creates in edit mode (id set)', () => {
    const fixture = TestBed.createComponent(ProcedureForm);
    fixture.componentRef.setInput('id', 'proc_1');
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
  });
});
