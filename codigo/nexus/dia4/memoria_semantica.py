"""Memoria semantica: lembrar o que importa, nao tudo.

O checkpointer guarda TUDO daquele thread_id, em ordem. Isso e perfeito para
retomar uma conversa e pessimo como memoria de longo prazo: na trigesima
pergunta o historico nao cabe mais na janela, e 95% dele e irrelevante.

A memoria semantica resolve por busca em vez de acumulo - a mesma mecanica do
RAG do dia 2, aplicada a fatos em vez de documentos.
"""
import uuid

from langchain.tools import tool
from langchain_ollama import OllamaEmbeddings
from langgraph.store.memory import InMemoryStore

MODELO_EMB = "nomic-embed-text"
DIMENSOES = 768


def criar_memoria(modelo: str = MODELO_EMB, dims: int = DIMENSOES):
    """Store com indice de embeddings - sem o indice, so busca por chave."""
    emb = OllamaEmbeddings(model=modelo)
    return InMemoryStore(index={"embed": emb.embed_documents, "dims": dims})


def guardar(memoria, usuario: str, texto: str, chave: str | None = None) -> str:
    """Grava um fato duravel sobre o usuario."""
    chave = chave or str(uuid.uuid4())
    memoria.put(("usuario", usuario), chave, {"texto": texto})
    return chave


def lembrancas_de(memoria, usuario: str, pergunta: str, limite: int = 3) -> str:
    """Recupera por significado e devolve em bloco pronto para o prompt."""
    achados = memoria.search(("usuario", usuario), query=pergunta, limit=limite)
    if not achados:
        return ""
    return "\n".join(f"- {a.value['texto']}" for a in achados)


@tool
def lembrar(fato: str) -> str:
    """Guarda um fato duravel sobre o usuario para conversas futuras.

    Use quando o usuario expressar uma preferencia, corrigir voce, ou informar
    algo sobre o contexto dele que valha para as proximas vezes. Nao use para
    fatos da conversa atual - isso o historico ja guarda.

    Args:
        fato: uma frase declarativa, autocontida, na terceira pessoa
    """
    # Versao simples, para o laboratorio. Na versao com ToolRuntime o store
    # chega por injecao e o user_id vem do config - ver apostila secao 4.9.
    return f"Anotado: {fato}"


def demonstrar():
    """Prova que a busca e semantica: query e fato nao compartilham palavras."""
    memoria = criar_memoria()
    guardar(memoria, "ana", "Ana prefere relatorios curtos, no maximo uma pagina.")
    guardar(memoria, "ana", "Ana trabalha no setor de compras da cooperativa.")
    guardar(memoria, "ana", "Ana pediu para nunca usar jargao tecnico sem explicar.")

    for pergunta in ["como devo formatar a resposta?",
                     "qual a area dela na empresa?",
                     "posso escrever de forma tecnica?"]:
        print(f"\nPergunta: {pergunta}")
        print(lembrancas_de(memoria, "ana", pergunta, limite=1))


if __name__ == "__main__":
    demonstrar()
