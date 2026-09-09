"""Interface Gradio sobre o grafo multi-agente.

O ponto desta demo: o GRAFO NAO MUDA. Sao vinte linhas de interface sobre
exatamente a mesma equipe que roda no terminal. O thread_id, que ate agora era
um parametro abstrato, vira um campo na tela - e a forma mais rapida de a turma
entender o que o checkpointer faz e digitar um nome novo e ver a memoria sumir.
"""
import pathlib
import sys

BASE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

import gradio as gr
from langchain_core.messages import HumanMessage

from equipe import compilar

EQUIPE = compilar()

CORES = {"supervisor": "#4C3A8C", "pesquisador": "#1B7F5C",
         "analista": "#B8860B", "redator": "#9C27B0", "critico": "#C62828"}


def responder(mensagem, historico, sessao):
    """Gerador: cada yield atualiza a tela. Com return, tudo aparece no fim."""
    config = {"configurable": {"thread_id": sessao or "demo"}}
    entrada = {
        "messages": [HumanMessage(mensagem)],
        "pergunta": mensagem,
        "rodadas": 0,
        "achados": [],
    }

    parcial = ""
    try:
        for evento in EQUIPE.stream(entrada, config, stream_mode="updates"):
            for no, delta in evento.items():
                msgs = delta.get("messages", [])
                if not msgs:
                    continue
                conteudo = getattr(msgs[-1], "content", "")
                if not conteudo:
                    continue
                cor = CORES.get(no, "#6B6580")
                parcial += (f"\n\n<span style='color:{cor};font-weight:600'>"
                            f"[{no}]</span>\n\n{conteudo}")
                yield parcial
    except Exception as e:
        yield parcial + f"\n\n**ERRO**: {type(e).__name__}: {e}"

    if not parcial:
        yield "O grafo terminou sem produzir texto. Confira o traco."


with gr.Blocks(title="NEXUS", theme=gr.themes.Soft()) as app:
    gr.Markdown(
        "# NEXUS\n"
        "Agencia de pesquisa local. Modelo, documentos e embeddings rodam "
        "na sua maquina."
    )
    sessao = gr.Textbox(
        label="Sessao",
        value="demo",
        info="Este e o thread_id. Mude para comecar uma conversa nova, "
             "repita para retomar a anterior.",
    )
    gr.ChatInterface(
        fn=responder,
        additional_inputs=[sessao],
        type="messages",
        examples=[
            ["Compare os tres fornecedores por custo total em 24 meses."],
            ["Qual foi o faturamento de 2024 e como se compara a 2023?"],
            ["Resuma o estatuto em cinco pontos."],
        ],
    )
    gr.Markdown(
        "> Nao use `share=True` com um agente que tem shell e acesso ao disco: "
        "o tunel e publico."
    )


if __name__ == "__main__":
    app.launch(server_name="127.0.0.1", server_port=7860, share=False)
