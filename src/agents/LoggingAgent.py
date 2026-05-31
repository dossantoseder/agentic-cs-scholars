"""
Agent responsible for logging all system operations.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler

from src.agents.BaseAgent import BaseAgent
from src.utils.config import Config


class LoggingAgent(BaseAgent):
    """
    Centralized logging agent.
    
    Responsibilities:
        - Register all agent operations
        - Log handoffs between agents
        - Track errors and execution times
        - Maintain audit trail for compliance
    """
    
    def __init__(self):
        super().__init__("LoggingAgent")
        self.logger = None
        self.log_file = Config.LOGS_DIR / "agentic_system.log"
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Configures structured logger with rotation."""
        Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("AgenticSystem")
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        if not self.logger.handlers:
            handler = RotatingFileHandler(
                self.log_file,
                maxBytes=10_485_760,
                backupCount=5,
                encoding="utf-8"
            )
            
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes logging operation.
        
        Expected context:
            - event_type: Type of event (agent_start, agent_end, handoff, error)
            - agent_name: Name of the source agent
            - event_data: Additional event data
            - correlation_id: Optional tracking ID
        """
        event_type = context.get("event_type", "unknown")
        agent_name = context.get("agent_name", self.name)
        event_data = context.get("event_data", {})
        correlation_id = context.get("correlation_id")
        
        log_entry = self._build_log_entry(event_type, agent_name, event_data, correlation_id)
        
        self._write_log(log_entry)
        
        self.log_event("log_written", {
            "event_type": event_type,
            "agent": agent_name,
            "correlation_id": correlation_id
        })
        
        return {"status": "success"}
    
    def _build_log_entry(self, event_type: str, agent_name: str, event_data: Dict, correlation_id: Optional[str]) -> Dict:
        """Builds structured log entry."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "agent": agent_name,
            "data": event_data
        }
        
        if correlation_id:
            entry["correlation_id"] = correlation_id
        
        return entry
    
    def _write_log(self, log_entry: Dict) -> None:
        """Writes log entry to file and console."""
        log_message = json.dumps(log_entry, ensure_ascii=False)
        
        if log_entry.get("event_type") in ["error", "execution_failed"]:
            self.logger.error(log_message)
        elif log_entry.get("event_type") in ["handoff", "execution_start"]:
            self.logger.info(log_message)
        else:
            self.logger.debug(log_message)
    
    def log_agent_start(self, agent_name: str, correlation_id: Optional[str] = None) -> None:
        """Logs agent execution start."""
        self.execute({
            "event_type": "agent_start",
            "agent_name": agent_name,
            "correlation_id": correlation_id,
            "event_data": {"status": "started"}
        })
    
    def log_agent_end(self, agent_name: str, duration_ms: float, correlation_id: Optional[str] = None) -> None:
        """Logs agent execution end."""
        self.execute({
            "event_type": "agent_end",
            "agent_name": agent_name,
            "correlation_id": correlation_id,
            "event_data": {"duration_ms": duration_ms}
        })
    
    def log_handoff(self, from_agent: str, to_agent: str, correlation_id: Optional[str] = None) -> None:
        """Logs handoff between agents."""
        self.execute({
            "event_type": "handoff",
            "agent_name": from_agent,
            "correlation_id": correlation_id,
            "event_data": {"from": from_agent, "to": to_agent}
        })
    
    def log_error(self, agent_name: str, error: str, correlation_id: Optional[str] = None) -> None:
        """Logs error occurrence."""
        self.execute({
            "event_type": "error",
            "agent_name": agent_name,
            "correlation_id": correlation_id,
            "event_data": {"error": error}
        })
    
    def get_logs(self, limit: int = 100, event_type: Optional[str] = None) -> list:
        """Retrieves recent logs for analysis."""
        if not self.log_file.exists():
            return []
        
        logs = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    if event_type is None or log_entry.get("event_type") == event_type:
                        logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
        
        return logs[-limit:]