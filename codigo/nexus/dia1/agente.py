"""Harness do agente, em Python puro. Nenhum framework."""

import argparse
import json
import time

from clientes import cliente
from ferramentas import ESPECIFICACOES, REGISTRO


SISTEMA = """
Voce e um assistente que usa ferramentas para responder com precisao.

REGRAS OBRIGATORIAS:

1. Use a ferramenta 'calcular' para QUALQUER conta.
   Nunca calcule de cabeca.

2. Use 'ler_arquivo' antes de afirmar qualquer coisa sobre um documento.

3. Quando o usuario informar um nome de arquivo, preserve esse nome.
   NUNCA invente, substitua ou escolha outro arquivo por conta propria.

4. Se o usuario pedir:
       leia estatuto.md
   voce deve chamar:
       ler_arquivo({"caminho": "estatuto.md"})

5. Se o arquivo solicitado nao existir, informe que ele nao existe.
   NUNCA leia outro arquivo como substituto.

6. Se houver varios arquivos disponiveis, isso NAO autoriza escolher um
   arquivo diferente daquele solicitado pelo usuario.

7. Cite explicitamente o nome do arquivo utilizado nas respostas sobre
   documentos.

8. Quando tiver a resposta final, responda diretamente, sem descrever
   raciocinio interno ou repetir desnecessariamente o processo.
""".strip()


def rodar(
    pergunta: str,
    backend: str = "ollama",
    max_passos: int = 8,
    verbose: bool = True,
) -> str:

    c, modelo = cliente(backend)

    mensagens = [
        {
            "role": "system",
            "content": SISTEMA,
        },
        {
            "role": "user",
            "content": pergunta,
        },
    ]

    tokens = 0
    t0 = time.time()

    for passo in range(max_passos):

        resposta = c.chat.completions.create(
            model=modelo,
            messages=mensagens,
            tools=ESPECIFICACOES,
            tool_choice="auto",
            temperature=0,
        )

        if resposta.usage:
            tokens += resposta.usage.total_tokens

        msg = resposta.choices[0].message

        # Adiciona a resposta do assistant ao histórico.
        mensagens.append(
            msg.model_dump(exclude_none=True)
        )

        # ---------------------------------------------------------
        # Nenhuma ferramenta solicitada -> resposta final
        # ---------------------------------------------------------

        if not msg.tool_calls:
            conteudo = msg.content or ""

            if verbose:
                print(
                    f"[passo {passo}] resposta final"
                    f" | {tokens} tokens"
                    f" | {time.time() - t0:.1f}s"
                )

            return conteudo

        # ---------------------------------------------------------
        # Executa todas as chamadas de ferramenta
        # ---------------------------------------------------------

        for chamada in msg.tool_calls:

            nome = chamada.function.name
            argumentos_brutos = chamada.function.arguments

            try:
                args = json.loads(argumentos_brutos)

                if not isinstance(args, dict):
                    raise ValueError(
                        "os argumentos da ferramenta precisam ser um objeto JSON"
                    )

            except (json.JSONDecodeError, ValueError) as e:
                args = {}
                resultado = f"ERRO: argumentos invalidos: {e}"

            else:
                fn = REGISTRO.get(nome)

                if fn is None:
                    resultado = (
                        f"ERRO: ferramenta '{nome}' nao existe. "
                        f"Disponiveis: {', '.join(REGISTRO.keys())}"
                    )

                else:
                    try:
                        resultado = fn(**args)

                    except TypeError as e:
                        resultado = (
                            f"ERRO de argumentos da ferramenta '{nome}': {e}"
                        )

                    except Exception as e:
                        resultado = (
                            f"ERRO ao executar ferramenta '{nome}': "
                            f"{type(e).__name__}: {e}"
                        )

            if verbose:
                preview = str(resultado).replace("\n", " ")[:120]

                print(
                    f"[passo {passo}] "
                    f"{nome}({args}) -> "
                    f"{preview}"
                    f" | {tokens} tokens"
                )

            mensagens.append(
                {
                    "role": "tool",
                    "tool_call_id": chamada.id,
                    "content": str(resultado),
                }
            )

    return (
        f"ERRO: limite de {max_passos} passos atingido "
        "sem uma resposta final."
    )


