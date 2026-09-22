import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { BedBoardStore } from '../bed-board.store';
import { AdjustDurationDialog } from './adjust-duration-dialog';

describe('AdjustDurationDialog', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdjustDurationDialog],
      providers: [provideHttpClient(), provideHttpClientTesting(), BedBoardStore],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(AdjustDurationDialog);
    fixture.componentRef.setInput('bedId', 'bed_1');
    fixture.componentRef.setInput('bedNumber', '3');
    fixture.componentRef.setInput('currentDurationMinutes', 120);
    fixture.componentRef.setInput('occupiedMinutes', 45);
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
  });
});
