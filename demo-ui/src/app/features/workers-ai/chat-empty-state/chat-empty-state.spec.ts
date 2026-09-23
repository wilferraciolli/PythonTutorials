import { TestBed } from '@angular/core/testing';

import { ChatEmptyState } from './chat-empty-state';

describe('ChatEmptyState', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatEmptyState],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(ChatEmptyState);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
