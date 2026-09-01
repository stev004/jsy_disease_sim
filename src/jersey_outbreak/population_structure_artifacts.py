"""Milestone 2 input validation and Milestone 3 Parquet artifacts."""

from __future__ import annotations

import json
import platform
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from .contracts import ArtifactRecord
from .data_pipeline import DataBuildError
from .hashing import canonical_json_bytes, sha256_bytes, sha256_file
from .population_artifacts import logical_content_hash as m2_logical_content_hash
from .population_artifacts import portable_artifact_path, resolve_portable_artifact_path
from .population_schemas import (
    CommunalSettingRecord,
    HouseholdRecord,
    PopulationArtifactManifest,
    ResidentRecord,
)
from .population_structure_schemas import (
    JobAssignmentRecord,
    ResidentStructureRecord,
    SchoolAssignmentRecord,
    SchoolClassRecord,
    SchoolRecord,
    StructureArtifactManifest,
    WorkplaceRecord,
    WorkplaceTeamRecord,
)

if TYPE_CHECKING:
    from .population_structure_generator import GeneratedStructure


@dataclass(frozen=True)
class M2PopulationInput:
    artifact_directory: Path
    manifest: PopulationArtifactManifest
    manifest_hash: str
    residents: list[dict[str, Any]]
    households: list[dict[str, Any]]
    communal_settings: list[dict[str, Any]]


@dataclass(frozen=True)
class StructureArtifact:
    artifact_directory: Path
    manifest: StructureArtifactManifest


@dataclass(frozen=True)
class M3StructureInput:
    """Validated Milestone 3 tables consumed by the Starsim-independent M4 layer."""

    artifact_directory: Path
    manifest: StructureArtifactManifest
    manifest_hash: str
    resident_structure: list[dict[str, Any]]
    schools: list[dict[str, Any]]
    classes: list[dict[str, Any]]
    school_assignments: list[dict[str, Any]]
    workplaces: list[dict[str, Any]]
    workplace_teams: list[dict[str, Any]]
    job_assignments: list[dict[str, Any]]


def _read_parquet(path: Path) -> list[dict[str, Any]]:
    try:
        return pq.read_table(path).to_pylist()
    except (OSError, pa.ArrowException, ValueError) as exc:
        raise DataBuildError(f"cannot read Parquet artifact {path}: {exc}") from exc


