"""Troca do embedding do RAG por um modelo do Hugging Face Hub, com rerank opcional."""
import pathlib
import shutil

from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE = pathlib.Path(__file__).resolve().parent.parent
PERSIST = str(BASE / ".chroma_hf")
MODELO_EMB = "intfloat/multilingual-e5-small"


def embeddings():
    return HuggingFaceEmbeddings(
        model_name=MODELO_EMB,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def indexar(recriar: bool = False):
    if recriar:
        shutil.rmtree(PERSIST, ignore_errors=True)
    emb = embeddings()
    if pathlib.Path(PERSIST).exists() and not recriar:
        return Chroma(persist_directory=PERSIST, embedding_function=emb)
    docs = DirectoryLoader(str(BASE / "docs"), glob="**/*.md", loader_cls=TextLoader,
                           loader_kwargs={"encoding": "utf-8"}).load()
    partes = RecursiveCharacterTextSplitter(
        chunk_size=800, chunk_overlap=120,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]).split_documents(docs)
    return Chroma.from_documents(partes, emb, persist_directory=PERSIST)


def busca_com_rerank(banco, consulta: str, k: int = 4, candidatos: int = 20):
    """Dois estagios: vetorial rapido (recall) + cross-encoder preciso (precisao)."""
    from sentence_transformers import CrossEncoder
    reranker = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    brutos = banco.similarity_search(consulta, k=candidatos)
    notas = reranker.predict([(consulta, d.page_content) for d in brutos])
    return [d for _, d in sorted(zip(notas, brutos), key=lambda x: -x[0])[:k]]


if __name__ == "__main__":
    banco = indexar(recriar=True)
    for d in busca_com_rerank(banco, "custo total das embalagens em 24 meses"):
        print("---", d.metadata.get("source"))
        print(d.page_content[:200])
