"""Testes que rodam sem LLM e sem rede."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "dia2"))

import pytest
from ferramentas import calcular, ler_arquivo, listar_arquivos, salvar_relatorio


def test_calcular_ok():
    assert calcular.invoke({"expressao": "950 * 24"}) == str(950 * 24)


@pytest.mark.parametrize("expr", ["__import__('os').system('ls')", "abrir()", "2 +"])
def test_calcular_recusa_o_que_nao_e_aritmetica(expr):
    assert calcular.invoke({"expressao": expr}).startswith("ERRO")


def test_ler_arquivo_bloqueia_travessia():
    saida = ler_arquivo.invoke({"caminho": "../../etc/passwd"})
    assert saida.startswith("ERRO")


def test_ler_arquivo_inexistente_lista_alternativas():
    saida = ler_arquivo.invoke({"caminho": "nao_existe.md"})
    assert saida.startswith("ERRO") and "Disponiveis" in saida


def test_listar_arquivos():
    assert "2024_relatorio.md" in listar_arquivos.invoke({})


def test_salvar_recusa_caminho():
    assert salvar_relatorio.invoke(
        {"nome": "../fora.md", "conteudo": "x"}).startswith("ERRO")
