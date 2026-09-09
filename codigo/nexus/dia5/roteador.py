"""Roteamento hibrido: classificador local antes de gastar uma chamada de LLM."""
from functools import lru_cache

ROTULOS = {
    "buscar informacao em documentos": "pesquisador",
    "fazer calculo ou comparacao numerica": "analista",
    "escrever um texto ou relatorio": "redator",
}
LIMIAR = 0.75


@lru_cache(maxsize=1)
def _classificador():
    from transformers import pipeline
    return pipeline("zero-shot-classification",
                    model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")


def rotear_barato(pergunta: str):
    """Devolve (papel, confianca) ou (None, confianca) se nao houver certeza."""
    r = _classificador()(pergunta, candidate_labels=list(ROTULOS))
    rotulo, nota = r["labels"][0], float(r["scores"][0])
    return (ROTULOS[rotulo] if nota >= LIMIAR else None), nota


if __name__ == "__main__":
    for p in ["Qual foi o faturamento de 2024?",
              "Some os dois faturamentos e tire a media",
              "Escreva um relatorio comparando os fornecedores"]:
        print(rotear_barato(p), "|", p)
