
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.chatbot.tools.meeting_tools import get_all_meeting_documents
from app.chatbot.rag.vector_store import get_vector_store


def index_meetings() -> dict:
    rows = get_all_meeting_documents()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
    )

    documents = []
    ids = []

    for row in rows:
        meeting_id = str(row.get("id", "unknown"))
        filename = row.get("file_name") or "Meeting"

        content = (
            f"Meeting: {filename}\n"
            f"Summary: {row.get('summary') or ''}\n"
            f"Transcript: {row.get('transcript') or ''}"
        ).strip()

        if not content:
            continue

        chunks = splitter.split_text(content)

        for index, chunk in enumerate(chunks):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "meeting_id": meeting_id,
                        "source": filename,
                        "chunk": index,
                    },
                )
            )

            ids.append(f"meeting-{meeting_id}-chunk-{index}")

    if not documents:
        return {
            "indexed_meetings": 0,
            "indexed_chunks": 0,
            "message": "No meeting transcripts were available.",
        }

    store = get_vector_store()

    # Delete older chunks for meetings that are being re-indexed.
    for row in rows:
        meeting_id = str(row.get("id", "unknown"))
        store.delete(
            where={"meeting_id": meeting_id}
        )

    store.add_documents(
        documents=documents,
        ids=ids,
    )

    return {
        "indexed_meetings": len(rows),
        "indexed_chunks": len(documents),
        "message": "Meeting transcripts indexed successfully.",
    }
