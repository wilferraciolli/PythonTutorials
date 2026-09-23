import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { ChatsStore } from '../chats.store';
import { ChatThread } from './chat-thread';

describe('ChatThread', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatThread],
      providers: [ChatsStore, provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(ChatThread);
    fixture.componentRef.setInput('chatId', 'test-chat-id');
    expect(fixture.componentInstance).toBeTruthy();
  });
});
