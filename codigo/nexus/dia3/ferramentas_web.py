"""Ferramentas que saem da maquina: busca na web e leitura de pagina.

O modelo continua local. A informacao, nao. Buscar na web significa que a
consulta do usuario sai da maquina - nao os pesos, nao o historico, mas a
pergunta. Para alguns projetos isso e irrelevante; para um agente que processa
dado de paciente ou contrato, e inaceitavel. A decisao e do projeto.
"""
import time

import requests
from bs4 import BeautifulSoup
from langchain.tools import tool
from pydantic import BaseModel, Field

CABECALHO = {"User-Agent": "NEXUS-curso/1.0 (uso educacional)"}
TIMEOUT = 15
LIXO_HTML = ["script", "style", "nav", "header", "footer", "aside", "form"]


class EntradaBusca(BaseModel):
    consulta: str = Field(description="termos de busca em linguagem natural")
    k: int = Field(default=5, ge=1, le=10,
                   description="quantos resultados retornar")


class EntradaPagina(BaseModel):
    url: str = Field(description="endereco completo, com http:// ou https://")
    max_chars: int = Field(default=4000, ge=200, le=20000,
                           description="limite de caracteres devolvidos")


def _limpar_html(html: str, max_chars: int) -> str:
    """Tira menu, rodape e script, e devolve texto util truncado."""
    sopa = BeautifulSoup(html, "html.parser")
    for lixo in sopa(LIXO_HTML):
        lixo.decompose()
    texto = sopa.get_text(separator="\n")
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    limpo = "\n".join(linhas)
    if len(limpo) > max_chars:
        return limpo[:max_chars] + "\n...[truncado]"
    return limpo


@tool(args_schema=EntradaBusca)
def buscar_web(consulta: str, k: int = 5) -> str:
    """Busca na web e devolve titulo, trecho e URL dos resultados.

    Use quando a resposta nao estiver nos documentos locais, ou quando a
    pergunta envolver algo posterior ao corte de conhecimento do modelo.
    Sempre prefira buscar_documentos primeiro.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        return ("ERRO: pacote 'ddgs' nao instalado. "
                "Rode: pip install ddgs")

    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.text(consulta, max_results=k))
    except Exception as e:
        return f"ERRO na busca: {type(e).__name__}: {e}"

    if not resultados:
        return "Nenhum resultado encontrado."

    blocos = []
    for r in resultados:
        titulo = r.get("title", "(sem titulo)")
        corpo = r.get("body", "")
        href = r.get("href", "")
        blocos.append(f"[{titulo}]\n{corpo}\nFonte: {href}")
    return "\n\n---\n\n".join(blocos)


@tool(args_schema=EntradaPagina)
def ler_pagina(url: str, max_chars: int = 4000) -> str:
    """Baixa uma pagina web e devolve o texto limpo, sem HTML.

    Use depois de buscar_web, quando o trecho retornado nao for suficiente e
    voce precisar do conteudo completo daquela URL.
    """
    if not url.startswith(("http://", "https://")):
        return "ERRO: url deve comecar com http:// ou https://"

    try:
        resp = requests.get(url, headers=CABECALHO, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.Timeout:
        return f"ERRO: a pagina nao respondeu em {TIMEOUT}s."
    except Exception as e:
        return f"ERRO ao baixar: {type(e).__name__}: {e}"

    texto = _limpar_html(resp.text, max_chars)
    if len(texto) < 200:
        return (f"{texto}\n\n[AVISO: a pagina devolveu pouco texto. "
                "Pode ser conteudo renderizado por JavaScript - "
                "tente ler_pagina_dinamica.]")
    return texto


@tool
def ler_pagina_dinamica(url: str, espera: int = 3,
                        max_chars: int = 4000) -> str:
    """Como ler_pagina, mas executa o JavaScript da pagina antes de ler.

    Use apenas quando ler_pagina devolver conteudo vazio ou incompleto: e
    muito mais lento (segundos, nao milissegundos).

    Args:
        url: endereco completo da pagina
        espera: segundos de espera apos carregar, para o JS terminar
        max_chars: limite de caracteres devolvidos
    """
    if not url.startswith(("http://", "https://")):
        return "ERRO: url deve comecar com http:// ou https://"

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        return ("ERRO: pacote 'selenium' nao instalado. "
                "Rode: pip install selenium")

    opcoes = Options()
    opcoes.add_argument("--headless=new")
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")

    navegador = None
    try:
        navegador = webdriver.Chrome(options=opcoes)
        navegador.get(url)
        time.sleep(espera)
        html = navegador.page_source
    except Exception as e:
        return f"ERRO no navegador: {type(e).__name__}: {e}"
    finally:
        # sem isso, cada falha deixa um Chrome vivo consumindo memoria
        if navegador is not None:
            navegador.quit()

    return _limpar_html(html, max_chars)


def buscar_tavily(max_results: int = 5):
    """A alternativa paga: devolve trecho limpo em vez de fragmento de HTML.

    Exige TAVILY_API_KEY no .env. Nao e usada no laboratorio do curso -
    existe aqui para o aluno saber trocar quando o projeto justificar.
    """
    from dotenv import load_dotenv
    from langchain_tavily import TavilySearch

    load_dotenv()
    return TavilySearch(max_results=max_results, topic="general")


FERRAMENTAS_WEB = [buscar_web, ler_pagina, ler_pagina_dinamica]


if __name__ == "__main__":
    print("== buscar_web ==")
    print(buscar_web.invoke({"consulta": "o que e o padrao ReAct em agentes",
                             "k": 3})[:600])
    print("\n== ler_pagina ==")
    print(ler_pagina.invoke({"url": "https://example.com"})[:400])
