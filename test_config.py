import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.config import Config
from src.agents.BaseAgent import BaseAgent


class TestAgent(BaseAgent):
    """Agente de teste para verificar a classe base."""
    
    def execute(self, context: dict) -> dict:
        self.log_event("test_execution", context)
        return {"status": "success", "message": "Test agent working!"}


def main():
    print("=" * 50)
    print("Teste de Configuração do Ambiente")
    print("=" * 50)
    
    # Teste 1: Configuração
    print("\n1. Testando Configuração...")
    try:
        Config.ensure_directories()
        print(" Configuração carregada com sucesso")
    except Exception as e:
        print(f"Erro na configuração: {e}")
        return
    
    # Teste 2: API Key
    print("\n2. Verificando API Key...")
    api_key = Config.OPENAI_API_KEY
    if api_key and api_key != "sua-chave-api-aqui":
        print(f" API Key configurada: {api_key[:15]}...")
    else:
        print("API Key não configurada! Edite o arquivo .env")
    
    # Teste 3: Base Agent
    print("\n3. Testando Base Agent...")
    try:
        test_agent = TestAgent("Testador")
        result = test_agent.execute({"test": "hello"})
        print(f"Base Agent funcionando: {result}")
    except Exception as e:
        print(f"Erro no Base Agent: {e}")
        return
    
    # Teste 4: OpenAI
    print("\n4. Testando import do OpenAI...")
    try:
        import openai
        print(f"OpenAI importado com sucesso (versão {openai.__version__})")
    except Exception as e:
        print(f"Erro ao importar OpenAI: {e}")
        return
    
    print("\n" + "=" * 50)
    print("TODOS OS TESTES PASSARAM!")
    print("=" * 50)


if __name__ == "__main__":
    main()