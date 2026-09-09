# Construindo Sistemas Multiagente com Modelos Locais

Curso intensivo de 40 horas — cinco encontros de oito horas.
Stack: Ollama, llama.cpp, vLLM e Hugging Face Transformers, tudo local.
Projeto fio-condutor: NEXUS, uma agência de pesquisa que roda na própria máquina.

## O que tem neste pacote

```
entrega/
├── apostila.pdf              162 páginas: planejamento, cinco dias,
├── apostila.docx             exercícios, projeto final e dois anexos
├── slides/
│   ├── dia1_harness.pptx         82 slides
│   ├── dia2_langchain.pptx       76 slides (62 visíveis + Anexo A oculto)
│   ├── dia3_langgraph.pptx       63 slides
│   ├── dia4_multiagente.pptx     71 slides (57 visíveis + Anexo B oculto)
│   ├── dia5_huggingface.pptx     53 slides
│   └── *.pdf                     mesma coisa, para consulta rápida
└── codigo/
    └── codigo_nexus.zip      o NEXUS completo, dia 1 a dia 5, com testes
```

## Notas de apresentação

**Todo slide traz o roteiro do instrutor nas notas de apresentação.** Abra o PowerPoint no
modo Apresentador, ou vá em Exibir → Anotações. O formato é sempre o mesmo:

```
[N min]

DIGA — o argumento, com a razão por trás de cada item.
FAÇA — o que acontece ao vivo: comando, desenho no quadro, pergunta para a turma.
SE PERGUNTAREM '...' — a resposta pronta.
```

Aparecem também `DIGA TAMBÉM` (a ressalva honesta) e `NÃO FAÇA` (armadilha do instrutor).

As **divisórias de seção** trazem o plano do bloco: horário, o que ele entrega, o roteiro
com o tempo de cada slide, e o que cortar se o tempo apertar.

## Slides ocultos

Os decks dos dias 2 e 4 terminam com um anexo marcado como oculto no arquivo: Make e n8n
no dia 2, Copilot Studio e Power Automate no dia 4. Eles não aparecem na apresentação nem
na numeração, e continuam editáveis e imprimíveis. É material excedente, para quem
perguntar ou para uma turma com esse perfil.

Para exibi-los: clique com o botão direito no slide, em Classificação de Slides, e escolha
Ocultar Slide para desmarcar.

## Código

```bash
unzip codigo_nexus.zip && cd codigo/nexus
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama pull qwen3:4b && ollama pull nomic-embed-text
python check_ambiente.py
python -m pytest testes -q      # 55 testes, nenhum carrega modelo
```

Cada pasta `diaN/` é o estado do sistema ao fim daquele dia. O README do código detalha o
resto, incluindo as políticas de PreToolUse, o steering e o conjunto de avaliação.

## Compromisso do curso

Tudo roda local. Nenhuma parte obrigatória do curso precisa de chave de API paga.
