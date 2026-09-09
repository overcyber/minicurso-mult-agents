"""CLI de demonstracao do NEXUS completo."""
import argparse
import json
import pathlib
import sys
import time

BASE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "dia4"))

from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from equipe import compilar

console = Console()
CORES = {"supervisor": "cyan", "pesquisador": "green", "analista": "yellow",
         "redator": "magenta", "critico": "red"}


def main():
    p = argparse.ArgumentParser(description="NEXUS - agencia de pesquisa local")
    p.add_argument("pergunta")
    p.add_argument("--thread", default="demo")
    p.add_argument("--saida", default="relatorio.md")
    p.add_argument("--traco", default="tracos/execucao.jsonl")
    args = p.parse_args()

    equipe = compilar()
    config = {"configurable": {"thread_id": args.thread}}
    entrada = {"messages": [HumanMessage(args.pergunta)], "pergunta": args.pergunta,
               "proximo": "", "instrucao": args.pergunta, "achados": [],
               "rascunho": "", "veredito": "", "rodadas": 0}

    pathlib.Path(args.traco).parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    transicoes = 0

    with open(args.traco, "a", encoding="utf-8") as traco:
        for evento in equipe.stream(entrada, config, stream_mode="updates"):
            for no, delta in evento.items():
                transicoes += 1
                msgs = delta.get("messages") or []
                texto = str(getattr(msgs[-1], "content", ""))[:700] if msgs else ""
                if texto.strip():
                    console.print(Panel(texto, title=no,
                                        border_style=CORES.get(no, "white")))
                traco.write(json.dumps({"t": round(time.time() - t0, 2), "no": no,
                                        "chaves": list(delta.keys()),
                                        "resumo": texto[:400]},
                                       ensure_ascii=False) + "\n")

    final = equipe.get_state(config).values
    relatorio = final.get("rascunho") or "(sem relatorio)"
    pathlib.Path(args.saida).write_text(relatorio, encoding="utf-8")

    t = Table(title="execucao")
    t.add_column("metrica"); t.add_column("valor", justify="right")
    t.add_row("transicoes", str(transicoes))
    t.add_row("rodadas de critica", str(final.get("rodadas", 0)))
    t.add_row("veredito", final.get("veredito", "-"))
    t.add_row("tempo", f"{time.time() - t0:.1f}s")
    console.print(t)
    console.print(f"[bold green]Relatorio salvo em {args.saida}[/]")


if __name__ == "__main__":
    main()
