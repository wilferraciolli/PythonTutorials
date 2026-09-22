import { Component, inject, signal } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';

import { ConfirmDialog } from '../../../../shared/confirm-dialog/confirm-dialog';
import { Ward, WardsManagementStore } from '../wards-management.store';

@Component({
  selector: 'app-wards-list',
  imports: [RouterLink],
  templateUrl: './wards-list.html',
  styleUrl: './wards-list.scss',
})
export class WardsList {
  protected readonly store = inject(WardsManagementStore);
  private readonly dialog = inject(MatDialog);

  protected readonly actionError = signal<string | null>(null);
  protected readonly pendingId = signal<string | null>(null);

  protected async onDelete(ward: Ward): Promise<void> {
    if (ward.bed_count > 0) {
      const dialogRef = this.dialog.open(ConfirmDialog, {
        data: {
          title: "Can't delete this ward",
          message: `${ward.name} still has ${ward.bed_count} bed(s) assigned — reassign or remove them first.`,
          confirmLabel: 'Got it',
          cancelLabel: 'Close',
        },
      });
      await firstValueFrom(dialogRef.afterClosed());
      return;
    }

    const dialogRef = this.dialog.open(ConfirmDialog, {
      data: {
        title: 'Delete ward',
        message: `Delete ward "${ward.name}"? This cannot be undone.`,
        confirmLabel: 'Delete',
        tone: 'danger',
      },
    });
    const confirmed = await firstValueFrom(dialogRef.afterClosed());
    if (!confirmed) {
      return;
    }

    this.actionError.set(null);
    this.pendingId.set(ward.id);
    try {
      await this.store.deleteWard(ward);
    } catch {
      this.actionError.set(`Couldn't delete "${ward.name}" — check the API is reachable.`);
    } finally {
      this.pendingId.set(null);
    }
  }
}