def main():
    parser = argparse.ArgumentParser(
        description="Agente do Dia 1"
    )

    parser.add_argument(
        "pergunta",
        nargs="*",
        help="Pergunta ou instrucao para o agente",
    )

    parser.add_argument(
        "--backend",
        default="ollama",
        help="Backend utilizado. Padrao: ollama",
    )

    parser.add_argument(
        "--max-passos",
        type=int,
        default=8,
        help="Numero maximo de iteracoes do agente",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Nao mostrar chamadas de ferramentas",
    )

    args = parser.parse_args()

    if args.pergunta:
        # FUNDAMENTAL:
        # junta TODOS os argumentos da linha de comando.
        pergunta = " ".join(args.pergunta)
    else:
        pergunta = "Quanto e 950 vezes 24?"

    resposta = rodar(
        pergunta=pergunta,
        backend=args.backend,
        max_passos=args.max_passos,
        verbose=not args.quiet,
    )

    print("\n" + resposta)


if __name__ == "__main__":
    main()















# """O harness completo, em Python puro. Nenhum framework."""
# import json
# import sys
# import time
 
# from clientes import cliente
# from ferramentas import ESPECIFICACOES, REGISTRO

# SISTEMA = """Voce e um assistente que usa ferramentas para responder com precisao.

# Regras:
# - Use 'calcular' para QUALQUER conta. Nunca calcule de cabeca.
# - Use 'ler_arquivo' antes de afirmar qualquer coisa sobre um documento.
# - Cite o arquivo de onde tirou cada numero.
# - Quando tiver a resposta, escreva-a de forma direta, sem repetir o processo.
# """


# def rodar(pergunta: str, backend: str = "ollama", max_passos: int = 8,
#           verbose: bool = True) -> str:
#     c, modelo = cliente(backend)
#     mensagens = [
#         {"role": "system", "content": SISTEMA},
#         {"role": "user", "content": pergunta},
#     ]
#     tokens = 0
#     t0 = time.time()

#     for passo in range(max_passos):
#         resposta = c.chat.completions.create(
#             model=modelo, messages=mensagens, tools=ESPECIFICACOES, temperature=0)
#         if resposta.usage:
#             tokens += resposta.usage.total_tokens
#         msg = resposta.choices[0].message
#         mensagens.append(msg.model_dump(exclude_none=True))

#         if not msg.tool_calls:
#             if verbose:
#                 print(f"[passo {passo}] resposta final | {tokens} tokens | "
#                       f"{time.time() - t0:.1f}s")
#             return msg.content

#         for chamada in msg.tool_calls:
#             nome = chamada.function.name
#             args = {}
#             try:
#                 args = json.loads(chamada.function.arguments)
#             except json.JSONDecodeError:
#                 resultado = "ERRO: os argumentos nao sao JSON valido."
#             else:
#                 fn = REGISTRO.get(nome)
#                 if fn is None:
#                     resultado = (f"ERRO: ferramenta '{nome}' nao existe. "
#                                  f"Disponiveis: {list(REGISTRO)}")
#                 else:
#                     try:
#                         resultado = fn(**args)
#                     except TypeError as e:
#                         resultado = f"ERRO de argumentos: {e}"

#             if verbose:
#                 print(f"[passo {passo}] {nome}({args}) -> {str(resultado)[:80]} "
#                       f"| {tokens} tokens")

#             mensagens.append({"role": "tool", "tool_call_id": chamada.id,
#                               "content": str(resultado)})

#     return "Limite de passos atingido sem resposta final."


# if __name__ == "__main__":
#     pergunta = sys.argv[1] if len(sys.argv) > 1 else "Quanto e 950 vezes 24?"
#     #backend = sys.argv[2] if len(sys.argv) > 2 else "ollama"
#     print("\n" + rodar(pergunta))
