"""Parquet artifact, logical hash, manifest and report writing for Milestone 2."""

from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from .contracts import ArtifactRecord
from .hashing import canonical_json_bytes, sha256_bytes, sha256_file
from .population_generator import GeneratedPopulation
from .population_schemas import PopulationArtifactManifest


@dataclass(frozen=True)
class PopulationArtifact:
    artifact_directory: Path
    manifest: PopulationArtifactManifest


def logical_content_hash(
    residents: list[dict[str, Any]],
    households: list[dict[str, Any]],
    communal_settings: list[dict[str, Any]],
) -> str:
    """Hash logical rows in stable ID order, independent of Parquet metadata."""

    payload = {
        "residents": sorted(residents, key=lambda row: row["agent_id"]),
        "households": sorted(households, key=lambda row: row["household_id"]),
        "communal_settings": sorted(communal_settings, key=lambda row: row["setting_id"]),
    }
    return sha256_bytes(canonical_json_bytes(payload))


def _write_parquet(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty Parquet artifact: {path}")
    columns = list(rows[0])
    table = pa.Table.from_pylist([{column: row.get(column) for column in columns} for row in rows])
    pq.write_table(table, path, compression="zstd", use_dictionary=True, write_statistics=True)


def _git_metadata(root: Path) -> tuple[str | None, bool]:
    try:
        commit_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        commit = commit_result.stdout.strip() if commit_result.returncode == 0 else None
        return commit, bool(status_result.stdout.strip())
    except OSError:
        return None, True


def portable_artifact_path(path: Path, artifact_directory: Path) -> str:
    """Return a portable path relative to the artifact that contains it."""

    try:
        return path.resolve().relative_to(artifact_directory.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("portable artifact output must be inside its artifact directory") from exc


def resolve_portable_artifact_path(path_value: str, artifact_directory: Path) -> Path:
    """Resolve one manifest path while enforcing the portable path contract."""

    path = Path(path_value)
    if path.is_absolute():
        raise ValueError("portable artifact paths must be relative to the artifact directory")
    if ".." in path.parts:
        raise ValueError("portable artifact paths must not contain parent traversal")
    resolved = (artifact_directory / path).resolve()
    try:
        resolved.relative_to(artifact_directory.resolve())
    except ValueError as exc:
        raise ValueError("portable artifact path escaped its artifact directory") from exc
    return resolved


def _markdown_report(diagnostics: dict[str, Any], benchmark: dict[str, Any]) -> str:
    lines = [
        "# Milestone 2 synthetic population diagnostics",
        "",
        f"Status: **{diagnostics['status']}**",
        f"Mode: `{diagnostics['mode']}`",
        f"Generated population: **{diagnostics['generated_population']}**",
        "",
        "## Benchmark",
        "",
        f"- Runtime seconds: `{benchmark['runtime_seconds']}`",
        f"- Peak resident memory bytes: `{benchmark['peak_memory_bytes']}`",
        f"- Python: `{benchmark['python_version']}`",
        f"- Platform: `{benchmark['platform']}`",
        "",
        "## Population controls",
        "",
        f"- Sex: `{json.dumps(diagnostics['population']['sex'], sort_keys=True)}`",
        f"- Age bands: `{json.dumps(diagnostics['population']['age_bands'], sort_keys=True)}`",
        "",
        "## Parish controls",
        "",
        "| Parish | Target | Generated | Error | Status |",
        "|---|---:|---:|---:|---|",
    ]
    for row in diagnostics["parish"]["rows"]:
        lines.append(
            f"| {row['parish']} | {row['target']} | {row['generated']} | "
            f"{row['absolute_error']} | {row['status']} |"
        )
    lines.extend(
        [
            "",
            "## Household controls",
            "",
            "| Type | Target | Generated | Difference |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in diagnostics["households"]["type_rows"]:
        lines.append(
            f"| {row['household_type']} | {row['target']} | {row['generated']} | "
            f"{row['difference']} |"
        )
    lines.extend(
        [
            "",
            "## Communal settings",
            "",
            "| Setting | Target residents | Generated residents | "
            "Target establishments | Generated establishments |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in diagnostics["communal"]["rows"]:
        lines.append(
            f"| {row['setting_type']} | {row['target_residents']} | {row['generated_residents']} | "
            f"{row['target_establishments']} | {row['generated_establishments']} |"
        )
    lines.extend(["", "## Validation checks", ""])
    for check in diagnostics["checks"]:
        lines.append(
            f"- **{check['status']}** `{check['name']}`: "
            f"actual={check.get('actual', '')}, expected={check.get('expected', '')}, "
            f"tolerance={check.get('tolerance', '')}"
        )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {assumption}" for assumption in diagnostics["provenance"]["assumptions"])
    lines.append("")
    return "\n".join(lines)


def write_population_artifact(
    generated: GeneratedPopulation,
    root: Path,
    output_dir: Path,
) -> PopulationArtifact:
    """Write one versioned population artifact and its manifest."""

    config_hash = sha256_bytes(canonical_json_bytes(generated.config))
    artifact_id = (
        f"jos-population-m2-{generated.config.mode}-seed-{generated.config.seed}-{config_hash[:12]}"
    )
    artifact_directory = output_dir.resolve() / artifact_id
    artifact_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_directory / "manifest.json"
    if manifest_path.exists():
        existing = PopulationArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        if existing.logical_content_hash != generated.logical_content_hash:
            raise ValueError("immutable artifact ID already exists with different logical content")
        return PopulationArtifact(artifact_directory, existing)

    residents_path = artifact_directory / "residents.parquet"
    households_path = artifact_directory / "households.parquet"
    settings_path = artifact_directory / "communal_settings.parquet"
    _write_parquet(residents_path, generated.residents)
    _write_parquet(households_path, generated.households)
    _write_parquet(settings_path, generated.communal_settings)
    benchmark = {
        "schema_version": "1.0",
        "artifact_id": artifact_id,
        "mode": generated.config.mode,
        "seed": generated.config.seed,
        "target_population": generated.config.resolved_target_population,
        "generated_population": len(generated.residents),
        "households": len(generated.households),
        "communal_residents": sum(row["resident_count"] for row in generated.communal_settings),
        "runtime_seconds": generated.runtime_seconds,
        "peak_memory_bytes": generated.peak_memory_bytes,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "output_artifact_bytes": sum(
            path.stat().st_size for path in (residents_path, households_path, settings_path)
        ),
    }
    diagnostics = dict(generated.diagnostics)
    diagnostics["benchmark"] = benchmark
    diagnostics["logical_content_hash"] = generated.logical_content_hash
    diagnostics_json_path = artifact_directory / "diagnostics.json"
    diagnostics_json_path.write_text(
        json.dumps(diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    diagnostics_md_path = artifact_directory / "diagnostics.md"
    diagnostics_md_path.write_text(_markdown_report(diagnostics, benchmark), encoding="utf-8")
    benchmark_path = artifact_directory / "benchmark.json"
    benchmark_path.write_text(
        json.dumps(benchmark, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    git_commit, dirty_worktree = _git_metadata(root)
    output_paths = (
        residents_path,
        households_path,
        settings_path,
        diagnostics_json_path,
        diagnostics_md_path,
        benchmark_path,
    )
    output_artifacts = [
        ArtifactRecord(
            path=portable_artifact_path(path, artifact_directory),
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
        )
        for path in output_paths
    ]
    manifest = PopulationArtifactManifest(
        artifact_id=artifact_id,
        generator_version=generated.config.generator_version,
        mode=generated.config.mode,
        seed=generated.config.seed,
        target_population=generated.config.resolved_target_population,
        actual_population=len(generated.residents),
        household_count=len(generated.households),
        communal_resident_count=sum(row["resident_count"] for row in generated.communal_settings),
        created_at=datetime.now(UTC),
        git_commit=git_commit,
        dirty_worktree_flag=dirty_worktree,
        config_hash=config_hash,
        source_manifest_hash=generated.controls.source_manifest_hash,
        input_canonical_hashes=generated.controls.canonical_hashes,
        logical_content_hash=generated.logical_content_hash,
        diagnostics_status=generated.diagnostics["status"],
        runtime_seconds=generated.runtime_seconds,
        peak_memory_bytes=generated.peak_memory_bytes,
        output_artifacts=output_artifacts,
    )
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return PopulationArtifact(artifact_directory, manifest)
