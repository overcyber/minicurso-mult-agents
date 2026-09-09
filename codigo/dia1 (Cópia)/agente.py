"""O harness completo, em Python puro. Nenhum framework."""
import json
import sys
import time
 
from clientes import cliente
from ferramentas import ESPECIFICACOES, REGISTRO

SISTEMA = """Voce e um assistente que usa ferramentas para responder com precisao.

Regras:
- Use 'calcular' para QUALQUER conta. Nunca calcule de cabeca.
- Use 'ler_arquivo' antes de afirmar qualquer coisa sobre um documento.
- Cite o arquivo de onde tirou cada numero.
- Quando tiver a resposta, escreva-a de forma direta, sem repetir o processo.
"""


def rodar(pergunta: str, backend: str = "ollama", max_passos: int = 8,
          verbose: bool = True) -> str:
    c, modelo = cliente(backend)
    mensagens = [
        {"role": "system", "content": SISTEMA},
        {"role": "user", "content": pergunta},
    ]
    tokens = 0
    t0 = time.time()

    for passo in range(max_passos):
        resposta = c.chat.completions.create(
            model=modelo, messages=mensagens, tools=ESPECIFICACOES, temperature=0)
        if resposta.usage:
            tokens += resposta.usage.total_tokens
        msg = resposta.choices[0].message
        mensagens.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            if verbose:
                print(f"[passo {passo}] resposta final | {tokens} tokens | "
                      f"{time.time() - t0:.1f}s")
            return msg.content

        for chamada in msg.tool_calls:
            nome = chamada.function.name
            args = {}
            try:
                args = json.loads(chamada.function.arguments)
            except json.JSONDecodeError:
                resultado = "ERRO: os argumentos nao sao JSON valido."
            else:
                fn = REGISTRO.get(nome)
                if fn is None:
                    resultado = (f"ERRO: ferramenta '{nome}' nao existe. "
                                 f"Disponiveis: {list(REGISTRO)}")
                else:
                    try:
                        resultado = fn(**args)
                    except TypeError as e:
                        resultado = f"ERRO de argumentos: {e}"

            if verbose:
                print(f"[passo {passo}] {nome}({args}) -> {str(resultado)[:80]} "
                      f"| {tokens} tokens")

            mensagens.append({"role": "tool", "tool_call_id": chamada.id,
                              "content": str(resultado)})

    return "Limite de passos atingido sem resposta final."


if __name__ == "__main__":
    pergunta = sys.argv[1] if len(sys.argv) > 1 else "Quanto e 950 vezes 24?"
    #backend = sys.argv[2] if len(sys.argv) > 2 else "ollama"
    print("\n" + rodar(pergunta))
