import { Component, inject, signal } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { ConfirmDialog } from '../../../../shared/confirm-dialog/confirm-dialog';
import { ProcedureType, ProceduresManagementStore } from '../procedures-management.store';

@Component({
  selector: 'app-procedures-list',
  imports: [RouterLink],
  templateUrl: './procedures-list.html',
  styleUrl: './procedures-list.scss',
})
export class ProceduresList {
  protected readonly store = inject(ProceduresManagementStore);
  private readonly dialog = inject(MatDialog);

  protected readonly actionError = signal<string | null>(null);
  protected readonly pendingId = signal<string | null>(null);

  protected async onDelete(procedure: ProcedureType): Promise<void> {
    const dialogRef = this.dialog.open(ConfirmDialog, {
      data: {
        title: 'Deactivate procedure type',
        message: `Deactivate "${procedure.name}"? Existing bed history is preserved and it can be reactivated later.`,
        confirmLabel: 'Deactivate',
        tone: 'danger',
      },
    });
    const confirmed = await firstValueFrom(dialogRef.afterClosed());
    if (!confirmed) {
      return;
    }

    this.actionError.set(null);
    this.pendingId.set(procedure.id);
    try {
      await this.store.deleteProcedure(procedure);
    } catch {
      this.actionError.set(`Couldn't deactivate "${procedure.name}" — check the API is reachable.`);
    } finally {
      this.pendingId.set(null);
    }
  }
}
