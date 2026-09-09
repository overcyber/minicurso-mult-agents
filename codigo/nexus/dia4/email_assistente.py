"""Assistente de e-mail: triagem por intencao, roteamento e aprovacao humana.

Este arquivo existe para provar que voce aprendeu uma ARQUITETURA, nao um
projeto. Nenhuma peca nova: saida estruturada do dia 2, grafo e interrupt do
dia 3, roteamento condicional do dia 4, e o retriever do dia 2 reaproveitado
como base de FAQ.

Rode:  python email_assistente.py --arquivo dados/emails.json
"""
import argparse
import csv
import json
import pathlib
import sys
from typing import Literal, TypedDict

BASE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "dia2"))

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field

MODELO = "qwen3:4b"


class EstadoEmail(TypedDict, total=False):
    remetente: str
    assunto: str
    corpo: str
    intencao: str
    urgencia: str
    resumo: str
    rascunho: str
    rota: str
    decisao: str


class Triagem(BaseModel):
    """Classificacao de um e-mail recebido.

    As descricoes de cada classe nao sao enfeite: sem elas o modelo joga quase
    tudo em 'outro'. Vale demonstrar isso em sala removendo-as.
    """

    intencao: Literal["duvida_produto", "reclamacao", "orcamento",
                      "spam", "outro"] = Field(
        description=(
            "duvida_produto: pergunta sobre como algo funciona, prazo, "
            "politica, garantia. "
            "reclamacao: cliente insatisfeito, problema ja ocorrido. "
            "orcamento: pedido de preco ou proposta comercial. "
            "spam: propaganda nao solicitada, phishing, corrente. "
            "outro: nao se encaixa em nenhuma acima."
        )
    )
    urgencia: Literal["baixa", "media", "alta"] = Field(
        description=("alta: prejuizo em curso, prazo legal, cliente ameacando "
                     "cancelar. media: espera resposta hoje. baixa: o resto.")
    )
    resumo: str = Field(description="Uma frase: o que a pessoa quer")


def construir_grafo(modelo: str = MODELO, retriever=None):
    llm = ChatOllama(model=modelo, temperature=0)
    triador = llm.with_structured_output(Triagem)

    def no_triagem(estado: EstadoEmail) -> dict:
        t = triador.invoke([
            SystemMessage("Classifique o e-mail abaixo. Seja conservador na "
                          "urgencia: 'alta' so quando houver prejuizo em curso."),
            HumanMessage(f"De: {estado['remetente']}\n"
                         f"Assunto: {estado['assunto']}\n\n{estado['corpo']}"),
        ])
        return {"intencao": t.intencao, "urgencia": t.urgencia,
                "resumo": t.resumo}

    def rotear(estado: EstadoEmail) -> str:
        if estado["intencao"] == "spam":
            return "arquivar"
        if estado["urgencia"] == "alta" or estado["intencao"] == "reclamacao":
            return "escalar"
        if estado["intencao"] == "duvida_produto":
            return "responder_com_faq"
        return "responder_simples"

    def no_arquivar(estado: EstadoEmail) -> dict:
        return {"rota": "arquivar", "rascunho": "", "decisao": "arquivado"}

    def no_escalar(estado: EstadoEmail) -> dict:
        texto = (f"ESCALADO PARA HUMANO\n"
                 f"Motivo: {estado['intencao']} / urgencia "
                 f"{estado['urgencia']}\n"
                 f"Resumo: {estado['resumo']}")
        return {"rota": "escalar", "rascunho": texto}

    def no_faq(estado: EstadoEmail) -> dict:
        # Reuso literal do retriever do dia 2 - se voce precisou reescrever,
        # o dia 2 ficou acoplado demais e vale refatorar.
        contexto = ""
        if retriever is not None:
            achados = retriever.similarity_search(estado["corpo"], k=3)
            contexto = "\n\n".join(
                f"[fonte: {d.metadata.get('source', '?')}]\n{d.page_content}"
                for d in achados)

        sistema = (
            "Voce responde e-mails de clientes usando SOMENTE o contexto "
            "abaixo. Se o contexto nao responder, diga que vai verificar e "
            "encaminhe - nao invente politica nem prazo.\n\n"
            f"Contexto:\n{contexto if contexto else '(base vazia)'}"
        )
        r = llm.invoke([SystemMessage(sistema),
                        HumanMessage(estado["corpo"])])
        return {"rota": "responder_com_faq", "rascunho": r.content}

    def no_simples(estado: EstadoEmail) -> dict:
        r = llm.invoke([
            SystemMessage("Escreva uma resposta curta, cordial e objetiva. "
                          "Nao prometa prazo nem valor que nao esteja no "
                          "e-mail original."),
            HumanMessage(estado["corpo"]),
        ])
        return {"rota": "responder_simples", "rascunho": r.content}

    def no_aprovacao(estado: EstadoEmail) -> Command:
        decisao = interrupt({
            "para": estado["remetente"],
            "assunto": f"Re: {estado['assunto']}",
            "rascunho": estado["rascunho"],
            "intencao": estado["intencao"],
            "urgencia": estado["urgencia"],
        })
        acao = decisao.get("acao", "descartar")
        if acao == "enviar":
            return Command(goto="enviar", update={"decisao": "enviado"})
        if acao == "editar":
            return Command(goto="enviar",
                           update={"rascunho": decisao.get("texto", ""),
                                   "decisao": "editado_e_enviado"})
        return Command(goto=END, update={"decisao": "descartado"})

    def no_enviar(estado: EstadoEmail) -> dict:
        # O curso para no rascunho. Conectar a IMAP/Gmail/Outlook e trabalho
        # de integracao, especifico de cada ambiente, e nao muda a arquitetura.
        print(f"\n[ENVIADO] para {estado['remetente']}\n{estado['rascunho']}\n")
        return {}

    g = StateGraph(EstadoEmail)
    g.add_node("triagem", no_triagem)
    g.add_node("arquivar", no_arquivar)
    g.add_node("escalar", no_escalar)
    g.add_node("responder_com_faq", no_faq)
    g.add_node("responder_simples", no_simples)
    g.add_node("aprovacao", no_aprovacao)
    g.add_node("enviar", no_enviar)

    g.add_edge(START, "triagem")
    g.add_conditional_edges("triagem", rotear, {
        "arquivar": "arquivar",
        "escalar": "escalar",
        "responder_com_faq": "responder_com_faq",
        "responder_simples": "responder_simples",
    })
    g.add_edge("arquivar", END)
    g.add_edge("escalar", "aprovacao")
    g.add_edge("responder_com_faq", "aprovacao")
    g.add_edge("responder_simples", "aprovacao")
    g.add_edge("enviar", END)

    return g.compile(checkpointer=InMemorySaver())


