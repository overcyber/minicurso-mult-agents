"""Demo de remocao de fundo para publicar no Hugging Face Spaces.

O ponto pedagogico nao e a imagem. E que a mecanica e IDENTICA a de qualquer
outro modelo do Hub: escolher por tarefa, ler o card, instalar, chamar,
avaliar. O aluno aplica a metodologia do dia 5 a um dominio que nao foi
ensinado - que e exatamente o que se espera dele depois do curso.

Para publicar:
  1. huggingface-cli login
  2. crie um Space (SDK: gradio) em huggingface.co/new-space
  3. git init && git remote add origin <url do space>
  4. git add . && git commit -m "primeira versao" && git push origin main

Nunca comite chave de API: um Space e um repositorio Git publico. Segredos vao
em Settings -> Repository secrets.
"""
import gradio as gr
from rembg import remove


def processar(imagem):
    if imagem is None:
        return None
    return remove(imagem)


demo = gr.Interface(
    fn=processar,
    inputs=gr.Image(type="pil", label="Imagem original"),
    outputs=gr.Image(type="pil", label="Sem fundo", format="png"),
    title="Removedor de fundo",
    description=("Modelo de segmentacao rodando localmente, sem chamada a "
                 "nenhuma API. Envie uma imagem e receba a versao com fundo "
                 "transparente."),
    article=("Construido no curso Sistemas Multi-Agente com Modelos Locais. "
             "O tier gratuito do Spaces e CPU com 16 GB - serve para modelos "
             "pequenos como este, e nao serve para um LLM de 4B."),
    flagging_mode="never",
    examples=None,
)


if __name__ == "__main__":
    demo.launch()
