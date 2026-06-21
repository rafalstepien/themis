import json
import logging
from pathlib import Path

import pytest

from src.review_engine.adapters.outbound import LocalFileContextAdapter


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def test_loads_rules_keyed_by_module_basename(tmp_path: Path) -> None:
    _write(tmp_path / "rules" / "catalog" / "rule.json", {"module": "catalog"})
    adapter = LocalFileContextAdapter(themis_dir=tmp_path)

    rules = adapter.load_rules(["src/themis_example/catalog"])

    assert rules == {"catalog": {"module": "catalog"}}


def test_loads_architecture_keyed_by_module_basename(tmp_path: Path) -> None:
    _write(tmp_path / "architecture" / "orders" / "architecture.json", {"style": "Hexagonal"})
    adapter = LocalFileContextAdapter(themis_dir=tmp_path)

    architecture = adapter.load_architecture(["src/themis_example/orders"])

    assert architecture == {"orders": {"style": "Hexagonal"}}


def test_only_requested_modules_are_loaded(tmp_path: Path) -> None:
    _write(tmp_path / "rules" / "catalog" / "rule.json", {"module": "catalog"})
    _write(tmp_path / "rules" / "payments" / "rule.json", {"module": "payments"})
    adapter = LocalFileContextAdapter(themis_dir=tmp_path)

    rules = adapter.load_rules(["src/themis_example/catalog"])

    assert rules == {"catalog": {"module": "catalog"}}


def test_missing_file_is_skipped(tmp_path: Path) -> None:
    adapter = LocalFileContextAdapter(themis_dir=tmp_path)

    rules = adapter.load_rules(["src/themis_example/catalog"])

    assert rules == {}


def test_malformed_json_is_skipped_with_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path = tmp_path / "rules" / "catalog" / "rule.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")
    adapter = LocalFileContextAdapter(themis_dir=tmp_path)

    with caplog.at_level(logging.WARNING):
        rules = adapter.load_rules(["src/themis_example/catalog"])

    assert rules == {}
    assert any("Malformed JSON" in record.message for record in caplog.records)


def test_warns_when_no_rules_loaded_for_affected_modules(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    adapter = LocalFileContextAdapter(themis_dir=tmp_path)

    with caplog.at_level(logging.WARNING):
        rules = adapter.load_rules(["src/themis_example/catalog"])

    assert rules == {}
    assert any(
        "No rules context loaded" in record.message and record.levelno == logging.WARNING
        for record in caplog.records
    )


def test_does_not_warn_when_at_least_one_module_loads(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    _write(tmp_path / "rules" / "catalog" / "rule.json", {"module": "catalog"})
    adapter = LocalFileContextAdapter(themis_dir=tmp_path)

    with caplog.at_level(logging.WARNING):
        adapter.load_rules(["src/themis_example/catalog", "src/themis_example/payments"])

    assert not any(record.levelno == logging.WARNING for record in caplog.records)


def test_no_warning_when_module_list_empty(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    adapter = LocalFileContextAdapter(themis_dir=tmp_path)

    with caplog.at_level(logging.WARNING):
        adapter.load_rules([])

    assert caplog.records == []


def test_empty_module_list_returns_empty_dict(tmp_path: Path) -> None:
    adapter = LocalFileContextAdapter(themis_dir=tmp_path)

    assert adapter.load_rules([]) == {}
    assert adapter.load_architecture([]) == {}


def test_freeform_payload_is_passed_through_unchanged(tmp_path: Path) -> None:
    payload = {"rules": [{"rule": "x", "extra": ["anything", {"nested": True}]}]}
    _write(tmp_path / "rules" / "catalog" / "rule.json", payload)
    adapter = LocalFileContextAdapter(themis_dir=tmp_path)

    assert adapter.load_rules(["src/themis_example/catalog"]) == {"catalog": payload}
