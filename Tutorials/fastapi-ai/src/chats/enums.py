from enum import Enum


class ChatMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
