"""Steering: corrigir o agente ENQUANTO ele trabalha.

Os tres mecanismos do curso, e onde cada um age:

    instruction  fala ANTES     (prompt de sistema)
    constraint   IMPEDE         (hooks.py)
    steering     corrige DURANTE (este modulo)

A diferenca entre abortar e orientar e a diferenca entre constraint e steering.
Abortar encerra a execucao; orientar da ao agente a chance de mudar de abordagem
com a informacao de que a atual nao esta funcionando.

Sistemas maduros fazem os dois, nesta ordem: primeiro orientam, e so abortam se a
orientacao nao resolver.

Todas as funcoes aqui sao puras: recebem estado, devolvem delta. Testaveis sem LLM.
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage

JANELA = 6          # quantas mensagens de ferramenta olhar para tras
REPETICOES = 3      # a partir de quantas identicas consideramos travado
MAX_ORIENTACOES = 2 # depois disso, abortar e melhor que insistir


def _chamadas_recentes(estado: dict) -> list[tuple[str, str]]:
    """Assinatura (nome da ferramenta, conteudo) das ultimas observacoes."""
    saida = []
    for m in estado.get("messages", [])[-JANELA:]:
        if getattr(m, "type", "") == "tool":
            saida.append((getattr(m, "name", "?"), str(getattr(m, "content", ""))[:200]))
    return saida


def detectar_repeticao(estado: dict) -> bool:
    """True quando as ultimas observacoes sao identicas entre si."""
    chamadas = _chamadas_recentes(estado)
    return len(chamadas) >= REPETICOES and len(set(chamadas)) == 1


def detectar_estagnacao(estado: dict) -> bool:
    """True quando o agente gastou muitos passos sem produzir nenhum achado."""
    return estado.get("passos", 0) >= 6 and not estado.get("achados")


def no_steering(estado: dict) -> dict:
    """No do grafo. Devolve delta vazio quando nao ha nada a corrigir.

    Coloque-o ANTES do no do agente, com uma conditional edge que so desvia para ele
    quando ha sinal de desvio. Rodar em todo passo desperdicaria uma passagem por volta.
    """
    ja_orientou = estado.get("orientacoes", 0)
    if ja_orientou >= MAX_ORIENTACOES:
        return {}

    if detectar_repeticao(estado):
        return {
            "orientacoes": ja_orientou + 1,
            "messages": [HumanMessage(
                "Voce repetiu a mesma chamada tres vezes e obteve o mesmo resultado. "
                "Nao repita de novo. Faca UMA destas coisas: (a) reformule a consulta "
                "com outros termos, (b) use outra ferramenta, ou (c) responda com o que "
                "ja tem e diga explicitamente o que nao foi possivel apurar.")],
        }

    if detectar_estagnacao(estado):
        return {
            "orientacoes": ja_orientou + 1,
            "messages": [HumanMessage(
                "Voce ja gastou varios passos sem registrar nenhum achado. "
                "Comece pelo mais barato: buscar_documentos na base local. "
                "Se a resposta nao estiver la, diga isso antes de partir para a web.")],
        }

    return {}


def precisa_de_steering(estado: dict) -> str:
    """Funcao de roteamento. Use em add_conditional_edges."""
    if estado.get("orientacoes", 0) >= MAX_ORIENTACOES:
        return "agente"
    if detectar_repeticao(estado) or detectar_estagnacao(estado):
        return "steering"
    return "agente"
