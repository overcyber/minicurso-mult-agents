"""Diagnostico de ambiente para o curso. Roda em ate 30 segundos."""
import importlib
import sys

OK, FALHA = "[ OK ]", "[FALHA]"


def checar(descricao, funcao):
    try:
        detalhe = funcao()
        print(f"{OK} {descricao}" + (f" -> {detalhe}" if detalhe else ""))
        return True
    except Exception as e:
        print(f"{FALHA} {descricao} -> {type(e).__name__}: {e}")
        return False


def python_versao():
    if sys.version_info < (3, 11):
        raise RuntimeError(f"Python {sys.version_info.major}.{sys.version_info.minor}, precisa 3.11+")
    return f"Python {sys.version_info.major}.{sys.version_info.minor}"


def pacotes():
    faltando = []
    for nome in ["langchain", "langgraph", "langchain_ollama", "openai",
                 "chromadb", "pydantic", "rich"]:
        try:
            importlib.import_module(nome)
        except ImportError:
            faltando.append(nome)
    if faltando:
        raise RuntimeError(f"faltando: {', '.join(faltando)}")
    return "todos instalados"


def ollama_servindo():
    import requests
    r = requests.get("http://localhost:11434/api/tags", timeout=5)
    r.raise_for_status()
    modelos = [m["name"] for m in r.json().get("models", [])]
    if not modelos:
        raise RuntimeError("nenhum modelo baixado; rode 'ollama pull qwen3:4b'")
    return f"{len(modelos)} modelo(s): {', '.join(modelos[:4])}"


def modelo_responde():
    from langchain_ollama import ChatOllama
    r = ChatOllama(model="qwen3:4b", temperature=0).invoke("Responda apenas: ok")
    return r.content.strip()[:40]


def tool_calling():
    from langchain_ollama import ChatOllama
    from langchain.tools import tool

    @tool
    def somar(a: int, b: int) -> int:
        """Soma dois numeros inteiros."""
        return a + b

    r = ChatOllama(model="qwen3:4b", temperature=0).bind_tools([somar]).invoke(
        "Use a ferramenta para somar 2 e 3.")
    if not r.tool_calls:
        raise RuntimeError("o modelo nao emitiu tool_call; troque de modelo")
    return str(r.tool_calls[0]["args"])


def embeddings():
    from langchain_ollama import OllamaEmbeddings
    v = OllamaEmbeddings(model="nomic-embed-text").embed_query("teste")
    return f"dimensao {len(v)}"


if __name__ == "__main__":
    resultados = [
        checar("Versao do Python", python_versao),
        checar("Pacotes instalados", pacotes),
        checar("Ollama servindo", ollama_servindo),
        checar("Modelo responde", modelo_responde),
        checar("Tool calling funciona", tool_calling),
        checar("Embeddings funcionam", embeddings),
    ]
    print()
    if all(resultados):
        print("Ambiente pronto para o curso.")
    else:
        print("Corrija os itens marcados como FALHA antes do primeiro dia.")
        sys.exit(1)
