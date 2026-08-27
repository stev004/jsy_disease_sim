"""Scenario configuration loading and M7 demonstration definitions."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from .intervention_schemas import ScenarioConfig


def _date_value(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return value
    return value


def load_scenario_config(root: Path, path: Path | None = None) -> ScenarioConfig:
    """Load and strictly validate a YAML M7 scenario."""

    scenario_path = path or root / "configs" / "scenarios" / "m7_baseline.yaml"
    try:
        payload = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("scenario YAML must contain a mapping")
        payload["start_date"] = _date_value(payload.get("start_date"))
        for item in payload.get("interventions", []):
            if isinstance(item, dict):
                item["start_date"] = _date_value(item.get("start_date"))
                item["end_date"] = _date_value(item.get("end_date"))
        return ScenarioConfig.model_validate(payload)
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid scenario configuration {scenario_path}: {exc}") from exc
