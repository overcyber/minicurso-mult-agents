"""Toda logica de roteamento deve ser testavel sem modelo."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "dia4"))

from langgraph.graph import END


def rotear_supervisor(estado, max_rodadas=3):
    if estado.get("rodadas", 0) >= max_rodadas:
        return END
    return END if estado["proximo"] == "FIM" else estado["proximo"]


def rotear_critico(estado, max_rodadas=3):
    if estado["veredito"] == "aprovado" or estado.get("rodadas", 0) >= max_rodadas:
        return END
    return "supervisor"


def test_supervisor_encaminha():
    assert rotear_supervisor({"proximo": "analista", "rodadas": 0}) == "analista"


def test_supervisor_termina_no_fim():
    assert rotear_supervisor({"proximo": "FIM", "rodadas": 0}) == END


def test_supervisor_corta_no_limite():
    assert rotear_supervisor({"proximo": "analista", "rodadas": 3}) == END


def test_critico_aprovado_termina():
    assert rotear_critico({"veredito": "aprovado", "rodadas": 1}) == END


def test_critico_reprovado_volta():
    assert rotear_critico({"veredito": "revisar", "rodadas": 1}) == "supervisor"


def test_critico_nao_cicla_para_sempre():
    assert rotear_critico({"veredito": "revisar", "rodadas": 3}) == END
