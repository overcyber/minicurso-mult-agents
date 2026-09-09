---
title: Removedor de Fundo
emoji: 🖼️
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 5.9.1
app_file: app.py
pinned: false
license: mit
---

# Removedor de fundo

Demo do dia 5 do curso Sistemas Multi-Agente com Modelos Locais.

Um modelo de segmentacao (`rembg`) rodando no tier gratuito de CPU do Hugging Face
Spaces. Nenhuma chamada a API externa, nenhuma chave necessaria.

## O que este exemplo demonstra

A mecanica de trabalhar com o Hub e sempre a mesma, independente do dominio: escolher um
modelo por tarefa, ler o card, instalar, chamar e avaliar o resultado. Aqui isso foi
aplicado a visao computacional, que nao foi ensinada no curso - e funcionou.

## Estrutura

    app.py             a interface Gradio
    requirements.txt   dependencias que o Spaces instala no build
    README.md          este arquivo; o cabecalho YAML acima e a configuracao

## Rodando localmente

    pip install -r requirements.txt
    python app.py

## Publicando

    huggingface-cli login
    git init
    git remote add origin https://huggingface.co/spaces/SEU_USUARIO/removedor-de-fundo
    git add . && git commit -m "primeira versao"
    git push origin main

O build leva de tres a cinco minutos. Se o Space ficar preso em "Building", confira se o
`sdk_version` do cabecalho existe de verdade.

## Avisos

O tier gratuito e CPU com 16 GB de RAM. Serve confortavelmente para modelos pequenos como
este e **nao** serve para o NEXUS com um LLM de 4B - nao tente publicar o projeto do curso
aqui.

Qualquer chave de API vai em Settings -> Repository secrets, nunca no codigo. Um Space e
um repositorio Git publico, e um token comitado e um token vazado.
