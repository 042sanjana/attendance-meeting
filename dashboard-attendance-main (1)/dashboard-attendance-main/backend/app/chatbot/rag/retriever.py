
from app.chatbot.rag.vector_store import get_vector_store


def search_meetings(question: str, k: int = 5):
    try:
        store = get_vector_store()

        return store.similarity_search(
            question,
            k=k,
        )

    except Exception:
        # An unbuilt or empty vector store is not a fatal
        # error for structured database questions.
        return []
