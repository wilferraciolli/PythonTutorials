import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { TestBed } from '@angular/core/testing';

import { ConfirmDialog, ConfirmDialogData } from './confirm-dialog';

describe('ConfirmDialog', () => {
  let closedWith: unknown[];

  beforeEach(async () => {
    closedWith = [];
    const data: ConfirmDialogData = { title: 'Grant admin access', message: 'Are you sure?' };

    await TestBed.configureTestingModule({
      imports: [ConfirmDialog],
      providers: [
        { provide: MAT_DIALOG_DATA, useValue: data },
        { provide: MatDialogRef, useValue: { close: (value?: unknown) => closedWith.push(value) } },
      ],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(ConfirmDialog);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('closes with true on confirm', () => {
    const fixture = TestBed.createComponent(ConfirmDialog);
    fixture.componentInstance['confirm']();
    expect(closedWith).toEqual([true]);
  });

  it('closes with false on cancel', () => {
    const fixture = TestBed.createComponent(ConfirmDialog);
    fixture.componentInstance['cancel']();
    expect(closedWith).toEqual([false]);
  });
});
