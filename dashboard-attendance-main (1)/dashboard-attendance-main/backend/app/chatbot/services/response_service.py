
def build_response(answer: str, evidence: dict):
    sources = []

    for module, result in evidence.items():
        if result:
            sources.append({
                "module": module,
                "description": (
                    f"Retrieved records from the {module} module."
                ),
            })

    return {
        "answer": answer,
        "sources": sources,
    }
