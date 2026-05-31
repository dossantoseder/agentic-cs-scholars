"""
Agent responsible for scraping researcher data from CNPq Lattes platform.
"""

import requests
import time
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from src.agents.BaseAgent import BaseAgent


class WebScraperAgent(BaseAgent):
    """
    Web scraping agent for CNPq Lattes data.
    
    Responsibilities:
        - Fetch HTML page from CNPq
        - Find data table with researcher records
        - Extract and parse researcher information
        - Return structured data for enrichment
    """
    
    def __init__(self):
        super().__init__("WebScraperAgent")
        self.rate_limit_seconds = 1
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes web scraping.
        
        Expected context:
            - url: Target URL for scraping
            - max_retries: Maximum retry attempts (optional, default 3)
        """
        url = context.get("url")
        max_retries = context.get("max_retries", 3)
        
        if not url:
            self.log_event("execution_failed", {"error": "No URL provided"})
            return {"status": "failed", "error": "No URL provided", "data": []}
        
        start_time = datetime.now()
        
        for attempt in range(max_retries):
            self.log_event("fetch_attempt", {"url": url, "attempt": attempt + 1})
            html = self._fetch_page(url)
            if html:
                break
            time.sleep(2 ** attempt)
        else:
            self.log_event("execution_failed", {"error": "All fetch attempts failed"})
            return {"status": "failed", "error": "All fetch attempts failed", "data": []}
        
        records = self._extract_researchers(html)
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        result = {
            "status": "success" if records else "partial",
            "data": records,
            "record_count": len(records),
            "duration_ms": duration_ms
        }
        
        self.log_event("execution_complete", {
            "record_count": len(records),
            "duration_ms": duration_ms
        })
        
        return result
    
    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetches HTML page with rate limiting."""
        time.sleep(self.rate_limit_seconds)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'iso-8859-1'
            return response.text
        except requests.RequestException as e:
            self.log_event("fetch_error", {"url": url, "error": str(e)})
            return None
    
    def _extract_researchers(self, html: str) -> List[Dict[str, Any]]:
        """
        Extracts researcher records from HTML table.
        Finds the table with most rows (data table).
        """
        soup = BeautifulSoup(html, "lxml")
        
        tables = soup.find_all("table")
        
        data_table = None
        max_rows = 0
        
        for table in tables:
            rows = table.find_all("tr")
            if len(rows) > max_rows and len(rows) > 10:
                max_rows = len(rows)
                data_table = table
                self.log_event("table_found", {"rows": len(rows)})
        
        if not data_table:
            self.log_event("parse_error", {"error": "Data table not found"})
            return []
        
        researchers = []
        rows = data_table.find_all("tr")
        
        for row in rows[1:]:
            cells = row.find_all("td")
            if len(cells) >= 5:
                researcher = self._parse_row(cells)
                if researcher.get("nome"):
                    researchers.append(researcher)
        
        self.log_event("parse_complete", {"extracted": len(researchers)})
        return researchers
    
    def _parse_row(self, cells: List) -> Dict[str, Any]:
        """Parses a single table row into researcher dictionary."""
        researcher = {}
        
        for i, cell in enumerate(cells):
            text = self._clean_text(cell.get_text())
            
            if i == 0:
                researcher["nome"] = text
            elif i == 1:
                researcher["instituicao"] = text
            elif i == 2:
                researcher["uf"] = self._extract_uf(text)
            elif i == 3:
                researcher["nivel_bolsa"] = text
            elif i == 4:
                researcher["area_atuacao"] = text
            elif i == 5:
                researcher["ano_doutorado"] = self._extract_year(text)
            elif i == 6:
                researcher["url_lattes"] = self._extract_lattes_url(text)
        
        return researcher
    
    def _clean_text(self, text: str) -> str:
        """Cleans and normalizes text."""
        return ' '.join(text.strip().split())
    
    def _extract_uf(self, text: str) -> str:
        """Extracts UF from text (e.g., 'SP', 'RJ')."""
        match = re.search(r'([A-Z]{2})$', text)
        if match:
            return match.group(1)
        
        uf_map = {
            "ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM",
            "BAHIA": "BA", "CEARA": "CE", "DISTRITO FEDERAL": "DF", "ESPIRITO SANTO": "ES",
            "GOIAS": "GO", "MARANHAO": "MA", "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS",
            "MINAS GERAIS": "MG", "PARA": "PA", "PARAIBA": "PB", "PARANA": "PR",
            "PERNAMBUCO": "PE", "PIAUI": "PI", "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN",
            "RIO GRANDE DO SUL": "RS", "RONDONIA": "RO", "RORAIMA": "RR", "SANTA CATARINA": "SC",
            "SAO PAULO": "SP", "SERGIPE": "SE", "TOCANTINS": "TO"
        }
        
        for name, uf in uf_map.items():
            if name in text.upper():
                return uf
        
        return text[:2] if len(text) >= 2 else text
    
    def _extract_year(self, text: str) -> int:
        """Extracts year from text."""
        match = re.search(r'\b(19|20)\d{2}\b', text)
        return int(match.group(0)) if match else 0
    
    def _extract_lattes_url(self, text: str) -> str:
        """Extracts Lattes URL from text."""
        match = re.search(r'(http://lattes\.cnpq\.br/\S+)', text)
        return match.group(1) if match else ""