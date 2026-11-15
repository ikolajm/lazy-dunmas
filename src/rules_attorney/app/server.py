"""The endpoint: one question in, its run streamed out as server-sent events.

    python -m uvicorn rules_attorney.app.server:app

Serves on port 8000 once the corpus is embedded, against the live Ollama
server.
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path
from typing import Any

import ollama
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

from rules_attorney.answer import Ruling, chat_request
from rules_attorney.app.stream import Call, Calls, run
from rules_attorney.corpus import load_corpus
from rules_attorney.gate import Gate
from rules_attorney.multihop import Plan
from rules_attorney.retrieve import Embedder, embed_documents, ollama_embed

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "srd-5.1"
MODEL_VAR = "LAZY_DUNMAS_MODEL"
EMBED_MODEL_VAR = "LAZY_DUNMAS_EMBED_MODEL"
QUERY_PREFIX_VAR = "LAZY_DUNMAS_QUERY_PREFIX"
DOCUMENT_PREFIX_VAR = "LAZY_DUNMAS_DOCUMENT_PREFIX"

# Async, so a stop or the run's limit cancels the request in flight, which
# closes it and ends Ollama's generation with it.
client = ollama.AsyncClient()


def required(var: str) -> str:
    """A model name from the environment, refusing one that is unset or blank."""
    value = os.environ.get(var, "").strip()
    if not value:
        raise RuntimeError(
            f"Set {var} in .env to an Ollama model, as `ollama list` names it."
        )
    return value


def chat_model() -> str:
    """The chat model for the gate, the plan and the ruling."""
    return required(MODEL_VAR)


def embedder() -> Embedder:
    """The embedding model for the search, and the prefixes its card asks for."""
    return Embedder(
        model=required(EMBED_MODEL_VAR),
        query_prefix=os.environ.get(QUERY_PREFIX_VAR, ""),
        document_prefix=os.environ.get(DOCUMENT_PREFIX_VAR, ""),
    )


def served(schema: dict[str, Any], model: str) -> Call:
    """A model call through Ollama, held to the schema given."""

    async def call(prompt: str) -> str:
        try:
            response = await client.chat(**chat_request(prompt, model, schema))
        except ollama.ResponseError as error:
            # Ollama is up but refused the call, a model not pulled among the
            # reasons, so the run ends as one whose model cannot be reached.
            raise ConnectionError(str(error)) from error
        return response.message.content or ""

    return call


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Embed the corpus once, at startup, and keep the calls a run makes."""
    load_dotenv(ROOT / ".env")
    model = chat_model()
    search = embedder()
    entries = load_corpus(DATA)
    embed = partial(ollama_embed, model=search.model)
    app.state.entries = entries
    app.state.matrix = embed_documents([entry.text for entry in entries], search, embed)
    app.state.calls = Calls(
        gate=served(Gate.model_json_schema(), model),
        plan=served(Plan.model_json_schema(), model),
        answer=served(Ruling.model_json_schema(), model),
        embed=embed,
        embedder=search,
    )
    yield


app = FastAPI(lifespan=lifespan)


class Ask(BaseModel):
    """The request body: the question to rule on."""

    question: str


@app.post("/ask", response_class=EventSourceResponse)
async def ask(body: Ask) -> AsyncIterator[ServerSentEvent]:
    """The question's run, one event per stage."""
    state = app.state
    async for event in run(body.question, state.calls, state.entries, state.matrix):
        yield ServerSentEvent(event=event.name, data=event.data)
