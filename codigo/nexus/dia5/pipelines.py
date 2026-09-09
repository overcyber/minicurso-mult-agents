"""Pipelines prontos: as tarefas que ja estao resolvidas.

A regra que este arquivo demonstra: se a tarefa TEM NOME, provavelmente ja
existe um modelo pequeno que a resolve melhor, mais rapido e mais barato que um
LLM generalista. Sentimento tem nome. Extracao de resposta tem nome.
Classificacao tem nome. "Pesquisar, cruzar com nossos documentos e escrever um
relatorio critico" nao tem - e ai o agente ganha.

Rode:  python pipelines.py sentimento
       python pipelines.py categorias
       python pipelines.py faq
       python pipelines.py chat
"""
import argparse
import pathlib
import sys
import time

BASE = pathlib.Path(__file__).resolve().parent.parent
DADOS = BASE / "dados"
SAIDA = BASE / "saida"

MODELO_SENTIMENTO = "nlptown/bert-base-multilingual-uncased-sentiment"
MODELO_ZEROSHOT = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
MODELO_QA = "deepset/xlm-roberta-base-squad2"
MODELO_CHAT = "Qwen/Qwen3-0.6B"

CATEGORIAS = ["maquinario agricola", "pecas de reposicao",
              "equipamento industrial", "ferramenta manual",
              "insumo quimico", "servico"]

STOPWORDS_PT = {
    "que", "para", "com", "uma", "mas", "por", "dos", "das", "nao", "muito",
    "produto", "mais", "sem", "foi", "esta", "isso", "ele", "ela", "meu",
    "minha", "seu", "sua", "como", "quando", "onde", "pelo", "pela", "nos",
    "num", "numa", "ate", "ja", "so", "tem", "ter", "ser", "era", "sao",
    "dia", "dias", "vez", "fazer", "todo", "toda", "aqui", "depois", "ainda",
}


def _carregar_avaliacoes():
    import pandas as pd
    caminho = DADOS / "avaliacoes.csv"
    if not caminho.exists():
        sys.exit(f"ERRO: {caminho} nao existe. Ver dados/ no repositorio.")
    return pd.read_csv(caminho)


# --------------------------------------------------------------------------
# 1. Analise de sentimento em lote
# --------------------------------------------------------------------------

def sentimento(gerar_nuvem: bool = True):
    from transformers import pipeline

    df = _carregar_avaliacoes()
    analisador = pipeline("sentiment-analysis", model=MODELO_SENTIMENTO)

    # Em lote: a diferenca entre um script utilizavel e um inutilizavel esta
    # neste parametro. truncation=True evita que uma avaliacao longa derrube
    # tudo com erro de tamanho de sequencia.
    t0 = time.perf_counter()
    resultados = analisador(df["texto"].tolist(), batch_size=16,
                            truncation=True)
    t_lote = time.perf_counter() - t0

    # Item a item, so nas 50 primeiras, para o aluno extrapolar
    t0 = time.perf_counter()
    for texto in df["texto"].tolist()[:50]:
        analisador(texto, truncation=True)
    t_um = time.perf_counter() - t0

    # O rotulo e uma string ("4 stars"), nao um numero. Cada modelo rotula a
    # sua maneira: leia o card antes de assumir o formato.
    df["estrelas"] = [int(r["label"][0]) for r in resultados]
    df["confianca"] = [round(r["score"], 3) for r in resultados]

    print(f"Em lote (300 itens, batch_size=16): {t_lote:.1f}s")
    print(f"Item a item (50 itens): {t_um:.1f}s "
          f"-> ~{t_um * 6:.0f}s para 300")
    print(f"Ganho: {(t_um * 6) / t_lote:.1f}x\n")

    print(df.groupby("produto")["estrelas"]
            .agg(["mean", "count"])
            .sort_values("mean")
            .round(2))

    SAIDA.mkdir(exist_ok=True)
    df.to_csv(SAIDA / "avaliacoes_com_sentimento.csv", index=False)

    if gerar_nuvem:
        _nuvem(df)
    return df


