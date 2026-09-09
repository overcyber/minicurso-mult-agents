"""NEXUS multi-agente: supervisor, especialistas e critico."""
import operator
import pathlib
import sys
from typing import Annotated, Literal, TypedDict

BASE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "dia2"))

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph, add_messages
from pydantic import BaseModel, Field

import prompts
from ferramentas import calcular, fazer_busca, ler_arquivo, listar_arquivos, salvar_relatorio
from indexar import construir

MAX_RODADAS = 3


class EstadoEquipe(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    pergunta: str
    proximo: str
    instrucao: str
    achados: Annotated[list[str], operator.add]
    rascunho: str
    veredito: str
    rodadas: int


class Roteamento(BaseModel):
    """Decisao de qual agente deve trabalhar em seguida."""
    proximo: Literal["pesquisador", "analista", "redator", "critico", "FIM"]
    instrucao: str = Field(description="O que exatamente esse agente deve fazer agora")
    motivo: str = Field(description="Por que este agente e nao outro")


class Critica(BaseModel):
    veredito: Literal["aprovado", "revisar"]
    problemas: list[str] = Field(default_factory=list)
    sugestao: str = ""


def fazer_especialista(nome: str, prompt: str, ferramentas: list, llm):
    agente = create_agent(model=llm, tools=ferramentas, system_prompt=prompt)

    def no(estado: EstadoEquipe) -> dict:
        # isolamento de contexto: o especialista recebe a tarefa, nao o historico
        tarefa = (f"Tarefa: {estado['instrucao']}\n\n"
                  f"Pergunta original do usuario: {estado['pergunta']}")
        if nome in ("redator", "critico") and estado.get("achados"):
            tarefa += "\n\nAchados da equipe:\n" + "\n".join(estado["achados"])
        saida = agente.invoke({"messages": [HumanMessage(tarefa)]})
        texto = saida["messages"][-1].content
        delta = {"messages": [AIMessage(content=texto, name=nome)],
                 "achados": [f"[{nome}] {texto}"]}
        if nome == "redator":
            delta["rascunho"] = texto
        return delta

    return no


def construir_equipe(modelo: str = "qwen3:4b"):
    banco = construir()
    buscar = fazer_busca(banco)
    llm = ChatOllama(model=modelo, temperature=0)
    llm_redator = ChatOllama(model=modelo, temperature=0.3)

    def no_supervisor(estado: EstadoEquipe) -> dict:
        contexto = (f"Pergunta: {estado['pergunta']}\n\n"
                    f"Ja foi feito:\n" + ("\n".join(estado.get("achados", [])) or "nada ainda")
                    + f"\n\nVeredito do critico ate agora: {estado.get('veredito', 'nenhum')}")
        d = llm.with_structured_output(Roteamento).invoke(
            [SystemMessage(prompts.SUPERVISOR), HumanMessage(contexto)])
        return {"proximo": d.proximo, "instrucao": d.instrucao,
                "messages": [AIMessage(content=f"-> {d.proximo}: {d.motivo}",
                                       name="supervisor")]}

    def no_critico(estado: EstadoEquipe) -> dict:
        c = llm.with_structured_output(Critica).invoke([
            SystemMessage(prompts.CRITICO),
            HumanMessage(f"Pergunta: {estado['pergunta']}\n\n"
                         f"Achados:\n" + "\n".join(estado.get("achados", [])) +
                         f"\n\nRelatorio:\n{estado.get('rascunho', '(vazio)')}"),
        ])
        return {"veredito": c.veredito,
                "rodadas": estado.get("rodadas", 0) + 1,
                "messages": [AIMessage(
                    content=f"Critica: {c.veredito}. Problemas: {c.problemas}. {c.sugestao}",
                    name="critico")],
                "achados": [f"[critico] {c.veredito}: {'; '.join(c.problemas)}"]}

    g = StateGraph(EstadoEquipe)
    g.add_node("supervisor", no_supervisor)
    g.add_node("pesquisador", fazer_especialista(
        "pesquisador", prompts.PESQUISADOR, [buscar, listar_arquivos, ler_arquivo], llm))
    g.add_node("analista", fazer_especialista(
        "analista", prompts.ANALISTA, [calcular], llm))
    g.add_node("redator", fazer_especialista(
        "redator", prompts.REDATOR, [], llm_redator))
    g.add_node("critico", no_critico)

    g.add_edge(START, "supervisor")
    for esp in ("pesquisador", "analista", "redator"):
        g.add_edge(esp, "supervisor")

    def rotear_supervisor(estado: EstadoEquipe) -> str:
        if estado.get("rodadas", 0) >= MAX_RODADAS:
            return END
        return END if estado["proximo"] == "FIM" else estado["proximo"]

    def rotear_critico(estado: EstadoEquipe) -> str:
        if estado["veredito"] == "aprovado" or estado.get("rodadas", 0) >= MAX_RODADAS:
            return END
        return "supervisor"

    g.add_conditional_edges("supervisor", rotear_supervisor,
                            ["pesquisador", "analista", "redator", "critico", END])
    g.add_conditional_edges("critico", rotear_critico, ["supervisor", END])
    return g


def compilar(caminho_db: str = "equipe.db"):
    memoria = SqliteSaver.from_conn_string(caminho_db).__enter__()
    return construir_equipe().compile(checkpointer=memoria)


if __name__ == "__main__":
    equipe = compilar()
    print(equipe.get_graph().draw_ascii())
