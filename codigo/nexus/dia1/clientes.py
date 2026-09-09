"""Um cliente unico para tres backends locais compativeis com a API da OpenAI."""
import os

from openai import OpenAI 
# /usr/bin/python3 -m pip install --break-system-packages  openai
#ou Crie um env 
BACKENDS = {
    "ollama": dict(base_url="http://localhost:11434/v1", api_key="ollama",
                   model=os.getenv("MODELO", "qwen3:4b")),
    "llamacpp": dict(base_url="http://localhost:8080/v1", api_key="nao-usado",
                     model="local"),
    "vllm": dict(base_url=os.getenv("VLLM_URL", "http://localhost:8000/v1"),
                 api_key="nao-usado", model=os.getenv("VLLM_MODELO", "Qwen/Qwen3-8B")),
}


def cliente(nome: str = "ollama"):
    cfg = BACKENDS[nome]
    return OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"]), cfg["model"]


if __name__ == "__main__":
    import sys
    c, modelo = cliente(sys.argv[1] if len(sys.argv) > 1 else "ollama")
    r = c.chat.completions.create(
        model=modelo,
        messages=[{"role": "user", "content": "Responda em uma palavra: capital do Brasil?"}],
    )
    print(r.choices[0].message.content)
