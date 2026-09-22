import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { BedBoardStore } from '../bed-board.store';
import { AssignProcedureDialog } from './assign-procedure-dialog';

describe('AssignProcedureDialog', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AssignProcedureDialog],
      providers: [provideHttpClient(), provideHttpClientTesting(), BedBoardStore],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(AssignProcedureDialog);
    fixture.componentRef.setInput('bedId', 'bed_1');
    fixture.componentRef.setInput('bedNumber', '3');
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
  });
});
