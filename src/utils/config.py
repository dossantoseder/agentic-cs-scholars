"""
Configuração centralizada do sistema.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()


class Config:
    """Configuração do sistema."""
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Database
    DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "./data/database.sqlite"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Rate Limiting
    RATE_LIMIT_PER_SECOND = int(os.getenv("RATE_LIMIT_PER_SECOND", "1"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Data directories
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    LOGS_DIR = BASE_DIR / "logs"
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Garante que todos os diretórios necessários existem."""
        for dir_path in [cls.DATA_DIR, cls.RAW_DATA_DIR, cls.PROCESSED_DATA_DIR, cls.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls) -> bool:
        """Valida se a configuração está completa."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY não configurada no arquivo .env")
        return True