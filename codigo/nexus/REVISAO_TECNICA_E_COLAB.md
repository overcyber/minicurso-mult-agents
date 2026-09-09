# Revisão técnica — NEXUS / minicurso-mult-agents

Data da revisão: 2026-09-08  
Repositório: `overcyber/minicurso-mult-agents`  
Artefato analisado: `codigo/nexus/` e `codigo/nexus.7z`

## 1. Integridade do arquivo recebido

O `nexus.7z` recebido possui 43.484 bytes e Git blob SHA:

`03466246f2cb52c39c3cba8bf815625c40da22e0`

Esse valor coincide com o blob de `codigo/nexus.7z` no GitHub. Portanto, o arquivo recebido e o arquivo publicado no repositório são a mesma versão.

O arquivo 7z contém também:

- uma pasta duplicada `dia1 (Cópia)/`;
- `__pycache__/` e arquivos `.pyc`;
- uma cópia antiga do código do Dia 1.

A árvore extraída e versionada em `codigo/nexus/` está mais limpa que o 7z. Recomenda-se regenerar o arquivo compactado a partir da árvore limpa.

## 2. Escopo estático

Foram analisados 30 arquivos Python relevantes, aproximadamente 3.157 linhas físicas contando testes e blocos legados comentados.

A compilação sintática de todos os arquivos Python passou.

O projeto possui:

- 43 funções `test_*`;
- 55 casos pytest após parametrização;
- 17 casos de avaliação;
- 16 casos de hooks/constraints;
- 8 casos de ferramentas;
- 6 casos de roteamento;
- 8 casos de steering.

No ambiente de revisão, os 33 casos que dependem apenas de bibliotecas já disponíveis e do código puro foram executados e passaram. A execução integral fica incorporada ao notebook Colab depois da instalação das dependências.

## 3. Avaliação por dia

### Dia 1 — avaliação: boa base didática

Pontos fortes:

1. O loop do agente é explícito e fácil de auditar.
2. O parser de argumentos de tool call exige JSON objeto.
3. Erros de ferramenta são convertidos em observações, preservando o loop.
4. A calculadora usa `ast.parse`, evitando `eval`.
5. O acesso a documentos usa `Path.relative_to`, que é a forma correta de validar confinamento por diretório.
6. O backend Ollama utiliza a API OpenAI-compatible em `/v1`.

Problemas:

- `agente.py` e `ferramentas.py` mantêm versões antigas enormes comentadas no final do arquivo.
- A operação `**` não possui limites de magnitude; uma expressão criada adversarialmente pode causar consumo excessivo de CPU/memória.
- `ler_arquivo` devolve o arquivo completo; em uma base maior deve haver limite de tamanho.

### Dia 2 — avaliação: evolução correta, com regressão de segurança

Pontos fortes:

- abstrações LangChain;
- tools declarativas;
- saída estruturada com Pydantic;
- RAG simples e compreensível;
- Chroma persistente;
- chunking explícito.

Problemas relevantes:

1. `ler_arquivo()` volta a validar confinamento com `str(path).startswith(str(RAIZ))`. Isso é menos seguro que `Path.relative_to()` do Dia 1 e admite colisões de prefixo em determinadas estruturas de caminho.
2. `.chroma` é reutilizado apenas pela existência do diretório. Não há fingerprint de documentos, modelo de embedding, parâmetros de chunking ou versão do schema.
3. `salvar_relatorio` é segura para nomes simples, mas a política de aprovação só aparece depois.
4. A dependência do Ollama/embedding não tem fallback nem diagnóstico no próprio módulo.

### Dia 3 — avaliação: bons conceitos, integração incompleta

Pontos fortes:

- grafo de estado explícito;
- checkpoint SQLite;
- mecanismo HITL;
- hooks determinísticos e testáveis;
- steering testável;
- busca web separada da base local;
- erros de ferramentas web são tratados.

Problemas críticos:

1. `hooks.py` não está integrado ao grafo principal de `nexus.py`.
2. `steering.py` não está integrado ao grafo principal.
3. O grafo usa `ToolNode` diretamente; logo constraints descritas no curso não protegem de fato as ferramentas desse grafo.
4. `SqliteSaver.from_conn_string(...).__enter__()` é invocado sem o correspondente fechamento do context manager.
5. `hooks.py` repete a validação de path por `startswith`.
6. `ler_pagina()` aceita qualquer HTTP(S) sem mitigação de SSRF, inclusive localhost, redes privadas, metadata de cloud e serviços internos.
7. Conteúdo recuperado da web entra no contexto sem uma camada explícita contra prompt injection indireta.

### Dia 4 — avaliação: arquitetura multiagente didática, mas com componentes demonstrativos desacoplados

Pontos fortes:

- separação supervisor/especialistas/crítico;
- isolamento do contexto de especialistas;
- outputs estruturados para supervisor e crítico;
- prompts por papel claros;
- interface Gradio separada do grafo;
- exemplo de interrupt/HITL no e-mail.

Problemas críticos/relevantes:

