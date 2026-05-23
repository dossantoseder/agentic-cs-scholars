"""
Classe base para todos os agentes do sistema.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict


class BaseAgent(ABC):
    """Classe base abstrata para todos os agentes."""
    
    def __init__(self, name: str):
        self.agent_id = str(uuid.uuid4())[:8]
        self.name = name
        self.state: Dict[str, Any] = {}
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Método principal de execução do agente."""
        pass
    
    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Registra um evento no log."""
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [{self.name}] {event_type}: {data}")
    
    def update_state(self, key: str, value: Any) -> None:
        """Atualiza o estado interno do agente."""
        self.state[key] = value
        self.log_event("state_update", {"key": key})
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Recupera um valor do estado interno."""
        return self.state.get(key, default)