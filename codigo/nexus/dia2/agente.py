"""O mesmo loop do dia 1, agora com componentes do LangChain."""
import sys
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field, ValidationError

from ferramentas import calcular, fazer_busca, ler_arquivo, listar_arquivos
from indexar import construir

SISTEMA = """Voce e o NEXUS, assistente de pesquisa sobre documentos locais.

Regras:
- Use 'buscar_documentos' antes de afirmar qualquer coisa sobre os documentos.
- Use 'calcular' para qualquer conta.
- Cite a fonte de cada numero no formato [fonte: arquivo].
- Se a busca nao trouxer nada util, diga isso em vez de inventar.
"""


class Relatorio(BaseModel):
    """Relatorio estruturado de uma pesquisa."""
    titulo: str
    resumo: str = Field(description="No maximo 3 frases")
    pontos: list[str] = Field(description="Achados, um por item")
    fontes: list[str] = Field(default_factory=list)
    confianca: Literal["alta", "media", "baixa"]


def montar(modelo: str = "qwen3:4b"):
    banco = construir()
    ferramentas = [calcular, listar_arquivos, ler_arquivo, fazer_busca(banco)]
    llm = ChatOllama(model=modelo, temperature=0)
    return llm, llm.bind_tools(ferramentas), {t.name: t for t in ferramentas}


def rodar(pergunta: str, max_passos: int = 8, verbose: bool = True) -> str:
    _, llm_tools, registro = montar()
    msgs = [SystemMessage(SISTEMA), HumanMessage(pergunta)]
    for passo in range(max_passos):
        ai = llm_tools.invoke(msgs)
        msgs.append(ai)
        if not ai.tool_calls:
            return ai.content
        for tc in ai.tool_calls:
            ferramenta = registro.get(tc["name"])
            if ferramenta is None:
                saida = f"ERRO: ferramenta '{tc['name']}' nao existe. Disponiveis: {list(registro)}"
            else:
                try:
                    saida = ferramenta.invoke(tc["args"])
                except Exception as e:
                    saida = f"ERRO ao executar: {type(e).__name__}: {e}"
            if verbose:
                print(f"[passo {passo}] {tc['name']}({tc['args']}) -> {str(saida)[:80]}")
            msgs.append(ToolMessage(content=str(saida), tool_call_id=tc["id"]))
    return "Limite de passos atingido."


def estruturado_com_retry(llm, schema, texto: str, tentativas: int = 3):
    """Saida estruturada com reinjecao do erro de validacao."""
    cadeia = llm.with_structured_output(schema)
    ultimo = None
    for i in range(tentativas):
        try:
            entrada = texto if i == 0 else (
                f"{texto}\n\nSua resposta anterior falhou: {ultimo}. "
                f"Responda estritamente no formato pedido.")
            return cadeia.invoke(entrada)
        except (ValidationError, ValueError) as e:
            ultimo = e
    raise RuntimeError(f"falhou apos {tentativas} tentativas: {ultimo}")


if __name__ == "__main__":
    pergunta = sys.argv[1] if len(sys.argv) > 1 else "Qual foi o faturamento de 2024?"
    print("\n" + rodar(pergunta))
