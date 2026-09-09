"""Politicas de PreToolUse e steering: testados SEM LLM e SEM rede.

Este arquivo e o argumento do dia 3 em forma executavel: constraint e steering sao
codigo, e codigo se testa. A regra escrita no prompt nao tem teste possivel.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "dia3"))

import pytest
from hooks import (MAX_BUSCAS_POR_EXECUCAO, avaliar_politicas, executar_com_hooks,
                   limitar_buscas, limitar_tamanho_do_relatorio,
                   proteger_escrita_fora_da_saida, proteger_leitura_fora_de_docs,
                   recusar_comando_destrutivo)


# ------------------------------------------------------------ politicas


def test_escrita_dentro_da_saida_e_permitida():
    assert proteger_escrita_fora_da_saida(
        "salvar_relatorio", {"nome": "relatorio.md"}, None) is None


def test_escrita_fora_da_saida_e_negada():
    motivo = proteger_escrita_fora_da_saida(
        "salvar_relatorio", {"nome": "../../etc/passwd"}, None)
    assert motivo is not None


def test_recusa_explica_o_que_fazer():
    """Uma recusa bem escrita e uma instrucao: precisa dizer a alternativa."""
    motivo = proteger_escrita_fora_da_saida(
        "salvar_relatorio", {"nome": "/tmp/x.md"}, None)
    assert "saida" in motivo and "use" in motivo


def test_politica_ignora_ferramenta_que_nao_e_dela():
    assert proteger_escrita_fora_da_saida("calcular", {"expressao": "2+2"}, None) is None


def test_leitura_fora_de_docs_e_negada():
    assert proteger_leitura_fora_de_docs(
        "ler_arquivo", {"caminho": "../../etc/passwd"}, None) is not None


def test_limite_de_buscas_le_o_estado():
    estado_ok = {"buscas": MAX_BUSCAS_POR_EXECUCAO - 1}
    estado_estourado = {"buscas": MAX_BUSCAS_POR_EXECUCAO}
    assert limitar_buscas("buscar_web", {}, estado_ok) is None
    assert limitar_buscas("buscar_web", {}, estado_estourado) is not None


@pytest.mark.parametrize("cmd", ["rm -rf /", "dd if=/dev/zero of=/dev/sda", "shutdown -h now"])
def test_comando_destrutivo_e_bloqueado(cmd):
    assert recusar_comando_destrutivo("shell", {"comando": cmd}, None) is not None


def test_comando_inofensivo_passa():
    assert recusar_comando_destrutivo("shell", {"comando": "ls -la"}, None) is None


def test_relatorio_gigante_e_negado():
    assert limitar_tamanho_do_relatorio(
        "salvar_relatorio", {"conteudo": "x" * 100_000}, None) is not None


# ------------------------------------------------------------ execucao


class _FerramentaFalsa:
    def __init__(self, retorno=None, excecao=None):
        self.retorno, self.excecao, self.chamou = retorno, excecao, False

    def invoke(self, args):
        self.chamou = True
        if self.excecao:
            raise self.excecao
        return self.retorno


def test_execucao_permitida_chama_a_ferramenta():
    f = _FerramentaFalsa(retorno="ok")
    saida = executar_com_hooks({"salvar_relatorio": f},
                               "salvar_relatorio", {"nome": "r.md", "conteudo": "x"})
    assert saida == "ok" and f.chamou


def test_execucao_negada_nao_chama_a_ferramenta():
    """O ponto central: a ferramenta nem roda. Isso e constraint, nao aviso."""
    f = _FerramentaFalsa(retorno="ok")
    saida = executar_com_hooks({"salvar_relatorio": f},
                               "salvar_relatorio", {"nome": "../fora.md", "conteudo": "x"})
    assert saida.startswith("NEGADO") and not f.chamou


def test_ferramenta_inexistente_lista_as_validas():
    saida = executar_com_hooks({"calcular": _FerramentaFalsa("4")}, "calcula", {})
    assert "nao existe" in saida and "calcular" in saida


def test_excecao_da_ferramenta_nao_derruba_o_loop():
    f = _FerramentaFalsa(excecao=RuntimeError("banco fora do ar"))
    saida = executar_com_hooks({"buscar_documentos": f}, "buscar_documentos", {"consulta": "x"})
    assert saida.startswith("ERRO") and "RuntimeError" in saida


def test_avaliar_politicas_devolve_none_quando_tudo_permite():
    assert avaliar_politicas("calcular", {"expressao": "950 * 24"}, {}) is None
