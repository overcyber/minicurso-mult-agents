"""Ferramentas do dia 1: funcoes Python puras + schemas JSON escritos a mao."""
import ast
import operator
import pathlib
 
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
    ast.Mod: operator.mod, ast.FloorDiv: operator.floordiv,
}

RAIZ = (pathlib.Path(__file__).resolve().parent.parent / "docs").resolve()


def _avaliar(no):
    if isinstance(no, ast.Constant) and isinstance(no.value, (int, float)):
        return no.value
    if isinstance(no, ast.BinOp):
        return _OPS[type(no.op)](_avaliar(no.left), _avaliar(no.right))
    if isinstance(no, ast.UnaryOp):
        return _OPS[type(no.op)](_avaliar(no.operand))
    raise ValueError("expressao nao permitida")


def calcular(expressao: str) -> str:
    """Avalia uma expressao aritmetica. Ex: '950 * 24'."""
    try:
        return str(_avaliar(ast.parse(expressao, mode="eval").body))
    except Exception as e:
        return (f"ERRO: {e}. Envie apenas numeros e os operadores + - * / ** % //, "
                f"sem letras nem separador de milhar.")


def ler_arquivo(caminho: str) -> str:
    """Le um arquivo de texto dentro da pasta docs/."""
    alvo = (RAIZ / caminho).resolve()
    if not str(alvo).startswith(str(RAIZ)):
        return "ERRO: caminho fora da pasta permitida. Use apenas o nome do arquivo."
    if not alvo.exists():
        disponiveis = ", ".join(sorted(p.name for p in RAIZ.glob("*")))
        return f"ERRO: '{caminho}' nao existe. Disponiveis: {disponiveis}"
    return alvo.read_text(encoding="utf-8")[:4000]


REGISTRO = {"calcular": calcular, "ler_arquivo": ler_arquivo}

ESPECIFICACOES = [
    {
        "type": "function",
        "function": {
            "name": "calcular",
            "description": ("Avalia uma expressao aritmetica e devolve o resultado exato. "
                            "Use SEMPRE que houver conta, mesmo simples."),
            "parameters": {
                "type": "object",
                "properties": {
                    "expressao": {"type": "string",
                                  "description": "Expressao aritmetica, ex: '950 * 24'"},
                },
                "required": ["expressao"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ler_arquivo",
            "description": ("Le o conteudo completo de um arquivo de texto da pasta docs/. "
                            "Use antes de afirmar qualquer coisa sobre um documento."),
            "parameters": {
                "type": "object",
                "properties": {
                    "caminho": {"type": "string",
                                "description": "Nome do arquivo, ex: '2024_relatorio.md'"},
                },
                "required": ["caminho"],
            },
        },
    },
]
