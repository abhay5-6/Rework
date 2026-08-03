"""import requests

from app.core.config import (
    OLLAMA_GENERATE_URL,
    OLLAMA_TIMEOUT_SECONDS
)

from app.services.ai.context_builder import (
    build_workspace_context
)


async def generate_workspace_answer(
    db,
    workspace_id: int,
    query: str
):
    print("Generating workspace answer for workspace_id:", workspace_id, "with query:", query)

    context = await (
        build_workspace_context(
            db,
            workspace_id,
            query
        )
    )

    prompt = f
Workspace Context:
{context}

User Question:
{query}

Answer using the workspace context whenever relevant.


    response = requests.post(

        OLLAMA_GENERATE_URL,

        json={

            "model": "phi3",

            "prompt": prompt,

            "stream": False
        },
        timeout=OLLAMA_TIMEOUT_SECONDS
    )

    data = response.json()

    return data["response"]
    print("Workspace answer generated for workspace_id:", workspace_id, "with query:", query)
"""