def _legacy_manifest_file(path_value: str, root: Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else root / path


def load_m2_population_artifact(root: Path, artifact_directory: Path) -> M2PopulationInput:
    """Load and fail closed on a malformed or tampered Milestone 2 artifact."""

    artifact_directory = artifact_directory.resolve()
    manifest_path = artifact_directory / "manifest.json"
    if not manifest_path.is_file():
        raise DataBuildError(f"Milestone 2 manifest is missing: {manifest_path}")
    try:
        manifest = PopulationArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        raise DataBuildError(f"invalid Milestone 2 manifest: {manifest_path}: {exc}") from exc

    by_name: dict[str, Path] = {}
    for record in manifest.output_artifacts:
        try:
            path = (
                _legacy_manifest_file(record.path, root)
                if manifest.manifest_schema_version == "1.0"
                else resolve_portable_artifact_path(record.path, artifact_directory)
            )
        except ValueError as exc:
            raise DataBuildError(f"invalid Milestone 2 output path: {record.path}: {exc}") from exc
        if not path.is_file():
            raise DataBuildError(f"Milestone 2 output artifact is missing: {path}")
        if sha256_file(path) != record.sha256:
            raise DataBuildError(f"Milestone 2 output artifact hash mismatch: {path}")
        by_name[path.name] = path
    required = {"residents.parquet", "households.parquet", "communal_settings.parquet"}
    if not required.issubset(by_name):
        raise DataBuildError("Milestone 2 artifact does not contain all required Parquet tables")

    residents = _read_parquet(by_name["residents.parquet"])
    households = _read_parquet(by_name["households.parquet"])
    communal_settings = _read_parquet(by_name["communal_settings.parquet"])
    if len(residents) != manifest.actual_population:
        raise DataBuildError("Milestone 2 resident row count does not match its manifest")
    if len(households) != manifest.household_count:
        raise DataBuildError("Milestone 2 household row count does not match its manifest")
    if sum(row["resident_count"] for row in communal_settings) != manifest.communal_resident_count:
        raise DataBuildError("Milestone 2 communal count does not match its manifest")
    try:
        [ResidentRecord.model_validate(row) for row in residents]
        [HouseholdRecord.model_validate(row) for row in households]
        [CommunalSettingRecord.model_validate(row) for row in communal_settings]
    except ValueError as exc:
        raise DataBuildError(f"Milestone 2 Parquet schema validation failed: {exc}") from exc
    logical_hash = m2_logical_content_hash(residents, households, communal_settings)
    if logical_hash != manifest.logical_content_hash:
        raise DataBuildError("Milestone 2 logical content hash mismatch")
    return M2PopulationInput(
        artifact_directory=artifact_directory,
        manifest=manifest,
        manifest_hash=sha256_file(manifest_path),
        residents=residents,
        households=households,
        communal_settings=communal_settings,
    )


def logical_structure_hash(generated: GeneratedStructure) -> str:
    payload = {
        "resident_structure": sorted(generated.resident_structure, key=lambda row: row["agent_id"]),
        "schools": sorted(generated.schools, key=lambda row: row["school_id"]),
        "classes": sorted(generated.classes, key=lambda row: row["class_id"]),
        "school_assignments": sorted(generated.school_assignments, key=lambda row: row["agent_id"]),
        "workplaces": sorted(generated.workplaces, key=lambda row: row["workplace_id"]),
        "workplace_teams": sorted(generated.workplace_teams, key=lambda row: row["team_id"]),
        "job_assignments": sorted(generated.job_assignments, key=lambda row: row["job_id"]),
    }
    return sha256_bytes(canonical_json_bytes(payload))


def load_m3_structure_artifact(root: Path, artifact_directory: Path) -> M3StructureInput:
    """Load and fail closed on a missing, tampered or malformed M3 artifact."""

    artifact_directory = artifact_directory.resolve()
    manifest_path = artifact_directory / "manifest.json"
    if not manifest_path.is_file():
        raise DataBuildError(f"Milestone 3 manifest is missing: {manifest_path}")
    try:
        manifest = StructureArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        raise DataBuildError(f"invalid Milestone 3 manifest: {manifest_path}: {exc}") from exc

    required = {
        "resident_structure.parquet",
        "schools.parquet",
        "classes.parquet",
        "school_assignments.parquet",
        "workplaces.parquet",
        "workplace_teams.parquet",
        "job_assignments.parquet",
    }
    by_name: dict[str, Path] = {}
    for record in manifest.output_artifacts:
        try:
            path = (
                _legacy_manifest_file(record.path, root)
                if manifest.manifest_schema_version == "1.0"
                else resolve_portable_artifact_path(record.path, artifact_directory)
            )
        except ValueError as exc:
            raise DataBuildError(f"invalid Milestone 3 output path: {record.path}: {exc}") from exc
        if path.is_file() and path.name in required:
            if sha256_file(path) != record.sha256:
                raise DataBuildError(f"Milestone 3 output artifact hash mismatch: {path}")
            by_name[path.name] = path
    if set(by_name) != required:
        missing = sorted(required - set(by_name))
        raise DataBuildError(f"Milestone 3 artifact is missing tables: {missing}")

    tables = {name: _read_parquet(path) for name, path in by_name.items()}
    try:
        [
            ResidentStructureRecord.model_validate(row)
            for row in tables["resident_structure.parquet"]
        ]
        [SchoolRecord.model_validate(row) for row in tables["schools.parquet"]]
        [SchoolClassRecord.model_validate(row) for row in tables["classes.parquet"]]
        [SchoolAssignmentRecord.model_validate(row) for row in tables["school_assignments.parquet"]]
        [WorkplaceRecord.model_validate(row) for row in tables["workplaces.parquet"]]
        [WorkplaceTeamRecord.model_validate(row) for row in tables["workplace_teams.parquet"]]
        [JobAssignmentRecord.model_validate(row) for row in tables["job_assignments.parquet"]]
    except ValueError as exc:
        raise DataBuildError(f"Milestone 3 Parquet schema validation failed: {exc}") from exc
    if len(tables["resident_structure.parquet"]) != manifest.actual_population:
        raise DataBuildError("Milestone 3 resident structure row count does not match manifest")

    return M3StructureInput(
        artifact_directory=artifact_directory,
        manifest=manifest,
        manifest_hash=sha256_file(manifest_path),
        resident_structure=tables["resident_structure.parquet"],
        schools=tables["schools.parquet"],
        classes=tables["classes.parquet"],
        school_assignments=tables["school_assignments.parquet"],
        workplaces=tables["workplaces.parquet"],
        workplace_teams=tables["workplace_teams.parquet"],
        job_assignments=tables["job_assignments.parquet"],
    )


def _write_parquet(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise DataBuildError(f"cannot write empty Milestone 3 artifact: {path}")
    columns = list(rows[0])
    table = pa.Table.from_pylist([{column: row.get(column) for column in columns} for row in rows])
    pq.write_table(table, path, compression="zstd", use_dictionary=True, write_statistics=True)


def _git_metadata(root: Path) -> tuple[str | None, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        return commit.stdout.strip() or None, bool(status.stdout.strip())
    except OSError:
        return None, True


def _markdown_report(diagnostics: dict[str, Any], benchmark: dict[str, Any]) -> str:
    lines = [
        "# Milestone 3 daytime-structure diagnostics",
        "",
        f"Status: **{diagnostics['status']}**",
        f"Mode: `{diagnostics['mode']}`",
        f"Generated population: **{diagnostics['generated_population']}**",
        "",
        "## Benchmark",
        "",
        f"- Runtime seconds: `{benchmark['runtime_seconds']}`",
        f"- Peak resident memory bytes: `{benchmark['peak_memory_bytes']}`",
        f"- Output artifact bytes: `{benchmark['output_artifact_bytes']}`",
        "",
        "## Checks",
        "",
    ]
    lines.extend(
        f"- **{check['status']}** `{check['name']}`: "
        f"actual={check.get('actual', '')}, expected={check.get('expected', '')}, "
        f"tolerance={check.get('tolerance', '')}"
        for check in diagnostics["checks"]
    )
    lines.extend(["", "## Assumptions", ""])
    lines.extend(f"- {assumption}" for assumption in diagnostics["provenance"]["assumptions"])
    lines.append("")
    return "\n".join(lines)


def write_structure_artifact(
    generated: GeneratedStructure,
    root: Path,
    output_dir: Path,
    m2_input: M2PopulationInput,
) -> StructureArtifact:
    """Write immutable normalized M3 structure tables and provenance."""

    config_hash = sha256_bytes(canonical_json_bytes(generated.config))
    artifact_id = (
        f"jos-structure-m3-{generated.config.mode}-seed-{generated.config.seed}-{config_hash[:12]}"
    )
    artifact_directory = output_dir.resolve() / artifact_id
    artifact_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_directory / "manifest.json"
    if manifest_path.exists():
        existing = StructureArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        if existing.logical_content_hash != generated.logical_content_hash:
            raise ValueError("immutable M3 artifact ID already exists with different content")
        return StructureArtifact(artifact_directory, existing)

    table_rows = {
        "resident_structure.parquet": generated.resident_structure,
        "schools.parquet": generated.schools,
        "classes.parquet": generated.classes,
        "school_assignments.parquet": generated.school_assignments,
        "workplaces.parquet": generated.workplaces,
        "workplace_teams.parquet": generated.workplace_teams,
        "job_assignments.parquet": generated.job_assignments,
    }
    table_paths: list[Path] = []
    for filename, rows in table_rows.items():
        path = artifact_directory / filename
        _write_parquet(path, rows)
        table_paths.append(path)

    benchmark = {
        "schema_version": "1.0",
        "artifact_id": artifact_id,
        "mode": generated.config.mode,
        "seed": generated.config.seed,
        "target_population": generated.config.resolved_target_population,
        "generated_population": len(generated.resident_structure),
        "schools": len(generated.schools),
        "classes": len(generated.classes),
        "school_assignments": len(generated.school_assignments),
        "workplaces": len(generated.workplaces),
        "workplace_teams": len(generated.workplace_teams),
        "primary_jobs": sum(row["job_role"] == "primary" for row in generated.job_assignments),
        "secondary_jobs": sum(row["job_role"] == "secondary" for row in generated.job_assignments),
        "runtime_seconds": generated.runtime_seconds,
        "peak_memory_bytes": generated.peak_memory_bytes,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "output_artifact_bytes": sum(path.stat().st_size for path in table_paths),
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
    output_paths = (*table_paths, diagnostics_json_path, diagnostics_md_path, benchmark_path)
    output_artifacts = [
        ArtifactRecord(
            path=portable_artifact_path(path, artifact_directory),
            sha256=sha256_file(path),
            size_bytes=path.stat().st_size,
        )
        for path in output_paths
    ]
    git_commit, dirty_worktree = _git_metadata(root)
    manifest = StructureArtifactManifest(
        artifact_id=artifact_id,
        generator_version=generated.config.generator_version,
        mode=generated.config.mode,
        seed=generated.config.seed,
        target_population=generated.config.resolved_target_population,
        actual_population=len(generated.resident_structure),
        m2_artifact_id=m2_input.manifest.artifact_id,
        m2_manifest_hash=m2_input.manifest_hash,
        m2_logical_content_hash=m2_input.manifest.logical_content_hash,
        config_hash=config_hash,
        canonical_input_hashes=generated.controls.canonical_hashes,
        logical_content_hash=generated.logical_content_hash,
        diagnostics_status=generated.diagnostics["status"],
        created_at=datetime.now(UTC),
        git_commit=git_commit,
        dirty_worktree_flag=dirty_worktree,
        runtime_seconds=generated.runtime_seconds,
        peak_memory_bytes=generated.peak_memory_bytes,
        output_artifacts=output_artifacts,
    )
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return StructureArtifact(artifact_directory, manifest)
