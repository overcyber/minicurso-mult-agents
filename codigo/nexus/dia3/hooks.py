"""Registro de politicas de PreToolUse: a camada de constraints do dia 3.

A diferenca entre instruction e constraint esta aqui, em codigo:

    instruction  -> texto no prompt pedindo bom comportamento (probabilistico)
    constraint   -> uma funcao que roda ANTES da ferramenta e pode NEGAR (deterministico)

Contrato de uma politica:

    politica(ferramenta: str, args: dict, estado: dict | None) -> str | None

    devolver None   = permitir
    devolver string = NEGAR, e a string e o motivo que volta ao modelo

O motivo importa: uma recusa bem escrita e uma instrucao. Compare

    "NEGADO"
    "NEGADO: escrita fora de saida/ nao e permitida; use saida/relatorio.md"

A primeira faz o agente tentar de novo ate o limite de passos. A segunda faz ele
acertar na volta seguinte.

Todas as politicas deste modulo sao funcoes puras e testaveis SEM LLM nenhum.
Ver testes/test_hooks.py.
"""
from __future__ import annotations

import pathlib
import re
from typing import Callable, Optional

Politica = Callable[[str, dict, Optional[dict]], Optional[str]]

PRE: list[Politica] = []

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SAIDA = (RAIZ / "saida").resolve()
DOCS = (RAIZ / "docs").resolve()

MAX_BUSCAS_POR_EXECUCAO = 10
MAX_CHARS_RELATORIO = 60_000


def pre_tool_use(fn: Politica) -> Politica:
    """Registra uma politica de PreToolUse."""
    PRE.append(fn)
    return fn


def limpar_politicas() -> None:
    """Usado pelos testes para isolar cenarios."""
    PRE.clear()


# ---------------------------------------------------------------- politicas


@pre_tool_use
def proteger_escrita_fora_da_saida(ferramenta, args, estado=None):
    """Escrita so dentro de saida/. Vale para qualquer ferramenta que escreve."""
    if ferramenta not in {"salvar_relatorio", "escrever_arquivo"}:
        return None
    nome = args.get("nome") or args.get("caminho") or ""
    destino = (SAIDA / nome).resolve()
    if not str(destino).startswith(str(SAIDA)):
        return (f"escrita fora de {SAIDA.name}/ nao e permitida; "
                f"use um nome simples como relatorio.md")
    return None


@pre_tool_use
def proteger_leitura_fora_de_docs(ferramenta, args, estado=None):
    """Leitura de arquivo so dentro de docs/."""
    if ferramenta != "ler_arquivo":
        return None
    alvo = (DOCS / args.get("caminho", "")).resolve()
    if not str(alvo).startswith(str(DOCS)):
        return f"leitura fora de {DOCS.name}/ nao e permitida"
    return None


@pre_tool_use
def limitar_buscas(ferramenta, args, estado=None):
    """Teto de buscas por execucao. Le o contador do estado, nao de variavel global."""
    if ferramenta not in {"buscar_web", "buscar_documentos"}:
        return None
    if estado is None:
        return None
    usadas = estado.get("buscas", 0)
    if usadas >= MAX_BUSCAS_POR_EXECUCAO:
        return (f"limite de {MAX_BUSCAS_POR_EXECUCAO} buscas por execucao atingido; "
                f"responda com o que ja foi apurado e diga o que faltou")
    return None


@pre_tool_use
def recusar_comando_destrutivo(ferramenta, args, estado=None):
    """Defesa em profundidade para qualquer ferramenta que aceite comando de shell."""
    if "comando" not in args:
        return None
    perigosos = re.compile(r"\brm\s+-rf\b|\bmkfs\b|\bdd\s+if=|\bshutdown\b|:\(\)\{")
    if perigosos.search(str(args["comando"])):
        return "comando destrutivo bloqueado pela politica de seguranca"
    return None


@pre_tool_use
def limitar_tamanho_do_relatorio(ferramenta, args, estado=None):
    """Relatorio gigante costuma ser loop, nao trabalho."""
    if ferramenta != "salvar_relatorio":
        return None
    conteudo = str(args.get("conteudo", ""))
    if len(conteudo) > MAX_CHARS_RELATORIO:
        return (f"relatorio com {len(conteudo)} caracteres excede o limite de "
                f"{MAX_CHARS_RELATORIO}; resuma antes de salvar")
    return None


# ---------------------------------------------------------------- execucao


def avaliar_politicas(ferramenta: str, args: dict, estado: dict | None = None) -> str | None:
    """Devolve o motivo da primeira recusa, ou None se todas permitirem."""
    for politica in PRE:
        motivo = politica(ferramenta, args, estado)
        if motivo:
            return motivo
    return None


def executar_com_hooks(registro: dict, ferramenta: str, args: dict,
                       estado: dict | None = None) -> str:
    """Substitui REGISTRO[ferramenta].invoke(args), passando pelas politicas antes.

    Devolve sempre texto: o resultado da ferramenta, o motivo da recusa, ou o erro.
    Uma excecao aqui derrubaria o loop inteiro, e o dia 2 ja explicou por que isso
    e inaceitavel.
    """
    motivo = avaliar_politicas(ferramenta, args, estado)
    if motivo:
        return f"NEGADO pela politica: {motivo}"

    alvo = registro.get(ferramenta)
    if alvo is None:
        validas = ", ".join(sorted(registro)) or "nenhuma"
        return f"ERRO: ferramenta '{ferramenta}' nao existe. Validas: {validas}"

    try:
        return str(alvo.invoke(args))
    except Exception as e:  # nao recuperavel pela ferramenta, recuperavel pelo agente
        return f"ERRO ao executar {ferramenta}: {type(e).__name__}: {e}"
