import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { TestBed } from '@angular/core/testing';

import { ChatList } from './chat-list';
import { ChatsStore } from '../chats.store';

describe('ChatList', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatList],
      providers: [ChatsStore, provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();
  });

  it('creates', () => {
    const fixture = TestBed.createComponent(ChatList);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
