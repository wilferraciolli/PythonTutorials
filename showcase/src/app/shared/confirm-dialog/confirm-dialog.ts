import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';

export interface ConfirmDialogData {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  // 'danger' renders the confirm button in the warn palette — for
  // destructive/hard-to-undo actions (delete). Defaults to primary.
  tone?: 'primary' | 'danger';
}

// Generic yes/no confirmation — replaces the browser's native confirm()
// wherever a destructive action needs a deliberate step (see
// todos-list.ts's delete action). Open with:
//   inject(MatDialog).open(ConfirmDialog, { data: { title, message } })
//     .afterClosed() // emits true (confirmed) or false/undefined (cancelled)
@Component({
  selector: 'app-confirm-dialog',
  imports: [MatButtonModule, MatDialogModule],
  templateUrl: './confirm-dialog.html',
  styleUrl: './confirm-dialog.scss',
})
export class ConfirmDialog {
  protected readonly data = inject<ConfirmDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<ConfirmDialog, boolean>);

  protected confirm(): void {
    this.dialogRef.close(true);
  }

  protected cancel(): void {
    this.dialogRef.close(false);
  }
}