def processar(caminho: str, saida_csv: str = "triagem.csv",
              automatico: bool = False):
    emails = json.loads(pathlib.Path(caminho).read_text(encoding="utf-8"))
    grafo = construir_grafo()
    linhas = []

    for i, email in enumerate(emails):
        config = {"configurable": {"thread_id": f"email-{i}"}}
        estado = grafo.invoke(email, config)

        decisao = estado.get("decisao", "")
        if not decisao:
            # o grafo parou no interrupt: e aqui que o humano entra
            pendente = grafo.get_state(config).tasks[0].interrupts[0].value
            print("=" * 70)
            print(f"Para: {pendente['para']} | {pendente['assunto']}")
            print(f"Intencao: {pendente['intencao']} | "
                  f"urgencia: {pendente['urgencia']}")
            print("-" * 70)
            print(pendente["rascunho"])
            print("-" * 70)
            if automatico:
                escolha = {"acao": "enviar"}
            else:
                resp = input("[e]nviar / [d]escartar / [t]exto novo: ").strip()
                if resp.startswith("t"):
                    escolha = {"acao": "editar", "texto": input("Novo texto: ")}
                elif resp.startswith("e"):
                    escolha = {"acao": "enviar"}
                else:
                    escolha = {"acao": "descartar"}
            estado = grafo.invoke(Command(resume=escolha), config)

        linhas.append({
            "remetente": estado.get("remetente", ""),
            "assunto": estado.get("assunto", ""),
            "intencao": estado.get("intencao", ""),
            "urgencia": estado.get("urgencia", ""),
            "rota": estado.get("rota", ""),
            "decisao": estado.get("decisao", ""),
        })

    with open(saida_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)
    print(f"\n{len(linhas)} e-mails processados. Resultado em {saida_csv}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Assistente de e-mail do NEXUS")
    p.add_argument("--arquivo", default=str(BASE / "dados" / "emails.json"))
    p.add_argument("--saida", default="triagem.csv")
    p.add_argument("--automatico", action="store_true",
                   help="aprova tudo sem perguntar (so para teste)")
    args = p.parse_args()
    processar(args.arquivo, args.saida, args.automatico)
