import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { ChatList } from '../chat-list/chat-list';
import { ChatsStore } from '../chats.store';

@Component({
  selector: 'app-workers-ai-shell',
  imports: [RouterOutlet, ChatList],
  providers: [ChatsStore],
  templateUrl: './workers-ai-shell.html',
  styleUrl: './workers-ai-shell.scss',
})
export class WorkersAiShell {}
