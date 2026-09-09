"""O comparador do conjunto de avaliacao, testado sem LLM.

Se o comparador estiver errado, toda a tabela do projeto final esta errada.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "dia5"))

import pytest
from avaliacao import carregar_casos, confere, resumir, rodar


# ------------------------------------------------------------ comparador


@pytest.mark.parametrize("resposta,esperado", [
    ("O faturamento foi de R$ 5.640.000,00 em 2024.", "5.640.000"),
    ("A media dos dois anos e R$ 5.230.000,00.", "5.230.000"),
    ("Foram 261 cooperados ao fim do ano.", "261"),
    ("O mais barato e a Verde Embalagens Ltda.", "Verde Embalagens"),
])
def test_acerta_quando_o_valor_aparece(resposta, esperado):
    assert confere(resposta, esperado)


@pytest.mark.parametrize("resposta,esperado", [
    ("A media e R$ 4.000.000,00.", "5.230.000"),
    ("Foram 238 cooperados.", "261"),
    ("", "5.640.000"),
])
def test_erra_quando_o_valor_nao_bate(resposta, esperado):
    assert not confere(resposta, esperado)


def test_tolera_formatacao_diferente_do_numero():
    assert confere("faturamento de 5640000 reais", "5.640.000")


@pytest.mark.parametrize("resposta", [
    "Nao encontrei essa informacao nos documentos disponiveis.",
    "Nao consta nos relatorios da cooperativa.",
    "Nao foi possivel apurar: o periodo esta fora dos documentos.",
])
def test_recusa_e_considerada_acerto_quando_esperada(resposta):
    assert confere(resposta, "RECUSAR")


@pytest.mark.parametrize("resposta", [
    "O faturamento de 2030 foi de R$ 9.000.000,00.",
    "O presidente e Joao da Silva.",
])
def test_inventar_quando_deveria_recusar_e_erro(resposta):
    """O caso mais importante do conjunto: um sistema que nunca recusa nao e confiavel."""
    assert not confere(resposta, "RECUSAR")


# ------------------------------------------------------------ conjunto


def test_conjunto_tem_dez_casos_e_pelo_menos_duas_recusas():
    casos = carregar_casos(RAIZ / "avaliacao" / "casos.jsonl")
    assert len(casos) == 10
    recusas = [c for c in casos if c["esperado"].strip().upper() == "RECUSAR"]
    assert len(recusas) >= 2


def test_todo_caso_com_gabarito_aponta_a_fonte():
    casos = carregar_casos(RAIZ / "avaliacao" / "casos.jsonl")
    for c in casos:
        if c["esperado"].strip().upper() != "RECUSAR":
            assert c["fonte"], f"caso {c['id']} sem fonte declarada"


# ------------------------------------------------------------ runner


def test_rodar_registra_erro_sem_derrubar_a_bateria():
    def nexus_quebrado(pergunta):
        raise RuntimeError("modelo fora do ar")

    casos = [{"id": "q1", "pergunta": "x", "esperado": "1", "fonte": ""}]
    linhas = rodar(nexus_quebrado, casos)
    assert linhas[0]["erro"] and not linhas[0]["acertou"]


def test_resumo_conta_certo():
    def nexus_falso(pergunta):
        return "R$ 5.640.000,00", ["2024_relatorio.md"], 1200

    casos = [
        {"id": "q1", "pergunta": "x", "esperado": "5.640.000", "fonte": "2024_relatorio.md"},
        {"id": "q2", "pergunta": "y", "esperado": "999", "fonte": "outro.md"},
    ]
    r = resumir(rodar(nexus_falso, casos))
    assert r["casos"] == 2 and r["acertos"] == 1 and r["fontes_ok"] == 1
