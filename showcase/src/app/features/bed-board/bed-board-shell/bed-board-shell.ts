import { Component, inject, signal } from '@angular/core';
import { MatChipListboxChange, MatChipsModule } from '@angular/material/chips';

import { I18nStore } from '../../../core/i18n/i18n.store';
import { wardLabel } from '../../../core/i18n/labels';
import { AdjustDurationDialog } from '../adjust-duration-dialog/adjust-duration-dialog';
import { AssignProcedureDialog } from '../assign-procedure-dialog/assign-procedure-dialog';
import { BedCard } from '../bed-card/bed-card';
import { Bed, BedBoardStore, BedStatus } from '../bed-board.store';

type ActiveDialog = { kind: 'assign' | 'adjust'; bed: Bed } | null;

@Component({
  selector: 'app-bed-board-shell',
  imports: [BedCard, AssignProcedureDialog, AdjustDurationDialog, MatChipsModule],
  providers: [BedBoardStore],
  templateUrl: './bed-board-shell.html',
  styleUrl: './bed-board-shell.scss',
})
export class BedBoardShell {
  protected readonly store = inject(BedBoardStore);
  protected readonly i18n = inject(I18nStore);
  protected readonly wardLabel = wardLabel;

  protected readonly activeDialog = signal<ActiveDialog>(null);

  protected onStatusChange(bedId: string, status: BedStatus): void {
    this.store.updateStatus(bedId, status);
  }

  protected onWardFilterChange(event: MatChipListboxChange): void {
    this.store.wardFilters.set(new Set(event.value as string[]));
  }

  protected openAssignProcedure(bed: Bed): void {
    this.activeDialog.set({ kind: 'assign', bed });
  }

  protected openAdjustDuration(bed: Bed): void {
    this.activeDialog.set({ kind: 'adjust', bed });
  }

  protected closeDialog(): void {
    this.activeDialog.set(null);
  }
}
