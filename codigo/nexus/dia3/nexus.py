"""O NEXUS como grafo de estado: memoria, roteamento e aprovacao humana."""
import pathlib
import sys
from typing import Annotated, Literal, TypedDict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "dia2"))

from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from ferramentas import calcular, fazer_busca, ler_arquivo, listar_arquivos, salvar_relatorio
from indexar import construir

SISTEMA = """Voce e o NEXUS, assistente de pesquisa sobre documentos locais.

Regras:
- Use 'buscar_documentos' antes de afirmar qualquer coisa sobre os documentos.
- Use 'calcular' para qualquer conta.
- Cite a fonte de cada numero no formato [fonte: arquivo].
- So use 'salvar_relatorio' quando o usuario pedir explicitamente.
- Se a busca nao trouxer nada util, diga isso em vez de inventar.
"""

MAX_PASSOS = 10


class Estado(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    passos: int


def construir_grafo(modelo: str = "qwen3:4b"):
    banco = construir()
    ferramentas = [calcular, listar_arquivos, ler_arquivo,
                   fazer_busca(banco), salvar_relatorio]
    llm = ChatOllama(model=modelo, temperature=0).bind_tools(ferramentas)

    def no_agente(estado: Estado) -> dict:
        msgs = estado["messages"]
        if not any(getattr(m, "type", "") == "system" for m in msgs):
            msgs = [SystemMessage(SISTEMA), *msgs]
        return {"messages": [llm.invoke(msgs)], "passos": estado.get("passos", 0) + 1}

    def rotear(estado: Estado) -> Literal["ferramentas", "__end__"]:
        if estado.get("passos", 0) >= MAX_PASSOS:
            return END
        ultima = estado["messages"][-1]
        return "ferramentas" if getattr(ultima, "tool_calls", None) else END

    g = StateGraph(Estado)
    g.add_node("agente", no_agente)
    g.add_node("ferramentas", ToolNode(ferramentas))
    g.add_edge(START, "agente")
    g.add_conditional_edges("agente", rotear, ["ferramentas", END])
    g.add_edge("ferramentas", "agente")
    return g


def compilar(caminho_db: str = "nexus.db", aprovar_ferramentas: bool = True):
    memoria = SqliteSaver.from_conn_string(caminho_db).__enter__()
    return construir_grafo().compile(
        checkpointer=memoria,
        interrupt_before=["ferramentas"] if aprovar_ferramentas else [],
    )
