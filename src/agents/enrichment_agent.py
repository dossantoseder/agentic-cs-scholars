"""
Agent responsible for enriching researcher data with Google Scholar links.
"""

import time
import json
import csv
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import quote

from src.agents.base_agent import BaseAgent


class EnrichmentAgent(BaseAgent):
    """
    Data enrichment agent.
    
    Responsibilities:
        - Fetch Google Scholar link for each researcher
        - Validate enriched data
        - Save final data to CSV and JSON files
    """
    
    def __init__(self):
        super().__init__("EnrichmentAgent")
        self.data_dir = None
        
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes data enrichment.
        
        Expected context:
            - researchers: List of researcher dictionaries
            - output_dir: Directory to save output files (optional)
        """
        researchers = context.get("researchers", [])
        self.data_dir = context.get("output_dir", "./data")
        
        if not researchers:
            self.log_event("execution_failed", {"error": "No researchers to process"})
            return {"status": "failed", "error": "No researchers to process", "data": []}
        
        start_time = datetime.now()
        enriched_count = 0
        failed_count = 0
        
        self.log_event("execution_start", {"total_researchers": len(researchers)})
        
        for i, researcher in enumerate(researchers):
            self.log_event("processing", {
                "index": i + 1,
                "total": len(researchers),
                "name": researcher.get("nome", "Unknown")
            })
            
            google_scholar = self._fetch_google_scholar(researcher)
            researcher["google_scholar"] = google_scholar
            
            if google_scholar:
                enriched_count += 1
                self.log_event("enriched", {
                    "name": researcher.get("nome"),
                    "google_scholar": google_scholar[:50] + "..."
                })
            else:
                failed_count += 1
                self.log_event("not_found", {"name": researcher.get("nome")})
            
            time.sleep(0.5)
        
        self._save_to_files(researchers)
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        result = {
            "status": "success",
            "total_researchers": len(researchers),
            "enriched_count": enriched_count,
            "failed_count": failed_count,
            "duration_ms": duration_ms,
            "data": researchers
        }
        
        self.log_event("execution_complete", result)
        return result
    
    def _fetch_google_scholar(self, researcher: Dict[str, Any]) -> Optional[str]:
        """
        Fetches Google Scholar link for a researcher.
        
        Strategy:
            1. Search by name + institution
            2. If not found, search by name only
            3. Return None if not found
        """
        name = researcher.get("nome", "")
        institution = researcher.get("instituicao", "")
        
        if institution:
            query = f"{name} {institution.split()[0] if institution else ''}"
            result = self._search_google_scholar(query)
            if result:
                return result
        
        result = self._search_google_scholar(name)
        if result:
            return result
        
        clean_name = self._clean_name(name)
        result = self._search_google_scholar(clean_name)
        if result:
            return result
        
        return None
    
    def _search_google_scholar(self, query: str) -> Optional[str]:
        """
        Searches Google Scholar and returns profile URL.
        
        Note: Google Scholar resists scraping. For production, consider:
        - SerpAPI
        - Google Custom Search JSON API
        - scholarly library
        """
        if not query or len(query) < 3:
            return None
        
        encoded_query = quote(query)
        search_url = f"https://scholar.google.com.br/scholar?q={encoded_query}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "pt-BR,pt;q=0.9"
        }
        
        try:
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                self.log_event("search_failed", {"query": query, "status": response.status_code})
                return None
            
            if "user" in response.text:
                import re
                pattern = r'url\?q=(https://scholar\.google\.[^/]+/citations\?user=[^&"\']+)'
                match = re.search(pattern, response.text)
                if match:
                    return match.group(1)
            
            return None
            
        except requests.RequestException as e:
            self.log_event("search_error", {"query": query, "error": str(e)})
            return None
    
    def _clean_name(self, name: str) -> str:
        """Removes accents and special characters from name."""
        import unicodedata
        normalized = unicodedata.normalize('NFKD', name)
        cleaned = ''.join(c for c in normalized if not unicodedata.combining(c))
        return cleaned
    
    def _save_to_files(self, researchers: List[Dict[str, Any]]) -> None:
        """Saves enriched data to CSV and JSON files."""
        import os
        from pathlib import Path
        
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        
        json_path = os.path.join(self.data_dir, "pesquisadores.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(researchers, f, ensure_ascii=False, indent=2)
        self.log_event("file_saved", {"path": json_path, "format": "json"})
        
        if researchers:
            csv_path = os.path.join(self.data_dir, "pesquisadores.csv")
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=researchers[0].keys())
                writer.writeheader()
                writer.writerows(researchers)
            self.log_event("file_saved", {"path": csv_path, "format": "csv"})
    
    def _validate_researcher(self, researcher: Dict[str, Any]) -> bool:
        """Validates if researcher has all required fields."""
        required_fields = ["nome", "instituicao", "uf", "url_lattes"]
        for field in required_fields:
            if not researcher.get(field):
                self.log_event("validation_failed", {"field": field, "researcher": researcher.get("nome")})
                return False
        return True