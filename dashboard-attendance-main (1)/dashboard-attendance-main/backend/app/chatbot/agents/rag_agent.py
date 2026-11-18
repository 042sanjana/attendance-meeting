
from app.chatbot.rag.retriever import search_meetings


def run_rag_agent(question: str) -> str:
    documents = search_meetings(question)

    if not documents:
        return "No matching meeting transcript passages were found."

    parts = []

    for doc in documents:
        parts.append(
            f"Source: {doc.metadata.get('source', 'Meeting')}\n"
            f"Meeting ID: {doc.metadata.get('meeting_id', 'Unknown')}\n"
            f"Content: {doc.page_content}"
        )

    return "\n\n".join(parts)
