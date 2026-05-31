"""
Agent responsible for strategic planning and orchestration of all agents.
"""

import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.BaseAgent import BaseAgent
from src.agents.WebScraperAgent import WebScraperAgent
from src.agents.EnrichmentAgent import EnrichmentAgent
from src.agents.NLQAgent import NLQAgent
from src.agents.LoggingAgent import LoggingAgent


class OrchestratorAgent(BaseAgent):
    """
    Strategic planner and orchestrator.
    
    Responsibilities:
        - Decompose high-level goals into tasks
        - Identify required agents
        - Define execution order and dependencies
        - Monitor execution and replan on failure
        - Coordinate handoffs between agents
    """
    
    def __init__(self):
        super().__init__("OrchestratorAgent")
        self.agents = {}
        self.current_plan = None
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes planning and orchestration.
        
        Expected context:
            - goal: High-level objective
            - parameters: Additional parameters for execution
        """
        goal = context.get("goal")
        parameters = context.get("parameters", {})
        
        if not goal:
            self.log_event("execution_failed", {"error": "No goal provided"})
            return {"status": "failed", "error": "No goal provided"}
        
        self._initialize_agents()
        
        plan = self._create_plan(goal, parameters)
        self.current_plan = plan
        
        self.log_event("plan_created", {"goal": goal, "steps": len(plan)})
        
        execution_result = self._execute_plan(plan)
        
        return execution_result
    
    def _initialize_agents(self) -> None:
        """Initializes all available agents."""
        self.agents = {
            "web_scraper": WebScraperAgent(),
            "enrichment": EnrichmentAgent(),
            "nlq": None,
            "logging": LoggingAgent()
        }
    
    def _create_plan(self, goal: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Creates execution plan based on goal.
        
        Planning strategies:
            - "collect_data": Full pipeline (scrape → enrich)
            - "query_data": Only NLQ (needs existing data)
            - "export_data": Only file operations
        """
        plan = []
        
        if "collect" in goal.lower() or "scrape" in goal.lower():
            plan.append({
                "step_id": 1,
                "agent": "web_scraper",
                "action": "fetch",
                "parameters": {"url": parameters.get("url")},
                "dependencies": []
            })
            plan.append({
                "step_id": 2,
                "agent": "enrichment",
                "action": "enrich",
                "parameters": {"output_dir": parameters.get("output_dir", "./data")},
                "dependencies": [1]
            })
        
        if "query" in goal.lower() or "ask" in goal.lower():
            self._ensure_nlq_agent()
            plan.append({
                "step_id": 3,
                "agent": "nlq",
                "action": "query",
                "parameters": {"question": parameters.get("question")},
                "dependencies": [2] if plan else []
            })
        
        return plan
    
    def _ensure_nlq_agent(self) -> None:
        """Lazy initialization of NLQ agent."""
        if self.agents["nlq"] is None:
            from src.agents.nlq_agent import NLQAgent
            self.agents["nlq"] = NLQAgent()
    
    def _execute_plan(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Executes plan steps respecting dependencies."""
        results = {}
        step_results = {}
        
        for step in plan:
            step_id = step["step_id"]
            agent_name = step["agent"]
            action = step["action"]
            params = step["parameters"]
            dependencies = step["dependencies"]
            
            if not self._dependencies_satisfied(dependencies, step_results):
                self.log_event("step_skipped", {"step_id": step_id, "reason": "unsatisfied_dependencies"})
                continue
            
            agent = self.agents.get(agent_name)
            if not agent:
                self.log_event("step_failed", {"step_id": step_id, "error": f"Agent {agent_name} not found"})
                continue
            
            self.log_event("step_start", {"step_id": step_id, "agent": agent_name})
            
            try:
                result = self._execute_step(agent, action, params, step_results)
                step_results[step_id] = result
                results[agent_name] = result
                self.log_event("step_success", {"step_id": step_id})
            except Exception as e:
                self.log_event("step_failed", {"step_id": step_id, "error": str(e)})
                return self._handle_failure(plan, step_id, step_results)
        
        return {
            "status": "success",
            "results": results
        }
    
    def _execute_step(self, agent, action: str, params: Dict, previous_results: Dict) -> Any:
        """Executes a single plan step with context from previous steps."""
        context = {}
        
        if action == "fetch":
            context = {"url": params.get("url")}
        elif action == "enrich":
            web_result = previous_results.get(1, {})
            researchers = web_result.get("data", [])
            context = {"researchers": researchers, "output_dir": params.get("output_dir")}
        elif action == "query":
            context = {"question": params.get("question")}
        
        return agent.execute(context)
    
    def _dependencies_satisfied(self, dependencies: List[int], results: Dict) -> bool:
        """Checks if all dependencies are satisfied."""
        for dep_id in dependencies:
            if dep_id not in results:
                return False
            result = results[dep_id]
            if result.get("status") != "success":
                return False
        return True
    
    def _handle_failure(self, plan: List[Dict], failed_step_id: int, results: Dict) -> Dict[str, Any]:
        """Handles step failure with replanning capability."""
        self.log_event("replanning", {"failed_step_id": failed_step_id})
        
        remaining_steps = [s for s in plan if s["step_id"] > failed_step_id]
        
        if remaining_steps:
            self.log_event("replanning_skip", {"skipped_steps": [s["step_id"] for s in remaining_steps]})
        
        return {
            "status": "partial",
            "results": results,
            "failed_step": failed_step_id
        }