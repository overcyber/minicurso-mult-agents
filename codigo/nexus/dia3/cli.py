"""CLI do dia 3: streaming, memoria por thread e aprovacao antes de agir."""
import argparse

from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import Command
from rich.console import Console
from rich.panel import Panel

from nexus import compilar

console = Console()
SENSIVEIS = {"salvar_relatorio"}


def mostrar(no: str, delta: dict):
    msgs = delta.get("messages") or []
    if not msgs:
        return
    texto = str(getattr(msgs[-1], "content", ""))[:600]
    if texto.strip():
        console.print(Panel(texto, title=no, border_style="cyan"))


def main():
    p = argparse.ArgumentParser(description="NEXUS dia 3")
    p.add_argument("pergunta")
    p.add_argument("--thread", default="demo")
    p.add_argument("--sem-aprovacao", action="store_true")
    args = p.parse_args()

    grafo = compilar(aprovar_ferramentas=not args.sem_aprovacao)
    config = {"configurable": {"thread_id": args.thread}}
    entrada = {"messages": [HumanMessage(args.pergunta)], "passos": 0}

    while True:
        for evento in grafo.stream(entrada, config, stream_mode="updates"):
            for no, delta in evento.items():
                mostrar(no, delta)

        estado = grafo.get_state(config)
        if not estado.next:
            break

        chamadas = getattr(estado.values["messages"][-1], "tool_calls", []) or []
        precisa = [c for c in chamadas if c["name"] in SENSIVEIS]
        if precisa and not args.sem_aprovacao:
            for c in precisa:
                console.print(Panel(str(c["args"])[:800],
                                    title=f"aprovar {c['name']}?", border_style="red"))
            if console.input("[bold]executar? [s/n] [/]").strip().lower() != "s":
                console.print("[yellow]acao recusada[/]")
                recusas = [ToolMessage(
                    content="Usuario recusou a acao. Explique e proponha uma "
                            "alternativa que nao escreva em disco.",
                    tool_call_id=c["id"]) for c in precisa]
                grafo.update_state(config, {"messages": recusas}, as_node="ferramentas")
        entrada = None

    final = grafo.get_state(config).values["messages"][-1]
    console.print(Panel(str(final.content), title="resposta", border_style="green"))


if __name__ == "__main__":
    main()
