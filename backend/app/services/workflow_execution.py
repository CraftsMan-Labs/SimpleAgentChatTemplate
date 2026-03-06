from __future__ import annotations

import json
import os
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from queue import Queue
from typing import Any

from simple_agents_py import Client

from app.core.config import settings
from app.models import WorkflowModel
from app.schemas.openai import ChatMessage


@dataclass
class RunResult:
    assistant_text: str
    raw_result: dict[str, Any]
    events: list[dict[str, Any]]
    usage: dict[str, int]


def _client() -> Client:
    api_base = settings.custom_api_base
    api_key = settings.custom_api_key
    if api_key:
        os.environ.setdefault("CUSTOM_API_KEY", api_key)
    if api_base:
        os.environ.setdefault("CUSTOM_API_BASE", api_base)
    return Client(settings.provider, api_base=api_base, api_key=api_key)


def normalize_terminal_output(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        subject = value.get("subject")
        body = value.get("body")
        if isinstance(subject, str) and isinstance(body, str):
            return f"Subject: {subject}\n\n{body}"
    return json.dumps(value, indent=2, ensure_ascii=True)


def usage_from_result(result: dict[str, Any]) -> dict[str, int]:
    prompt = int(result.get("total_input_tokens") or 0)
    completion = int(result.get("total_output_tokens") or 0)
    total = int(result.get("total_tokens") or (prompt + completion))
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
    }


def build_workflow_input(
    messages: list[ChatMessage], model: WorkflowModel
) -> dict[str, Any]:
    payload_messages = [m.model_dump(exclude_none=True) for m in messages]
    last_user_text = ""
    for msg in reversed(messages):
        if msg.role == "user":
            last_user_text = msg.content
            break
    workflow_input: dict[str, Any] = {
        "messages": payload_messages,
        "email_text": last_user_text,
    }
    if model.kind == "workflow_bundle" and model.registry:
        workflow_input["workflow_registry"] = model.registry
    return workflow_input


def run_non_stream(
    messages: list[ChatMessage], model: WorkflowModel, conversation_id: str
) -> RunResult:
    client = _client()
    workflow_input = build_workflow_input(messages, model)
    options = {
        "trace": {"tenant": {"conversation_id": conversation_id}},
        "telemetry": {"nerdstats": True},
    }
    started = time.time()
    result = client.run_workflow_yaml(
        model.workflow_path,
        workflow_input,
        include_events=True,
        workflow_options=options,
    )
    result.setdefault("total_elapsed_ms", int((time.time() - started) * 1000))
    terminal_output = result.get("terminal_output")
    return RunResult(
        assistant_text=normalize_terminal_output(terminal_output),
        raw_result=result,
        events=result.get("events", [])
        if isinstance(result.get("events"), list)
        else [],
        usage=usage_from_result(result),
    )


def run_stream(
    messages: list[ChatMessage], model: WorkflowModel, conversation_id: str
) -> Iterator[dict[str, Any]]:
    client = _client()
    workflow_input = build_workflow_input(messages, model)
    options = {
        "trace": {"tenant": {"conversation_id": conversation_id}},
        "telemetry": {"nerdstats": True},
    }
    events: list[dict[str, Any]] = []
    stream_queue: Queue[dict[str, Any] | object] = Queue()
    done_sentinel = object()
    outcome: dict[str, Any] = {}

    def on_event(event: dict[str, Any]) -> None:
        events.append(event)
        event_type = event.get("event_type")
        delta = event.get("delta")
        step_id = event.get("step_id")
        step_name = event.get("step_name")
        node_id = event.get("node_id")
        if event_type in {
            "node_stream_delta",
            "node_stream_output_delta",
        } and isinstance(delta, str):
            stream_queue.put(
                {
                    "type": "delta",
                    "content": delta,
                    "step_id": step_id if isinstance(step_id, str) else None,
                    "step_name": (
                        step_name
                        if isinstance(step_name, str)
                        else node_id
                        if isinstance(node_id, str)
                        else step_id
                        if isinstance(step_id, str)
                        else None
                    ),
                }
            )

    def worker() -> None:
        try:
            result = client.run_workflow_yaml_stream(
                model.workflow_path,
                workflow_input,
                on_event=on_event,
                workflow_options=options,
            )
            outcome["result"] = result
        except Exception as exc:
            outcome["error"] = exc
        finally:
            stream_queue.put(done_sentinel)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    while True:
        item = stream_queue.get()
        if item is done_sentinel:
            break
        if isinstance(item, dict):
            yield item

    thread.join(timeout=0.1)

    if "error" in outcome:
        raise outcome["error"]

    result = outcome.get("result", {})
    if not isinstance(result, dict):
        result = {}

    terminal_text = normalize_terminal_output(result.get("terminal_output"))
    yield {
        "type": "completed",
        "assistant_text": terminal_text,
        "raw_result": result,
        "events": events,
        "usage": usage_from_result(result),
    }
