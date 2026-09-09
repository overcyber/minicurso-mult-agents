"""Ferramentas do dia 1: funcoes Python puras + schemas JSON."""

import ast
import operator
import pathlib


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}


RAIZ = (
    pathlib.Path(__file__).resolve().parent.parent / "docs"
).resolve()


def _avaliar(no):

    if (
        isinstance(no, ast.Constant)
        and isinstance(no.value, (int, float))
        and not isinstance(no.value, bool)
    ):
        return no.value

    if isinstance(no, ast.BinOp):
        tipo_operador = type(no.op)

        if tipo_operador not in _OPS:
            raise ValueError("operador nao permitido")

        return _OPS[tipo_operador](
            _avaliar(no.left),
            _avaliar(no.right),
        )

    if isinstance(no, ast.UnaryOp):
        tipo_operador = type(no.op)

        if tipo_operador not in _OPS:
            raise ValueError("operador nao permitido")

        return _OPS[tipo_operador](
            _avaliar(no.operand)
        )

    raise ValueError("expressao nao permitida")


def calcular(expressao: str) -> str:
    """
    Avalia uma expressao aritmetica.

    Exemplo:
        950 * 24
    """

    try:
        arvore = ast.parse(
            expressao,
            mode="eval",
        )

        resultado = _avaliar(arvore.body)

        return str(resultado)

    except Exception as e:
        return (
            f"ERRO: {e}. "
            "Envie apenas numeros e os operadores "
            "+ - * / ** % //."
        )


def _caminho_seguro(caminho: str) -> pathlib.Path:
    """
    Resolve um caminho garantindo que continue dentro de docs/.
    """

    alvo = (RAIZ / caminho).resolve()

    try:
        alvo.relative_to(RAIZ)
    except ValueError:
        raise ValueError(
            "caminho fora da pasta permitida"
        )

    return alvo


def listar_arquivos() -> str:
    """
    Lista os arquivos existentes dentro de docs/.
    """

    if not RAIZ.exists():
        return (
            f"ERRO: diretorio docs nao existe: {RAIZ}"
        )

    arquivos = sorted(
        p.name
        for p in RAIZ.iterdir()
        if p.is_file()
    )

    if not arquivos:
        return "Nenhum arquivo encontrado em docs/."

    return "\n".join(arquivos)


def ler_arquivo(caminho: str) -> str:
    """
    Le um arquivo de texto localizado dentro de docs/.
    """

    if not caminho or not caminho.strip():
        return "ERRO: nome do arquivo vazio."

    caminho = caminho.strip()

    try:
        alvo = _caminho_seguro(caminho)

    except ValueError:
        return (
            "ERRO: caminho fora da pasta permitida. "
            "Use apenas arquivos existentes em docs/."
        )

    if not alvo.exists():
        disponiveis = listar_arquivos()

        return (
            f"ERRO: o arquivo '{caminho}' nao existe.\n\n"
            f"Arquivos disponiveis:\n{disponiveis}"
        )

    if not alvo.is_file():
        return (
            f"ERRO: '{caminho}' nao e um arquivo."
        )

    try:
        conteudo = alvo.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError:
        return (
            f"ERRO: '{caminho}' nao e um arquivo "
            "de texto UTF-8 valido."
        )

    except OSError as e:
        return (
            f"ERRO ao ler '{caminho}': {e}"
        )

    return conteudo


REGISTRO = {
    "calcular": calcular,
    "ler_arquivo": ler_arquivo,
    "listar_arquivos": listar_arquivos,
}


ESPECIFICACOES = [
    {
        "type": "function",
        "function": {
            "name": "calcular",
            "description": (
                "Avalia uma expressao aritmetica e devolve "
                "o resultado. Use SEMPRE que houver uma conta."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expressao": {
                        "type": "string",
                        "description": (
                            "Expressao aritmetica. "
                            "Exemplo: '950 * 24'"
                        ),
                    },
                },
                "required": ["expressao"],
                "additionalProperties": False,
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "ler_arquivo",
            "description": (
                "Le um arquivo especifico da pasta docs/. "
                "O parametro caminho deve corresponder ao arquivo "
                "pedido pelo usuario. Nunca substitua o arquivo "
                "solicitado por outro."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "caminho": {
                        "type": "string",
                        "description": (
                            "Nome EXATO do arquivo solicitado. "
                            "Exemplo: 'estatuto.md'"
                        ),
                    },
                },
                "required": ["caminho"],
                "additionalProperties": False,
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "listar_arquivos",
            "description": (
                "Lista os arquivos existentes na pasta docs/. "
                "Use quando o usuario perguntar quais documentos "
                "estao disponiveis ou quando precisar verificar nomes."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
]



















# """Ferramentas do dia 1: funcoes Python puras + schemas JSON escritos a mao."""
# import ast
# import operator
# import pathlib
 
# _OPS = {
#     ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
#     ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
#     ast.Mod: operator.mod, ast.FloorDiv: operator.floordiv,
# }

# RAIZ = (pathlib.Path(__file__).resolve().parent.parent / "docs").resolve()


# def _avaliar(no):
#     if isinstance(no, ast.Constant) and isinstance(no.value, (int, float)):
#         return no.value
#     if isinstance(no, ast.BinOp):
#         return _OPS[type(no.op)](_avaliar(no.left), _avaliar(no.right))
#     if isinstance(no, ast.UnaryOp):
#         return _OPS[type(no.op)](_avaliar(no.operand))
#     raise ValueError("expressao nao permitida")


# def calcular(expressao: str) -> str:
#     """Avalia uma expressao aritmetica. Ex: '950 * 24'."""
#     try:
#         return str(_avaliar(ast.parse(expressao, mode="eval").body))
#     except Exception as e:
#         return (f"ERRO: {e}. Envie apenas numeros e os operadores + - * / ** % //, "
#                 f"sem letras nem separador de milhar.")


# def ler_arquivo(caminho: str) -> str:
#     """Le um arquivo de texto dentro da pasta docs/."""
#     alvo = (RAIZ / caminho).resolve()
#     if not str(alvo).startswith(str(RAIZ)):
#         return "ERRO: caminho fora da pasta permitida. Use apenas o nome do arquivo."
#     if not alvo.exists():
#         disponiveis = ", ".join(sorted(p.name for p in RAIZ.glob("*")))
#         return f"ERRO: '{caminho}' nao existe. Disponiveis: {disponiveis}"
#     return alvo.read_text(encoding="utf-8")[:4000]


# REGISTRO = {"calcular": calcular, "ler_arquivo": ler_arquivo}

# ESPECIFICACOES = [
#     {
#         "type": "function",
#         "function": {
#             "name": "calcular",
#             "description": ("Avalia uma expressao aritmetica e devolve o resultado exato. "
#                             "Use SEMPRE que houver conta, mesmo simples."),
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "expressao": {"type": "string",
#                                   "description": "Expressao aritmetica, ex: '950 * 24'"},
#                 },
#                 "required": ["expressao"],
#             },
#         },
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "ler_arquivo",
#             "description": ("Le o conteudo completo de um arquivo de texto da pasta docs/. "
#                             "Use antes de afirmar qualquer coisa sobre um documento."),
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "caminho": {"type": "string",
#                                 "description": "Nome do arquivo, ex: '2024_relatorio.md'"},
#                 },
#                 "required": ["caminho"],
#             },
#         },
#     },
# ]
