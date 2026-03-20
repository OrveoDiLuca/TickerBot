import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from pathlib import Path

# Carpeta donde ChromaDB guarda sus datos en disco
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Modelo de embeddings (se descarga automaticamente la primera vez)
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Cliente persistente: los datos sobreviven entre reinicios
client = chromadb.PersistentClient(path=str(CHROMA_DIR))


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
    collection = client.get_or_create_collection(
        name=f"10k_{ticker.lower()}",
        embedding_function=embedding_fn,
    )

    # Si ya tiene documentos, no volvemos a ingestar
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
    collection = client.get_or_create_collection(
        name=f"10k_{ticker.lower()}",
        embedding_function=embedding_fn,
    )

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    return [{"text": doc, "chunk_index": meta.get("chunk_index", i)} for i, (doc, meta) in enumerate(zip(docs, metas))]
