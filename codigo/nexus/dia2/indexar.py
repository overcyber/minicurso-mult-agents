"""Cria (ou recria) o indice vetorial da pasta docs/."""
import pathlib
import shutil

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE = pathlib.Path(__file__).resolve().parent.parent
PERSIST = str(BASE / ".chroma")


def construir(recriar: bool = False):
    if recriar:
        shutil.rmtree(PERSIST, ignore_errors=True)
    emb = OllamaEmbeddings(model="nomic-embed-text")
    if pathlib.Path(PERSIST).exists() and not recriar:
        return Chroma(persist_directory=PERSIST, embedding_function=emb)

    docs = DirectoryLoader(str(BASE / "docs"), glob="**/*.md",
                           loader_cls=TextLoader,
                           loader_kwargs={"encoding": "utf-8"}).load()
    partes = RecursiveCharacterTextSplitter(
        chunk_size=800, chunk_overlap=120,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    ).split_documents(docs)
    print(f"{len(docs)} documentos -> {len(partes)} trechos")
    return Chroma.from_documents(partes, emb, persist_directory=PERSIST)


if __name__ == "__main__":
    import sys
    banco = construir(recriar="--recriar" in sys.argv)
    for d in banco.similarity_search("faturamento de 2024", k=2):
        print("---", d.metadata.get("source"))
        print(d.page_content[:200])
