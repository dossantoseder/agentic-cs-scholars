"""
Data manager for handling persistence and updates of researcher data.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class DataManager:
    """Manages data persistence and manual updates."""
    
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path("./data")
        self.data_dir = data_dir
        self.json_path = data_dir / "pesquisadores.json"
        self.csv_path = data_dir / "pesquisadores.csv"
        self.ensure_directories()
    
    def ensure_directories(self) -> None:
        """Creates data directory if it doesn't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_data(self) -> List[Dict[str, Any]]:
        """Loads researcher data from JSON file."""
        if not self.json_path.exists():
            return []
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_data(self, data: List[Dict[str, Any]]) -> bool:
        """Saves researcher data to JSON and CSV files."""
        try:
            # Save JSON
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Save CSV - dynamically get all fieldnames from data
            if data:
                fieldnames = list(data[0].keys())
                with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                    writer.writeheader()
                    writer.writerows(data)
            
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def update_field(self, nome: str, field: str, value: str) -> bool:
        """
        Updates a specific field for a researcher.
        
        Args:
            nome: Name of the researcher
            field: Field to update (e.g., "sexo", "google_scholar")
            value: New value for the field
        
        Returns:
            True if update was successful, False otherwise
        """
        data = self.load_data()
        
        for researcher in data:
            if researcher.get("nome") == nome:
                researcher[field] = value
                self.save_data(data)
                return True
        
        return False
    
    def get_researcher(self, nome: str) -> Optional[Dict[str, Any]]:
        """Returns a researcher by name."""
        data = self.load_data()
        for researcher in data:
            if researcher.get("nome") == nome:
                return researcher
        return None
    
    def get_all_researchers(self) -> List[Dict[str, Any]]:
        """Returns all researchers."""
        return self.load_data()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Returns basic statistics about the dataset."""
        data = self.load_data()
        
        if not data:
            return {
                "total": 0,
                "unique_institutions": 0,
                "unique_uf": 0,
                "gender_distribution": {},
                "level_distribution": {}
            }
        
        institutions = set()
        ufs = set()
        gender_count = {}
        level_count = {}
        
        for researcher in data:
            if researcher.get("instituicao"):
                institutions.add(researcher["instituicao"])
            if researcher.get("uf"):
                ufs.add(researcher["uf"])
            
            gender = researcher.get("sexo", "Nao informado")
            gender_count[gender] = gender_count.get(gender, 0) + 1
            
            level = researcher.get("nivel_bolsa", "")
            if level:
                level_count[level] = level_count.get(level, 0) + 1
        
        return {
            "total": len(data),
            "unique_institutions": len(institutions),
            "unique_uf": len(ufs),
            "gender_distribution": gender_count,
            "level_distribution": level_count
        }