1. `handoff.py` não é usado pela equipe principal.
2. `memoria_semantica.py` usa `InMemoryStore`; não há persistência.
3. A tool `lembrar()` apenas retorna `"Anotado"` e não grava no store.
4. `email_assistente.processar()` chama `construir_grafo()` sem retriever; a rota FAQ padrão recebe base vazia.
5. `MAX_RODADAS` é incrementado no crítico, não em toda transição. Uma sequência ruim de supervisor/especialistas pode consumir transições sem aumentar esse contador.
6. O mesmo padrão de `SqliteSaver.__enter__()` sem fechamento reaparece.
7. `share=True` no Colab precisa ser opt-in; um link público pode expor documentos e capacidades do agente.

### Dia 5 — avaliação: maior lacuna entre módulos existentes e sistema final

Pontos positivos:

- demonstra seleção de modelo por papel;
- embeddings HF;
- reranking;
- classificação barata;
- pipelines especializados;
- avaliação com gabarito e casos de recusa;
- traces no CLI.

Problemas críticos:

1. `dia5/cli.py` continua usando diretamente `equipe.compilar()` do Dia 4.
2. `dia5/cli.py` não integra `modelos.py`.
3. `dia5/cli.py` não integra `embeddings_hf.py`.
4. `dia5/cli.py` não integra `roteador.py`.
5. `dia5/avaliacao.py` importa `responder` de `dia5/cli.py`, mas essa função não existe. O comando documentado de avaliação falha no código atual.
6. `embeddings_hf.py` fixa `device="cpu"`.
7. `pipelines.py` cria pipelines Transformers sem `device`.
8. `roteador.py` cria pipeline zero-shot sem `device`.
9. O chat Transformers não usa `device_map` nem move a entrada explicitamente para CUDA.
10. A métrica de tokens esperada pela avaliação não está conectada ao grafo multiagente.

O notebook Colab não oculta essas inconsistências. Ele configura CUDA para os exemplos Hugging Face, fornece um adapter explícito para a interface de avaliação, usa o grafo existente para smoke test e mantém os módulos originais visíveis para posterior refatoração.

## 4. Persistência e Colab

A adaptação usa diretamente no Google Drive:

- modelos Ollama via `OLLAMA_MODELS`;
- cache Hugging Face;
- clone persistente do GitHub.

E executa localmente em `/content`, com sincronização para o Drive:

- Chroma;
- SQLite;
- relatórios;
- traces;
- logs.

Essa separação evita transformar o Google Drive em filesystem transacional para bases SQLite/Chroma e ainda preserva o estado entre sessões.

## 5. Dependências

O `requirements.txt` usa apenas limites inferiores. Isso facilita instalação, mas prejudica reprodutibilidade.

A versão Colab usa constraints para o núcleo verificado em setembro de 2026:

- `langchain==1.4.0`
- `langgraph==1.2.11`
- `langgraph-checkpoint-sqlite==3.1.1`
- `langchain-ollama==1.1.0`
- `langchain-chroma==1.1.0`
- `chromadb==1.5.9`

O restante continua sendo resolvido a partir do `requirements.txt`.

## 6. `.gitignore`

O `.gitignore` atual cobre `__pycache__`, `.pyc`, `.venv`, `.env` e `chroma_db/`, mas não cobre explicitamente:

- `.chroma/`;
- `.chroma_hf/`;
- `*.db`;
- `*.db-wal`;
- `*.db-shm`;
- `saida/`;
- `tracos/`.

Recomenda-se incluir esses padrões para impedir commit acidental de estado gerado.

## 7. Priorização de correções

### P0 — funcional

1. criar `responder()` ou adaptar formalmente `dia5/avaliacao.py`;
2. decidir se o Dia 5 deve realmente integrar `modelos.py`, `embeddings_hf.py` e `roteador.py`;
3. ligar o retriever ao fluxo padrão de `email_assistente`.

### P1 — segurança/controle

1. substituir `startswith` de paths por `Path.relative_to`;
2. integrar hooks ao caminho real de execução das tools;
3. integrar steering ao grafo ou retirar a alegação de que está ativo;
4. adicionar proteção SSRF às ferramentas web;
5. adicionar política contra prompt injection indireta em conteúdo externo.

### P2 — robustez

1. gestão explícita do ciclo de vida do SQLite checkpointer;
2. fingerprint/versionamento do índice Chroma;
3. limite global de transições do multiagente;
4. telemetry de tokens por nó/modelo;
5. persistência real da memória semântica.

### P3 — manutenção

1. remover blocos antigos comentados;
2. regenerar o 7z sem `dia1 (Cópia)` e sem caches;
3. ampliar `.gitignore`;
4. adicionar constraints/lock de dependências;
5. adicionar testes de integração opcionais com Ollama.

## 8. Conclusão

O projeto é didaticamente bem estruturado do Dia 1 ao Dia 4, mas a maturidade de integração diminui nos Dias 3–5.

A principal distinção é:

```text
módulo implementado e testado isoladamente
não implica
módulo integrado ao fluxo executado pelo sistema
```

O Dia 1 está em melhor estado operacional. O Dia 2 é funcionalmente coerente, com pontos de segurança/persistência. O Dia 3 possui bons componentes de controle que ainda não governam o grafo principal. O Dia 4 demonstra bem multiagentes, mas contém componentes parcialmente ilustrativos. O Dia 5 precisa de refatoração de integração antes de ser considerado um pipeline final validado.

O notebook Colab foi construído para permitir essa validação de forma reproduzível, com GPU, persistência e separação por dia.
