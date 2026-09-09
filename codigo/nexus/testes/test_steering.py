"""Steering: detectores e no de correcao, testados sem LLM."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "dia3"))

from langchain_core.messages import AIMessage, ToolMessage
from steering import (MAX_ORIENTACOES, detectar_estagnacao, detectar_repeticao,
                      no_steering, precisa_de_steering)


def _obs(conteudo, nome="buscar_web", i=0):
    return ToolMessage(content=conteudo, name=nome, tool_call_id=f"c{i}")


def test_detecta_repeticao_de_observacao_identica():
    estado = {"messages": [_obs("nada encontrado", i=k) for k in range(3)]}
    assert detectar_repeticao(estado)


def test_nao_acusa_repeticao_quando_o_resultado_muda():
    estado = {"messages": [_obs(f"resultado {k}", i=k) for k in range(3)]}
    assert not detectar_repeticao(estado)


def test_nao_acusa_repeticao_com_poucas_chamadas():
    estado = {"messages": [_obs("nada", i=0), _obs("nada", i=1)]}
    assert not detectar_repeticao(estado)


def test_detecta_estagnacao():
    assert detectar_estagnacao({"passos": 7, "achados": []})
    assert not detectar_estagnacao({"passos": 7, "achados": ["algo"]})
    assert not detectar_estagnacao({"passos": 2, "achados": []})


def test_no_steering_injeta_orientacao_na_repeticao():
    estado = {"messages": [_obs("nada encontrado", i=k) for k in range(3)],
              "orientacoes": 0}
    delta = no_steering(estado)
    assert delta["orientacoes"] == 1
    assert "Nao repita" in delta["messages"][0].content


def test_no_steering_para_de_orientar_depois_do_limite():
    """Orientar para sempre e outra forma de loop infinito."""
    estado = {"messages": [_obs("nada", i=k) for k in range(3)],
              "orientacoes": MAX_ORIENTACOES}
    assert no_steering(estado) == {}


def test_no_steering_nao_faz_nada_quando_esta_tudo_bem():
    estado = {"messages": [AIMessage(content="pronto")], "orientacoes": 0, "passos": 2}
    assert no_steering(estado) == {}


def test_roteador_desvia_so_quando_precisa():
    normal = {"messages": [AIMessage(content="ok")], "passos": 1, "orientacoes": 0}
    travado = {"messages": [_obs("nada", i=k) for k in range(3)],
               "passos": 4, "orientacoes": 0}
    assert precisa_de_steering(normal) == "agente"
    assert precisa_de_steering(travado) == "steering"
