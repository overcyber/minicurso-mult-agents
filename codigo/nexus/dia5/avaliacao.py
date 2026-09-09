"""Conjunto de avaliacao: dez casos e a tabela que decide.

Observabilidade responde o que o pipeline FEZ (traco do dia 4).
Avaliacao responde se o que ele fez estava CERTO. E este modulo.

Nao precisa de framework nem de servico: e um arquivo JSONL e um loop. O que ele
compra e a diferenca entre "achei que melhorou" e "o acerto foi de 7 para 9, e
custou 1,4 s a mais por pergunta".

Uso:

    python3 dia5/avaliacao.py --casos avaliacao/casos.jsonl
    python3 dia5/avaliacao.py --casos avaliacao/casos.jsonl --rotulo com-rerank
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import time
import unicodedata

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PADRAO_CASOS = RAIZ / "avaliacao" / "casos.jsonl"
PADRAO_SAIDA = RAIZ / "saida"

RECUSA = "RECUSAR"


# ------------------------------------------------------------ normalizacao


def _normalizar(texto: str) -> str:
    """Minusculas, sem acento, sem pontuacao de milhar/moeda, espacos colapsados."""
    t = unicodedata.normalize("NFD", str(texto))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    t = t.replace("r$", " ").replace(".", "").replace(",", ".")
    t = re.sub(r"[^a-z0-9. ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


TERMOS_DE_RECUSA = [
    "nao encontrei", "nao consta", "nao ha informacao", "nao foi possivel",
    "nao sei", "nao tenho como", "nao esta nos documentos", "fora do periodo",
]


def confere(resposta: str, esperado: str) -> bool:
    """Compara resposta com o gabarito.

    Dois modos:
      - esperado == "RECUSAR": acerta quem admite nao saber.
      - caso contrario: acerta quem contem o valor esperado (numeros comparados
        numericamente, para tolerar formatacao diferente).
    """
    r = _normalizar(resposta)

    if esperado.strip().upper() == RECUSA:
        return any(t in r for t in TERMOS_DE_RECUSA)

    e = _normalizar(esperado)
    if e and e in r:
        return True

    # comparacao numerica: todo numero do gabarito precisa aparecer na resposta
    numeros_esperados = re.findall(r"\d+(?:\.\d+)?", e)
    if not numeros_esperados:
        return False
    numeros_resposta = {float(x) for x in re.findall(r"\d+(?:\.\d+)?", r)}
    return all(
        any(abs(float(n) - m) < max(0.01, abs(float(n)) * 0.001) for m in numeros_resposta)
        for n in numeros_esperados
    )


# ------------------------------------------------------------ execucao


def carregar_casos(caminho: pathlib.Path) -> list[dict]:
    casos = []
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#"):
            casos.append(json.loads(linha))
    return casos


def rodar(nexus, casos: list[dict]) -> list[dict]:
    """nexus(pergunta) -> (resposta: str, fontes: list[str], tokens: int)."""
    linhas = []
    for caso in casos:
        t0 = time.time()
        try:
            resposta, fontes, tokens = nexus(caso["pergunta"])
            erro = ""
        except Exception as e:
            resposta, fontes, tokens = "", [], 0
            erro = f"{type(e).__name__}: {e}"
        segundos = round(time.time() - t0, 1)

        esperadas = {f.strip() for f in caso.get("fonte", "").split(",") if f.strip()}
        linhas.append({
            "id": caso["id"],
            "acertou": bool(erro == "" and confere(resposta, caso["esperado"])),
            "citou_ok": bool(esperadas.issubset(set(fontes))) if esperadas else True,
            "tokens": tokens,
            "segundos": segundos,
            "erro": erro,
            "resposta": resposta[:300],
        })
    return linhas


def resumir(linhas: list[dict]) -> dict:
    n = len(linhas) or 1
    return {
        "casos": len(linhas),
        "acertos": sum(l["acertou"] for l in linhas),
        "fontes_ok": sum(l["citou_ok"] for l in linhas),
        "tokens_medio": round(sum(l["tokens"] for l in linhas) / n),
        "segundos_medio": round(sum(l["segundos"] for l in linhas) / n, 1),
        "erros": sum(1 for l in linhas if l["erro"]),
    }


def tabela(linhas: list[dict]) -> str:
    cab = f"{'id':<5} {'acertou':<8} {'fonte':<6} {'tokens':>7} {'seg':>6}  observacao"
    corpo = [cab, "-" * len(cab)]
    for l in linhas:
        obs = l["erro"] or ("" if l["acertou"] else l["resposta"][:60])
        corpo.append(f"{l['id']:<5} {str(l['acertou']):<8} {str(l['citou_ok']):<6} "
                     f"{l['tokens']:>7} {l['segundos']:>6}  {obs}")
    r = resumir(linhas)
    corpo.append("-" * len(cab))
    corpo.append(f"acertos {r['acertos']}/{r['casos']} | fontes {r['fontes_ok']}/{r['casos']} "
                 f"| tokens medio {r['tokens_medio']} | {r['segundos_medio']} s/pergunta "
                 f"| erros {r['erros']}")
    return "\n".join(corpo)


def main() -> None:
    ap = argparse.ArgumentParser(description="Roda o conjunto de avaliacao do NEXUS.")
    ap.add_argument("--casos", type=pathlib.Path, default=PADRAO_CASOS)
    ap.add_argument("--rotulo", default="base",
                    help="nome desta rodada, para comparar antes/depois")
    args = ap.parse_args()

    from cli import responder as nexus  # o entrypoint do seu NEXUS

    casos = carregar_casos(args.casos)
    linhas = rodar(nexus, casos)
    print(tabela(linhas))

    PADRAO_SAIDA.mkdir(parents=True, exist_ok=True)
    destino = PADRAO_SAIDA / f"avaliacao_{args.rotulo}.json"
    destino.write_text(json.dumps(
        {"rotulo": args.rotulo, "resumo": resumir(linhas), "linhas": linhas},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nresultado salvo em {destino}")


if __name__ == "__main__":
    main()
