"""Milestone 0 demo orchestration and reproducibility manifest creation."""

from __future__ import annotations

import json
import platform
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .contracts import (
    ArtifactRecord,
    DiseaseParameterProvenance,
    ProjectConfig,
    RunConfig,
    RunManifest,
)
from .hashing import canonical_json_bytes, sha256_bytes, sha256_file
from .starsim_compat import SUPPORTED_STARSIM_VERSION, run_official_sir_demo


@dataclass(frozen=True)
class DemoRun:
    """Paths and machine-readable values emitted by one demo invocation."""

    summary: dict[str, Any]
    manifest: RunManifest
    summary_path: Path
    manifest_path: Path


def build_demo_config(seed: int) -> RunConfig:
    """Build the explicit, versioned configuration for the official spike."""

    return RunConfig(
        run=dict(
            label="starsim-official-sir-randomnet",
            start=2000.0,
            stop=2030.0,
            dt=1.0,
            unit="year",
            seed=seed,
            n_replicates=1,
        ),
        population=dict(artifact_id="starsim-internal-people-demo", mode="demo"),
        disease=dict(module="starsim_sir_demo", parameter_set="starsim-sir-demo-v0.1"),
    )


def _repo_root() -> Path:
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    return current


def _git_metadata(root: Path) -> tuple[str | None, bool]:
    try:
        commit_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        commit = commit_result.stdout.strip() if commit_result.returncode == 0 else None
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        return commit, bool(status_result.stdout.strip())
    except OSError:
        return None, True


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _relative_artifact_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _parameter_set() -> tuple[str, dict[str, Any], str]:
    """Return demo metadata without presenting it as real disease evidence."""

    provenance = DiseaseParameterProvenance(
        distribution="fixed demo values",
        mean=0.8,
        sigma=0.0,
        status="scenario_assumption",
        notes="Starsim SIR compatibility spike only; not a named pathogen parameter.",
    )
    values = {
        "beta_per_year": 0.8,
        "initial_prevalence": 0.1,
        "infectious_duration_years": 0.1,
        "death_probability": 0.0,
        "provenance": provenance.model_dump(mode="json"),
    }
    return "starsim-sir-demo-v0.1", values, sha256_bytes(canonical_json_bytes(values))


def run_demo(*, seed: int, output_dir: Path = Path("outputs")) -> DemoRun:
    """Run the verified spike and persist a summary plus reproducibility manifest."""

    config = build_demo_config(seed)
    project = ProjectConfig()
    root = _repo_root()
    output_root = output_dir if output_dir.is_absolute() else root / output_dir
    run_directory = output_root / f"demo_seed_{seed}"
    run_directory.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    result = run_official_sir_demo(seed=seed)
    runtime_seconds = time.perf_counter() - started
    parameter_set_id, parameter_values, parameter_set_hash = _parameter_set()
    config_hash = sha256_bytes(canonical_json_bytes(config))
    run_id = (
        "jos-demo-"
        + sha256_bytes(
            canonical_json_bytes(
                {
                    "config_hash": config_hash,
                    "parameter_set_hash": parameter_set_hash,
                    "project": project.model_dump(mode="json"),
                    "starsim_version": result.starsim_version,
                }
            )
        )[:12]
    )

    summary: dict[str, Any] = {
        "schema_version": "1.0",
        "run_id": run_id,
        "model": "starsim_official_sir_demo",
        "validation_level": "compatibility_spike",
        "seed": seed,
        "starsim_version": result.starsim_version,
        "population_size": result.n_agents,
        "network": {
            "type": "RandomNet",
            "official_starsim_network": True,
            "n_contacts": result.n_contacts,
        },
        "simulation": {
            "unit": "year",
            "start": 2000.0,
            "stop": 2030.0,
            "dt": 1.0,
        },
        "declared_deterministic_outputs": [
            "seed",
            "starsim_version",
            "time_series",
            "final",
        ],
        "time_series": {
            "time_index": result.time_index,
            "n_susceptible": result.n_susceptible,
            "n_infected": result.n_infected,
            "n_recovered": result.n_recovered,
            "cumulative_infections": result.cumulative_infections,
        },
        "final": {
            "n_susceptible": result.n_susceptible[-1],
            "n_infected": result.n_infected[-1],
            "n_recovered": result.n_recovered[-1],
            "cumulative_infections": result.cumulative_infections[-1],
        },
    }
    summary_bytes = _json_bytes(summary)
    summary_path = run_directory / "summary.json"
    summary_path.write_bytes(summary_bytes)
    summary_hash = sha256_bytes(summary_bytes)

    git_commit, dirty_worktree = _git_metadata(root)
    lock_path = root / "uv.lock"
    lock_hash = sha256_file(lock_path) if lock_path.exists() else "unavailable"
    manifest = RunManifest(
        run_id=run_id,
        created_at=datetime.now(UTC),
        status="completed",
        git_commit=git_commit,
        dirty_worktree_flag=dirty_worktree,
        python_version=platform.python_version(),
        starsim_version=SUPPORTED_STARSIM_VERSION,
        dependency_lock_hash=lock_hash,
        config_hash=config_hash,
        population_artifact_id=config.population.artifact_id,
        parameter_set_id=parameter_set_id,
        parameter_set_hash=parameter_set_hash,
        replicate_seeds=[seed],
        start=config.run.start,
        stop=config.run.stop,
        dt=config.run.dt,
        runtime_seconds=runtime_seconds,
        validation_level="compatibility_spike",
        output_artifacts=[
            ArtifactRecord(
                path=_relative_artifact_path(summary_path, root),
                sha256=summary_hash,
                size_bytes=len(summary_bytes),
            )
        ],
        declared_deterministic_outputs=[
            "summary.seed",
            "summary.starsim_version",
            "summary.time_series",
            "summary.final",
        ],
        summary_sha256=summary_hash,
    )
    manifest_path = run_directory / "run_manifest.json"
    manifest_path.write_bytes(_json_bytes(manifest.model_dump(mode="json")))
    return DemoRun(
        summary=summary, manifest=manifest, summary_path=summary_path, manifest_path=manifest_path
    )
