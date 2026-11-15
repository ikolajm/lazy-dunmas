"""Tests for the endpoint's model calls."""

import asyncio
from typing import Any

import ollama
import pytest

from rules_attorney.app import server
from rules_attorney.gate import Gate
from rules_attorney.retrieve import Embedder


def test_a_model_ollama_refuses_counts_as_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def refuse(**request: Any) -> None:
        # What Ollama answers for a model that has not been pulled.
        raise ollama.ResponseError("model 'some-model' not found", 404)

    monkeypatch.setattr(server.client, "chat", refuse)
    call = server.served(Gate.model_json_schema(), "some-model")
    with pytest.raises(ConnectionError):
        asyncio.run(call("Can a grappled creature attack?"))


@pytest.mark.parametrize("var", [server.MODEL_VAR, server.EMBED_MODEL_VAR])
@pytest.mark.parametrize("value", [None, "", "   "])
def test_the_server_refuses_to_start_without_a_model(
    monkeypatch: pytest.MonkeyPatch, var: str, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv(var, raising=False)
    else:
        monkeypatch.setenv(var, value)
    with pytest.raises(RuntimeError, match=var):
        server.required(var)


def test_the_server_serves_the_models_named(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(server.MODEL_VAR, "some-model")
    monkeypatch.setenv(server.EMBED_MODEL_VAR, "some-embedder")
    monkeypatch.setenv(server.QUERY_PREFIX_VAR, "query: ")
    monkeypatch.delenv(server.DOCUMENT_PREFIX_VAR, raising=False)
    assert server.chat_model() == "some-model"
    assert server.embedder() == Embedder(
        model="some-embedder", query_prefix="query: ", document_prefix=""
    )
