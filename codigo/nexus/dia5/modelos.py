"""Um modelo por papel. A escolha e engenharia de sistema, nao detalhe."""
import os

from langchain_ollama import ChatOllama

PEQUENO = os.getenv("MODELO_PEQUENO", "qwen3:1.7b")
MEDIO = os.getenv("MODELO_MEDIO", "qwen3:4b")
GRANDE = os.getenv("MODELO_GRANDE", "qwen3:8b")

# supervisor  -> roda a cada transicao; modelo pequeno economiza mais aqui
# pesquisador -> precisa seguir instrucao e ler trechos longos
# analista    -> so orquestra a ferramenta 'calcular'
# redator     -> roda uma vez; vale o modelo mais capaz, com temperatura maior
# critico     -> deve ser rigoroso e deterministico
MODELOS = {
    "supervisor": ChatOllama(model=PEQUENO, temperature=0),
    "pesquisador": ChatOllama(model=MEDIO, temperature=0),
    "analista": ChatOllama(model=PEQUENO, temperature=0),
    "redator": ChatOllama(model=GRANDE, temperature=0.3),
    "critico": ChatOllama(model=MEDIO, temperature=0),
}


def para(papel: str):
    return MODELOS.get(papel, MODELOS["pesquisador"])