def _nuvem(df):
    try:
        from wordcloud import WordCloud
    except ImportError:
        print("\n[pulei a nuvem: pip install wordcloud matplotlib]")
        return

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    conjuntos = {
        "negativas": (df["estrelas"] <= 2, "RdGy", STOPWORDS_PT),
        "positivas": (df["estrelas"] >= 4, "YlGn", STOPWORDS_PT),
        "negativas_sem_stopwords": (df["estrelas"] <= 2, "RdGy", set()),
    }

    for nome, (mascara, cor, stops) in conjuntos.items():
        texto = " ".join(df.loc[mascara, "texto"])
        if not texto.strip():
            continue
        nuvem = WordCloud(width=1200, height=600, background_color="white",
                          stopwords=stops, colormap=cor,
                          collocations=False).generate(texto)
        plt.figure(figsize=(12, 6))
        plt.imshow(nuvem, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout()
        destino = SAIDA / f"nuvem_{nome}.png"
        plt.savefig(destino, dpi=110)
        plt.close()
        print(f"gerado: {destino}")

    print("\nCompare nuvem_negativas com nuvem_negativas_sem_stopwords: a "
          "lista de stopwords e o que separa um grafico de um enfeite.")


# --------------------------------------------------------------------------
# 2. Categorizacao zero-shot com corte por score
# --------------------------------------------------------------------------

def categorias(corte: float = 0.5):
    from transformers import pipeline

    df = _carregar_avaliacoes().drop_duplicates("produto")
    clf = pipeline("zero-shot-classification", model=MODELO_ZEROSHOT)

    linhas = []
    for _, linha in df.iterrows():
        r = clf(linha["descricao"], candidate_labels=CATEGORIAS)
        linhas.append({
            "produto": linha["produto"],
            "categoria": r["labels"][0],
            "score": round(r["scores"][0], 3),
            "segunda_opcao": r["labels"][1],
        })

    import pandas as pd
    res = pd.DataFrame(linhas).sort_values("score")
    print(res.to_string(index=False))

    duvidosos = res[res["score"] < corte]
    SAIDA.mkdir(exist_ok=True)
    duvidosos.to_csv(SAIDA / "revisar.csv", index=False)
    print(f"\n{len(duvidosos)} itens abaixo de {corte} -> saida/revisar.csv")
    print("Um classificador que sempre devolve alguma categoria e perigoso. "
          "Um que separa o que nao sabe e utilizavel.")
    return res


# --------------------------------------------------------------------------
# 3. Question-answering extrativo sobre o FAQ
# --------------------------------------------------------------------------

PERGUNTAS_FAQ = [
    "Qual o prazo de troca por arrependimento?",
    "Quanto tempo dura a garantia?",
    "A garantia cobre turno duplo?",
    "O que preciso enviar para solicitar troca?",
    "Em quanto tempo chega a nota fiscal?",
    "O manual tem versao em portugues?",
    "Qual o prazo de entrega para o Nordeste?",
    "Qual a validade de um orcamento?",
    # As duas ultimas NAO estao no FAQ - e o que o exercicio quer observar
    "Qual a cor disponivel do VX-200?",
    "Voces tem loja fisica em Manaus?",
]


def faq():
    from transformers import pipeline

    caminho = DADOS / "faq" / "politicas.md"
    contexto = caminho.read_text(encoding="utf-8")
    qa = pipeline("question-answering", model=MODELO_QA)

    print(f"{'Pergunta':<45} {'Score':>6}  Resposta")
    print("-" * 100)
    for pergunta in PERGUNTAS_FAQ:
        t0 = time.perf_counter()
        r = qa(question=pergunta, context=contexto)
        ms = (time.perf_counter() - t0) * 1000
        resposta = r["answer"][:45].replace("\n", " ")
        print(f"{pergunta[:44]:<45} {r['score']:>6.3f}  {resposta} "
              f"({ms:.0f} ms)")

    print("\nAs duas ultimas perguntas nao tem resposta no FAQ. O QA extrativo "
          "nao inventa - ele devolve score baixo. Esse e o corte que decide "
          "quando escalar para o LLM.")


# --------------------------------------------------------------------------
# 4. Chat conversacional direto no transformers
# --------------------------------------------------------------------------

def chat(turnos: int = 3):
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(MODELO_CHAT)
    modelo = AutoModelForCausalLM.from_pretrained(MODELO_CHAT)

    historico = [{"role": "system",
                  "content": "Voce e um atendente cordial e objetivo. "
                             "Responda em portugues, em no maximo tres frases."}]

    def conversar(mensagem: str, recortar: bool = True) -> str:
        historico.append({"role": "user", "content": mensagem})
        entrada = tok.apply_chat_template(historico,
                                          add_generation_prompt=True,
                                          return_tensors="pt")
        saida = modelo.generate(entrada, max_new_tokens=180, do_sample=True,
                                temperature=0.7,
                                pad_token_id=tok.eos_token_id)
        # generate devolve o PROMPT + a continuacao. Sem o recorte, o chatbot
        # repete a pergunta inteira antes de responder.
        bruto = saida[0][entrada.shape[-1]:] if recortar else saida[0]
        resposta = tok.decode(bruto, skip_special_tokens=True).strip()
        historico.append({"role": "assistant", "content": resposta})
        return resposta

    perguntas = ["Bom dia, qual o prazo de garantia?",
                 "E se eu usar em turno duplo?",
                 "Obrigado. Como solicito a segunda via da nota?"]

    for pergunta in perguntas[:turnos]:
        print(f"\n> {pergunta}")
        print(conversar(pergunta))

    print(f"\nO historico tem {len(historico)} mensagens e cresce a cada "
          "turno. E literalmente a memoria de curto prazo do dia 3 - a mesma "
          "coisa que o checkpointer automatiza.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Pipelines aplicados do dia 5")
    p.add_argument("tarefa",
                   choices=["sentimento", "categorias", "faq", "chat"])
    p.add_argument("--corte", type=float, default=0.5)
    args = p.parse_args()

    {"sentimento": lambda: sentimento(),
     "categorias": lambda: categorias(args.corte),
     "faq": faq,
     "chat": chat}[args.tarefa]()
