"""Milestone 4 Parquet artifacts, diagnostics and provenance manifests."""

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
from .network_generator import GeneratedNetworks
from .network_schemas import NetworkArtifactManifest
from .population_artifacts import portable_artifact_path


@dataclass(frozen=True)
class NetworkArtifact:
    artifact_directory: Path
    manifest: NetworkArtifactManifest


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


def _write_table(path: Path, rows: list[dict[str, Any]], schema: pa.Schema) -> None:
    if rows:
        table = pa.Table.from_pylist(rows, schema=schema)
    else:
        table = pa.Table.from_arrays(
            [pa.array([], type=field.type) for field in schema], schema=schema
        )
    pq.write_table(table, path, compression="zstd", use_dictionary=True, write_statistics=True)


def _markdown_report(generated: GeneratedNetworks) -> str:
    cross_route = generated.diagnostics["cross_route"]
    calendar = generated.diagnostics["calendars"]
    route_diagnostics = generated.diagnostics["routes"]
    nested_overlap = sum(
        row["overlapping_agent_pairs"]
        for row in cross_route["route_overlap_matrix"]
        if row["policy"] == "FORBIDDEN"
    )
    shared_vehicle = cross_route["shared_vehicle"]
    calendar_provenance = calendar["school_calendar_provenance"]
    lines = [
        "# Milestone 4.1 Jersey route diagnostics",
        "",
        f"Status: **{generated.diagnostics['status']}**",
        f"Mode: `{generated.config.mode}`",
        f"Generated population: **{len(generated.agent_ids)}**",
        "",
        "## Route diagnostics",
        "",
        (
            "| Route | Edges | Participants | Mean degree | Median degree | Max degree | "
            "Repeated edge rate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for route_id, diagnostic in generated.diagnostics["routes"].items():
        lines.append(
            f"| {route_id} | {diagnostic['edge_count']} | {diagnostic['participating_agents']} | "
            f"{diagnostic['mean_degree']:.3f} | {diagnostic['median_degree']:.3f} | "
            f"{diagnostic['max_degree']:.3f} | {diagnostic['repeated_edge_rate']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Cross-route diagnostics",
            "",
            (
                "- Zero non-household contacts: "
                f"`{generated.diagnostics['cross_route']['zero_non_household_contacts']}`"
            ),
            (
                "- Multi-job workplace bridges: "
                f"`{generated.diagnostics['cross_route']['multi_job_workplace_bridges']}`"
            ),
            (
                "- Care staff/community bridges: "
                f"`{generated.diagnostics['cross_route']['care_staff_community_bridges']}`"
            ),
            (f"- Forbidden nested-route overlaps: `{nested_overlap}`."),
            (
                "- Route-overlap policy: forbidden nested layers are "
                "`school_class/school_cross_class` and "
                "`workplace_team/workplace_transient`; distinct physical settings "
                "remain diagnostically visible."
            ),
            (
                "- Shared-vehicle participants / unmatched aggregate-car commuters: "
                f"`{shared_vehicle['shared_vehicle_participants']}` / "
                f"`{shared_vehicle['unmatched_car_commuters']}`."
            ),
            "",
            "## Assumptions and limitations",
            "",
        ]
    )
    lines.extend(
        f"- {assumption}" for assumption in generated.diagnostics["provenance"]["assumptions"]
    )
    school = generated.diagnostics["staffing"]["school"]
    care = generated.diagnostics["staffing"]["care"]
    occupational = generated.diagnostics["staffing"]["occupational_staff_mapping"]
    lines.extend(
        [
            "",
            "## School staffing diagnostics",
            "",
            (
                f"- Observed 2025 CYPES FTE controls: teachers/lecturers "
                f"`{school['observed_fte_controls']['2025']['teachers_and_lecturers']}`, "
                f"teaching assistants "
                f"`{school['observed_fte_controls']['2025']['teaching_assistants']}`, "
                f"heads/deputies `{school['observed_fte_controls']['2025']['heads_and_deputies']}`."
            ),
            f"- Synthetic school staff endpoints: `{school['synthetic_staff_endpoints']}`.",
            "- Staff with household bridge membership: "
            f"`{school['staff_with_household_bridge_membership']}`.",
            f"- Staff assigned to zero schools: `{school['staff_assigned_to_zero_schools']}`.",
            f"- Duplicate staff assignments: `{school['duplicate_staff_assignments']}`.",
            (
                "- School calendar source: "
                f"`{calendar_provenance['source_id']}` "
                f"(SHA-256 `{calendar_provenance['source_sha256']}`)."
            ),
            (
                "- Community indoor/outdoor cross-day Jaccard: "
                f"`{route_diagnostics['community_indoor']['cross_day_jaccard']}` / "
                f"`{route_diagnostics['community_outdoor']['cross_day_jaccard']}`."
            ),
            "",
            "## Care staffing diagnostics",
            "",
            (
                f"- Supported establishments: nursing `{care['nursing_establishments']}`, "
                f"non-nursing `{care['non_nursing_establishments']}`."
            ),
            f"- Synthetic care/support workers: `{care['synthetic_care_support_workers']}`.",
            f"- Synthetic nurses: `{care['synthetic_nurses']}`.",
            f"- Settings failing structural minimums: `{care['settings_failing_minimum']}`.",
            "- Staff with household/community bridge membership: "
            f"`{care['staff_household_community_bridge_membership']}`.",
            "- Ratios are regulatory minimums; actual staff rosters remain unknown.",
            "",
            "## Occupational staff mapping",
            "",
            (
                f"- School staff with reinterpreted M3 primary workplace: "
                f"`{occupational['school']['primary_job_reinterpreted_to_institution']}`; "
                f"secondary-job workers retained: "
                f"`{occupational['school']['m3_secondary_job_workers']}`."
            ),
            (
                f"- Care staff with reinterpreted M3 primary workplace: "
                f"`{occupational['care']['primary_job_reinterpreted_to_institution']}`; "
                f"secondary-job workers retained: "
                f"`{occupational['care']['m3_secondary_job_workers']}`."
            ),
            (
                "- Unintended occupational double-counting after mapping: "
                f"`{occupational['unintended_occupational_double_counting']}`."
            ),
        ]
    )
    lines.append("")
    return "\n".join(lines)


def write_network_artifact(
    generated: GeneratedNetworks, root: Path, output_dir: Path
) -> NetworkArtifact:
    """Persist M4 structural edges and selected dynamic snapshots."""

    root = root.resolve()
    config_hash = sha256_bytes(canonical_json_bytes(generated.config.model_dump(mode="json")))
    artifact_id = (
        f"jos-networks-m4-{generated.config.mode}-seed-{generated.config.seed}-{config_hash[:12]}"
    )
    artifact_directory = output_dir.resolve() / artifact_id
    artifact_directory.mkdir(parents=True, exist_ok=True)
    manifest_path = artifact_directory / "manifest.json"
    if manifest_path.exists():
        existing = NetworkArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        if existing.logical_content_hash != generated.logical_content_hash:
            raise ValueError("immutable M4 artifact ID already exists with different content")
        return NetworkArtifact(artifact_directory, existing)

    route_specs_path = artifact_directory / "route_specs.json"
    route_specs_path.write_text(
        json.dumps(generated.route_specs, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    memberships = [
        {"route_id": route_id, **membership}
        for route_id, rows in sorted(generated.route_memberships.items())
        for membership in rows
    ]
    membership_schema = pa.schema(
        [
            ("route_id", pa.string()),
            ("membership", pa.string()),
            ("group_id", pa.string()),
            ("agent_id", pa.string()),
        ]
    )
    structural_edges = [
        {"route_id": route_id, **edge}
        for route_id, rows in sorted(generated.structural_edges.items())
        for edge in rows
    ]
    edge_schema = pa.schema(
        [
            ("route_id", pa.string()),
            ("p1", pa.string()),
            ("p2", pa.string()),
            ("weight", pa.float64()),
            ("persistence_days", pa.int64()),
        ]
    )
    memberships_path = artifact_directory / "memberships.parquet"
    structural_edges_path = artifact_directory / "structural_edges.parquet"
    _write_table(memberships_path, memberships, membership_schema)
    _write_table(structural_edges_path, structural_edges, edge_schema)

    school_staff_path = artifact_directory / "school_staff_assignments.parquet"
    school_staff_schema = pa.schema(
        [
            ("agent_id", pa.string()),
            ("role", pa.string()),
            ("school_id", pa.string()),
            ("school_type", pa.string()),
            ("school_year", pa.string()),
            ("class_id", pa.string()),
            ("assignment_status", pa.string()),
            ("provenance_status", pa.string()),
        ]
    )
    _write_table(school_staff_path, generated.school_staff_assignments, school_staff_schema)
    care_staff_path = artifact_directory / "care_staff_assignments.parquet"
    care_staff_schema = pa.schema(
        [
            ("agent_id", pa.string()),
            ("role", pa.string()),
            ("setting_id", pa.string()),
            ("setting_type", pa.string()),
            ("assignment_status", pa.string()),
            ("provenance_status", pa.string()),
            ("regulatory_status", pa.string()),
            ("shift_pattern", pa.string()),
        ]
    )
    _write_table(care_staff_path, generated.care_staff_assignments, care_staff_schema)
    staffing_provenance_path = artifact_directory / "staffing_provenance.json"
    staffing_provenance_path.write_text(
        json.dumps(generated.staffing_provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    snapshots = [
        {
            "route_id": route_id,
            "snapshot_date": snapshot_date.isoformat(),
            **edge,
        }
        for snapshot_date in generated.config.snapshot_dates
        for route_id in sorted(generated.route_specs)
        for edge in generated.route_snapshot(route_id, snapshot_date).edges
    ]
    snapshots_path = artifact_directory / "snapshot_edges.parquet"
    snapshot_schema = pa.schema(
        [
            ("route_id", pa.string()),
            ("snapshot_date", pa.string()),
            ("p1", pa.string()),
            ("p2", pa.string()),
            ("weight", pa.float64()),
            ("persistence_days", pa.int64()),
        ]
    )
    _write_table(snapshots_path, snapshots, snapshot_schema)

    diagnostics_path = artifact_directory / "diagnostics.json"
    diagnostics_path.write_text(
        json.dumps(generated.diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    diagnostics_md_path = artifact_directory / "diagnostics.md"
    diagnostics_md_path.write_text(_markdown_report(generated), encoding="utf-8")
    benchmark_path = artifact_directory / "benchmark.json"
    benchmark = {
        "schema_version": "1.0",
        "artifact_id": artifact_id,
        "mode": generated.config.mode,
        "seed": generated.config.seed,
        "target_population": len(generated.agent_ids),
        "generated_population": len(generated.agent_ids),
        "route_count": len(generated.route_specs),
        "structural_edges": sum(len(rows) for rows in generated.structural_edges.values()),
        "selected_snapshot_edges": len(snapshots),
        "construction_runtime_seconds": generated.runtime_seconds,
        "peak_memory_bytes": generated.peak_memory_bytes,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }
    benchmark_path.write_text(
        json.dumps(benchmark, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    route_hashes = {
        route_id: sha256_bytes(
            canonical_json_bytes(
                {
                    "spec": generated.route_specs[route_id],
                    "structural": generated.structural_edges[route_id],
                    "snapshots": [
                        {
                            "date": when.isoformat(),
                            "edges": list(generated.route_snapshot(route_id, when).edges),
                        }
                        for when in generated.config.snapshot_dates
                    ],
                }
            )
        )
        for route_id in sorted(generated.route_specs)
    }
    git_commit, dirty_worktree = _git_metadata(root)
    output_paths = (
        route_specs_path,
        memberships_path,
        structural_edges_path,
        school_staff_path,
        care_staff_path,
        staffing_provenance_path,
        snapshots_path,
        diagnostics_path,
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
    manifest = NetworkArtifactManifest(
        artifact_id=artifact_id,
        generator_version=generated.config.generator_version,
        mode=generated.config.mode,
        seed=generated.config.seed,
        target_population=len(generated.agent_ids),
        actual_population=len(generated.agent_ids),
        m2_artifact_id=generated.m2_input.manifest.artifact_id,
        m2_logical_content_hash=generated.m2_input.manifest.logical_content_hash,
        m3_artifact_id=generated.m3_input.manifest.artifact_id,
        m3_logical_content_hash=generated.m3_input.manifest.logical_content_hash,
        config_hash=config_hash,
        logical_content_hash=generated.logical_content_hash,
        route_logical_hashes=route_hashes,
        diagnostics_status=generated.diagnostics["status"],
        created_at=datetime.now(UTC).isoformat(),
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
    return NetworkArtifact(artifact_directory, manifest)
