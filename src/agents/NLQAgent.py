"""
Agent responsible for natural language querying on researcher dataset.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from openai import OpenAI

from src.agents.BaseAgent import BaseAgent
from src.utils.config import Config


class NLQAgent(BaseAgent):
    """
    Natural Language Query agent.
    
    Responsibilities:
        - Interpret user questions in natural language
        - Query dataset and generate responses
        - Use LLM for understanding and formatting
    """
    
    def __init__(self):
        super().__init__("NLQAgent")
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = "gpt-4o"
        self.dataset = None
        self.dataset_path = Config.DATA_DIR / "pesquisadores.json"
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes natural language query.
        
        Expected context:
            - question: User question in natural language
        """
        question = context.get("question")
        
        if not question:
            self.log_event("execution_failed", {"error": "No question provided"})
            return {"status": "failed", "error": "No question provided", "answer": ""}
        
        self._load_dataset()
        
        if not self.dataset:
            self.log_event("execution_failed", {"error": "Dataset not available"})
            return {"status": "failed", "error": "Dataset not available", "answer": ""}
        
        start_time = datetime.now()
        
        answer = self._generate_answer(question)
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        result = {
            "status": "success",
            "question": question,
            "answer": answer,
            "duration_ms": duration_ms
        }
        
        self.log_event("execution_complete", {
            "question": question[:50],
            "answer_length": len(answer),
            "duration_ms": duration_ms
        })
        
        return result
    
    def _load_dataset(self) -> None:
        """Loads researcher dataset from JSON file."""
        if not self.dataset_path.exists():
            self.log_event("dataset_not_found", {"path": str(self.dataset_path)})
            return
        
        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                self.dataset = json.load(f)
            self.log_event("dataset_loaded", {"records": len(self.dataset)})
        except Exception as e:
            self.log_event("dataset_load_error", {"error": str(e)})
    
    def _generate_answer(self, question: str) -> str:
        """Generates answer using LLM with dataset context."""
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(question)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.log_event("llm_error", {"error": str(e)})
            return f"Error generating answer: {str(e)}"
    
    def _build_system_prompt(self) -> str:
    """Builds system prompt with dataset summary."""
    dataset_summary = self._get_dataset_summary()
    
    return f"""
You are a data analyst assistant specialized in Brazilian CNPq researcher data.

DATASET SUMMARY:
- Total records: {dataset_summary['total']}
- Available fields: {', '.join(dataset_summary['fields'])}
- UF distribution: {dataset_summary['uf_distribution']}
- Scholarship level distribution: {dataset_summary['level_distribution']}

RULES:
1. Answer only based on the provided dataset
2. Be concise and objective
3. Use numbers and statistics when appropriate
4. If information is not available, say: "No data available for the requested query"
5. **ALWAYS RESPOND IN ENGLISH**

FORMAT:
- For counts: "There are X researchers..."
- For lists: Present up to 10 items, mention if there are more
- For trends: Highlight the most relevant observations
- For not found: "No researchers found matching the criteria: [criteria]"
"""
    
    def _build_user_prompt(self, question: str) -> str:
        """Builds user prompt with dataset preview."""
        dataset_preview = self._get_dataset_preview()
        
        return f"""
DATASET PREVIEW (first 20 records):
{dataset_preview}

USER QUESTION: {question}

Please answer based on the dataset above.
"""
    
    def _get_dataset_summary(self) -> Dict[str, Any]:
        """Generates summary statistics from dataset."""
        if not self.dataset:
            return {"total": 0, "fields": [], "uf_distribution": {}, "level_distribution": {}}
        
        uf_counts = {}
        level_counts = {}
        
        for researcher in self.dataset:
            uf = researcher.get("uf", "Unknown")
            level = researcher.get("nivel_bolsa", "Unknown")
            uf_counts[uf] = uf_counts.get(uf, 0) + 1
            level_counts[level] = level_counts.get(level, 0) + 1
        
        fields = list(self.dataset[0].keys()) if self.dataset else []
        
        return {
            "total": len(self.dataset),
            "fields": fields,
            "uf_distribution": uf_counts,
            "level_distribution": level_counts
        }
    
    def _get_dataset_preview(self) -> str:
        """Returns first 20 records as formatted JSON."""
        if not self.dataset:
            return "Dataset is empty"
        
        preview = self.dataset[:20]
        return json.dumps(preview, ensure_ascii=False, indent=2)