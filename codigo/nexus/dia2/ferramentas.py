"""Ferramentas do dia 2: declarativas, validadas e testaveis."""
import ast
import operator
import pathlib
from typing import Literal

from langchain.tools import tool
from pydantic import BaseModel, Field

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
    ast.Mod: operator.mod, ast.FloorDiv: operator.floordiv,
}

RAIZ = (pathlib.Path(__file__).resolve().parent.parent / "docs").resolve()
SAIDA = (pathlib.Path(__file__).resolve().parent.parent / "saida").resolve()


def _avaliar(no):
    if isinstance(no, ast.Constant) and isinstance(no.value, (int, float)):
        return no.value
    if isinstance(no, ast.BinOp):
        return _OPS[type(no.op)](_avaliar(no.left), _avaliar(no.right))
    if isinstance(no, ast.UnaryOp):
        return _OPS[type(no.op)](_avaliar(no.operand))
    raise ValueError("expressao nao permitida")


@tool
def calcular(expressao: str) -> str:
    """Avalia uma expressao aritmetica e devolve o resultado exato.

    Use SEMPRE que houver conta, mesmo simples. Nunca calcule de cabeca.

    Args:
        expressao: expressao aritmetica sem letras, ex: '950 * 24'
    """
    try:
        return str(_avaliar(ast.parse(expressao, mode="eval").body))
    except Exception as e:
        return (f"ERRO: {e}. Envie apenas numeros e os operadores + - * / ** % //, "
                f"sem separador de milhar.")


@tool
def listar_arquivos() -> str:
    """Lista os arquivos disponiveis na base local de documentos.

    Use quando nao souber qual documento consultar.
    """
    itens = sorted(RAIZ.glob("*"))
    if not itens:
        return "A pasta de documentos esta vazia."
    return "\n".join(f"- {p.name} ({p.stat().st_size} bytes)" for p in itens)


@tool
def ler_arquivo(caminho: str) -> str:
    """Le o conteudo completo de um arquivo da base local de documentos.

    Use quando precisar do texto inteiro; para trechos relevantes prefira
    'buscar_documentos'.

    Args:
        caminho: nome do arquivo, ex: '2024_relatorio.md'
    """
    alvo = (RAIZ / caminho).resolve()
    if not str(alvo).startswith(str(RAIZ)):
        return "ERRO: caminho fora da pasta permitida. Use apenas o nome do arquivo."
    if not alvo.exists():
        return (f"ERRO: '{caminho}' nao existe. "
                f"Disponiveis: {sorted(p.name for p in RAIZ.glob('*'))}")
    return alvo.read_text(encoding="utf-8")[:4000]


class BuscaArgs(BaseModel):
    consulta: str = Field(description="Pergunta ou termos em linguagem natural")
    k: int = Field(default=4, ge=1, le=8, description="Quantos trechos retornar")


def fazer_busca(banco):
    """Fabrica a ferramenta de busca amarrada a um banco vetorial ja criado."""

    @tool(args_schema=BuscaArgs)
    def buscar_documentos(consulta: str, k: int = 4) -> str:
        """Busca trechos relevantes na base local de documentos.

        Use antes de afirmar qualquer coisa sobre o conteudo dos documentos.
        """
        achados = banco.similarity_search(consulta, k=max(1, min(k, 8)))
        if not achados:
            return "Nenhum trecho relevante encontrado. Tente outros termos."
        return "\n\n---\n\n".join(
            f"[fonte: {pathlib.Path(d.metadata.get('source', '?')).name}]\n{d.page_content}"
            for d in achados)

    return buscar_documentos


@tool
def salvar_relatorio(nome: str, conteudo: str) -> str:
    """Salva um relatorio em Markdown na pasta de saida.

    Acao com efeito em disco: exige aprovacao humana.

    Args:
        nome: nome do arquivo, sem barras, ex: 'analise_fornecedores.md'
        conteudo: texto completo do relatorio em Markdown
    """
    if "/" in nome or "\\" in nome or nome.startswith("."):
        return "ERRO: use apenas um nome simples de arquivo, sem caminho."
    if not nome.endswith(".md"):
        nome += ".md"
    SAIDA.mkdir(exist_ok=True)
    (SAIDA / nome).write_text(conteudo, encoding="utf-8")
    return f"Salvo em saida/{nome} ({len(conteudo)} caracteres)."
