from langchain_chroma import Chroma

from app.chatbot.config import RAG_DIR
from app.chatbot.rag.embeddings import get_embeddings

_vector_store = None


def get_vector_store():
    global _vector_store

    if _vector_store is None:
        RAG_DIR.mkdir(parents=True, exist_ok=True)

        _vector_store = Chroma(
            collection_name="meeting_transcripts",
            embedding_function=get_embeddings(),
            persist_directory=str(RAG_DIR),
        )

    return _vector_store