# NEXUS — agência de pesquisa local

Projeto fio-condutor do curso *Construindo Sistemas Multiagente com Modelos Locais*.
Cada pasta `diaN/` é o estado do sistema ao final daquele dia.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3:4b
ollama pull nomic-embed-text
python check_ambiente.py
```

## Uso

```bash
python dia1/agente.py "Quanto custa o Fornecedor B em 24 meses?"
python dia2/indexar.py                       # cria o indice em .chroma
python dia3/cli.py "Qual foi o faturamento de 2024?" --thread ana
python dia3/ferramentas_web.py               # testa busca e leitura de pagina
python dia4/app_gradio.py                    # interface em http://127.0.0.1:7860
python dia4/memoria_semantica.py             # demonstra busca por significado
python dia4/email_assistente.py --automatico # triagem dos 10 e-mails de exemplo
python dia5/cli.py "Compare os fornecedores e recomende um." --saida rel.md
python dia5/pipelines.py sentimento          # tambem: categorias, faq, chat
python dia5/avaliacao.py --rotulo base       # roda os 10 casos e imprime a tabela
python -m pytest testes -q                   # 55 testes, sem LLM e sem rede
```

Na primeira vez que rodar `dia5/pipelines.py`, o `transformers` baixa os modelos do Hub
(entre 500 MB e 1,1 GB por tarefa). Depois disso tudo roda offline.

## Estrutura

```
nexus/
├── check_ambiente.py     diagnostico de instalacao
├── docs/                 base de documentos ficticia (Cooperativa Vale Verde)
├── dados/                avaliacoes.csv, emails.json e a base de FAQ
├── avaliacao/            casos.jsonl: dez perguntas com gabarito
├── saida/                nuvens de palavras, CSVs e relatorios gerados
├── dia1/                 harness em Python puro
├── dia2/                 ferramentas LangChain + RAG
├── dia3/                 grafo LangGraph com memoria, hooks e HITL
│   ├── ferramentas_web   busca (DDGS), leitura de pagina (BS4) e Selenium
│   ├── hooks             politicas de PreToolUse: constraints que NEGAM
│   └── steering          correcao em tempo de execucao (repeticao, estagnacao)
├── dia4/                 equipe multiagente
│   ├── memoria_semantica store com busca por significado
│   ├── app_gradio        interface sobre o mesmo grafo, sem mudar o grafo
│   └── email_assistente  triagem por intencao, FAQ com RAG e aprovacao humana
├── dia5/                 Hugging Face, modelos por papel, CLI
│   ├── pipelines         sentimento, zero-shot, question-answering, chat
│   ├── avaliacao         roda o conjunto de casos e imprime a tabela
│   └── space_demo/       demo de remocao de fundo pronta para o HF Spaces
└── testes/               pytest sem LLM (55 testes, nenhum carrega modelo)
```

## Avaliacao

O conjunto de casos vive em `avaliacao/casos.jsonl`: dez perguntas com gabarito, das quais
**duas exigem que o sistema recuse** (q9 e q10 pedem informacao que nao existe nos
documentos). Um sistema que nunca recusa nao e confiavel, e apenas confiante.

```bash
python dia5/avaliacao.py --rotulo sem-rerank
# ... ligue o rerank ...
python dia5/avaliacao.py --rotulo com-rerank
```

Cada rodada grava `saida/avaliacao_<rotulo>.json` com acerto, citacao de fonte, tokens e
tempo por caso. E a tabela que transforma "achei que melhorou" em numero.

## Constraints e steering

O dia 3 acrescenta duas pecas que sao codigo, e por isso sao testaveis:

- `dia3/hooks.py` — registro de politicas de `PreToolUse`. Devolver `None` permite;
  devolver uma string NEGA, e a string e o motivo que volta ao modelo. Uma recusa bem
  escrita e uma instrucao.
- `dia3/steering.py` — detecta repeticao e estagnacao e injeta orientacao **durante** a
  execucao, em vez de so abortar. Instrucao fala antes, constraint impede, steering
  corrige no meio.

Ambos sao funcoes puras e estao cobertos por `testes/test_hooks.py` e
`testes/test_steering.py`, que rodam em milissegundos sem carregar modelo nenhum.

## Dependencias opcionais

Nem tudo e necessario para o nucleo do curso:

| Pacote | Para que | Sem ele |
|---|---|---|
| `selenium` | paginas que so carregam com JavaScript | `ler_pagina` cobre a maioria dos casos |
| `wordcloud`, `matplotlib` | nuvens de palavras do dia 5 | o resto do `pipelines.py` roda igual |
| `ragas` | avaliacao automatica de RAG | comentado no requirements; instale se for fazer o exercicio |
| `langchain-tavily` | busca paga, feita para agentes | o `ddgs` cobre o laboratorio sem cadastro |

## Chaves de API

Nenhuma parte obrigatoria do curso precisa de chave. Se voce for usar OpenAI ou Tavily,
crie um `.env` na raiz:

```
OPENAI_API_KEY=...
TAVILY_API_KEY=...
```

E confirme que `.env` esta no `.gitignore` antes do primeiro commit.
