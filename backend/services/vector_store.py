import re
import math
from collections import Counter
from pathlib import Path
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings

CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
VECTOR_SIZE = 1024


class LightweightEmbeddingFunction(EmbeddingFunction):
    """
    Embedding function basada en hashing trick + TF.
    No requiere onnxruntime ni modelos externos.
    """
    def name(self) -> str:
        return "lightweight_hash_tf"

    def __call__(self, input: Documents) -> Embeddings:
        result = []
        for doc in input:
            vec = [0.0] * VECTOR_SIZE
            tokens = re.findall(r'\b[a-z]{2,}\b', doc.lower())
            tf = Counter(tokens)
            total = len(tokens) or 1
            for term, count in tf.items():
                idx = hash(term) % VECTOR_SIZE
                vec[idx] += count / total
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            result.append([v / norm for v in vec])
        return result


_embedding_fn = None
_client = None


def _get_embedding_fn() -> LightweightEmbeddingFunction:
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = LightweightEmbeddingFunction()
    return _embedding_fn


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Divide el texto en trozos de chunk_size palabras con overlap de solapamiento."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def ingest_10k(ticker: str, text: str) -> int:
    """
    Guarda el texto del 10-K en ChromaDB.
    Cada empresa tiene su propia coleccion.
    Retorna la cantidad de chunks guardados.
    """
    collection = _get_client().get_or_create_collection(
        name=f"10k_{ticker.lower()}",
        embedding_function=_get_embedding_fn(),
    )

    if collection.count() > 0:
        return collection.count()

    chunks = chunk_text(text)

    collection.add(
        documents=chunks,
        ids=[f"{ticker}_{i}" for i in range(len(chunks))],
        metadatas=[{"ticker": ticker, "chunk_index": i} for i in range(len(chunks))],
    )

    return len(chunks)


def query_10k(ticker: str, question: str, n_results: int = 5) -> list[dict]:
    """
    Busca en ChromaDB los chunks mas relevantes para la pregunta dada.
    Retorna una lista de dicts con 'text' y 'chunk_index'.
    """
    collection = _get_client().get_or_create_collection(
        name=f"10k_{ticker.lower()}",
        embedding_function=_get_embedding_fn(),
    )

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    return [
        {"text": doc, "chunk_index": meta.get("chunk_index", i)}
        for i, (doc, meta) in enumerate(zip(docs, metas))
    ]
