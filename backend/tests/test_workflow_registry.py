from pathlib import Path

from app.services.workflow_registry import (
    model_id_from_workflow_id,
    parse_workflow_file,
)


def test_model_id_from_workflow_id() -> None:
    assert (
        model_id_from_workflow_id("email-chat-draft-or-clarify")
        == "yaml/email-chat-draft-or-clarify"
    )


def test_parse_workflow_file_reads_valid_yaml(tmp_path: Path) -> None:
    workflow_file = tmp_path / "workflow.yaml"
    workflow_file.write_text(
        """
id: sample-workflow
version: 1.0.0
metadata:
  name: Sample
""".strip(),
        encoding="utf-8",
    )

    parsed = parse_workflow_file(workflow_file)

    assert parsed is not None
    assert parsed["id"] == "sample-workflow"


def test_parse_workflow_file_returns_none_without_id(tmp_path: Path) -> None:
    workflow_file = tmp_path / "invalid.yaml"
    workflow_file.write_text("version: 1.0.0", encoding="utf-8")

    parsed = parse_workflow_file(workflow_file)

    assert parsed is None
