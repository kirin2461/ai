"""Memory Manager - manages conversation history and context for AI Humanity."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Single message in conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """Conversation with message history."""
    id: str
    messages: List[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class MemoryManager:
    """Manages conversation memory and context."""
    
    def __init__(self, storage_dir: str = "data/memory", max_history: int = 100):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.max_history = max_history
        self._conversations: Dict[str, Conversation] = {}
        self._current_conversation_id: Optional[str] = None
        
    def create_conversation(self, conversation_id: str = None) -> str:
        """Create new conversation."""
        if conversation_id is None:
            conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self._conversations[conversation_id] = Conversation(id=conversation_id)
        self._current_conversation_id = conversation_id
        logger.info(f"Created conversation: {conversation_id}")
        return conversation_id
        
    def add_message(self, role: str, content: str, 
                    conversation_id: str = None, metadata: Dict = None) -> None:
        """Add message to conversation."""
        conv_id = conversation_id or self._current_conversation_id
        if conv_id is None:
            conv_id = self.create_conversation()
            
        if conv_id not in self._conversations:
            self._conversations[conv_id] = Conversation(id=conv_id)
            
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        self._conversations[conv_id].messages.append(message)
        self._conversations[conv_id].updated_at = datetime.now().isoformat()
        
        # Trim history if needed
        if len(self._conversations[conv_id].messages) > self.max_history:
            self._conversations[conv_id].messages = \
                self._conversations[conv_id].messages[-self.max_history:]
                
    def get_history(self, conversation_id: str = None, 
                    limit: int = None) -> List[Dict[str, str]]:
        """Get conversation history."""
        conv_id = conversation_id or self._current_conversation_id
        if conv_id is None or conv_id not in self._conversations:
            return []
            
        messages = self._conversations[conv_id].messages
        if limit:
            messages = messages[-limit:]
            
        return [{"role": m.role, "content": m.content} for m in messages]
        
    def get_context(self, conversation_id: str = None, 
                    max_tokens: int = 4000) -> str:
        """Get conversation context as string."""
        history = self.get_history(conversation_id)
        context_parts = []
        total_chars = 0
        
        for msg in reversed(history):
            msg_text = f"{msg['role']}: {msg['content']}"
            if total_chars + len(msg_text) > max_tokens * 4:  # rough char estimate
                break
            context_parts.insert(0, msg_text)
            total_chars += len(msg_text)
            
        return "\n".join(context_parts)
        
    def save_conversation(self, conversation_id: str = None) -> bool:
        """Save conversation to file."""
        conv_id = conversation_id or self._current_conversation_id
        if conv_id is None or conv_id not in self._conversations:
            return False
            
        filepath = self.storage_dir / f"{conv_id}.json"
        try:
            conv = self._conversations[conv_id]
            data = {
                "id": conv.id,
                "messages": [asdict(m) for m in conv.messages],
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "metadata": conv.metadata
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved conversation: {conv_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return False
            
    def load_conversation(self, conversation_id: str) -> bool:
        """Load conversation from file."""
        filepath = self.storage_dir / f"{conversation_id}.json"
        if not filepath.exists():
            return False
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            messages = [Message(**m) for m in data.get("messages", [])]
            self._conversations[conversation_id] = Conversation(
                id=conversation_id,
                messages=messages,
                created_at=data.get("created_at", ""),
                updated_at=data.get("updated_at", ""),
                metadata=data.get("metadata", {})
            )
            self._current_conversation_id = conversation_id
            logger.info(f"Loaded conversation: {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")
            return False
            
    def clear_conversation(self, conversation_id: str = None) -> None:
        """Clear conversation history."""
        conv_id = conversation_id or self._current_conversation_id
        if conv_id and conv_id in self._conversations:
            self._conversations[conv_id].messages.clear()
            logger.info(f"Cleared conversation: {conv_id}")
            
    def list_conversations(self) -> List[str]:
        """List all saved conversations."""
        return [f.stem for f in self.storage_dir.glob("*.json")]


# Global instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
