"""Shared M2/M3/M4 parent construction and stage entry points."""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from .hashing import canonical_json_bytes, sha256_bytes
from .network_artifacts import NetworkArtifact, write_network_artifact
from .network_generator import GeneratedNetworks, generate_networks
from .network_schemas import NetworkGenerationConfig
from .population_artifacts import PopulationArtifact, write_population_artifact
from .population_generator import GeneratedPopulation, generate_population
from .population_schemas import (
    PopulationArtifactManifest,
    PopulationGenerationConfig,
    PopulationMode,
)
from .population_structure_artifacts import (
    M2PopulationInput,
    M3StructureInput,
    StructureArtifact,
    load_m2_population_artifact,
    load_m3_structure_artifact,
    logical_structure_hash,
    write_structure_artifact,
)
from .population_structure_generator import GeneratedStructure, generate_structure
from .population_structure_schemas import StructureArtifactManifest, StructureGenerationConfig

DiagnosticsMode = Literal["full", "internal"]


@dataclass(frozen=True)
class ParentBuild:
    generated: GeneratedNetworks
    m4_artifact: NetworkArtifact | None


def _artifact_manifest_paths(reuse_from: Path) -> list[Path]:
    """Find manifest files below one caller-supplied reuse root."""

    reuse_from = reuse_from.resolve()
    if reuse_from.is_file():
        return [reuse_from] if reuse_from.name == "manifest.json" else []
    if not reuse_from.is_dir():
        return []
    return sorted(path for path in reuse_from.rglob("manifest.json") if path.is_file())


def _m2_config_hash(config: PopulationGenerationConfig) -> str:
    return sha256_bytes(canonical_json_bytes(config))


def _m3_config_hash(config: StructureGenerationConfig) -> str:
    return sha256_bytes(canonical_json_bytes(config))


def _expected_m2_artifact_id(config: PopulationGenerationConfig) -> str:
    return f"jos-population-m2-{config.mode}-seed-{config.seed}-{_m2_config_hash(config)[:12]}"


def _expected_m3_artifact_id(config: StructureGenerationConfig) -> str:
    return f"jos-structure-m3-{config.mode}-seed-{config.seed}-{_m3_config_hash(config)[:12]}"


def _m3_logical_hash(m3_input: M3StructureInput) -> str:
    """Recheck the M3 logical hash after the existing manifest/table loader."""

    # ``logical_structure_hash`` only consumes these seven normalized tables;
    # M3StructureInput is intentionally cast to its generated-table protocol.
    return logical_structure_hash(cast(GeneratedStructure, m3_input))


def _load_reusable_parents(
    root: Path,
    mode: PopulationMode,
    seed: int,
    reuse_from: Path,
) -> tuple[M2PopulationInput, M3StructureInput] | None:
    """Load an exact, verified M2/M3 pair or return None for a cold build."""

    m2_config = PopulationGenerationConfig(mode=mode, seed=seed)
    m3_config = StructureGenerationConfig(mode=mode, seed=seed)
    m2_hash = _m2_config_hash(m2_config)
    m3_hash = _m3_config_hash(m3_config)
    manifest_paths = _artifact_manifest_paths(reuse_from)
    m2_candidates: list[tuple[Path, PopulationArtifactManifest]] = []
    m3_candidates: list[tuple[Path, StructureArtifactManifest]] = []

    for manifest_path in manifest_paths:
        try:
            payload = manifest_path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            manifest = PopulationArtifactManifest.model_validate_json(payload)
        except ValueError:
            try:
                m3_manifest = StructureArtifactManifest.model_validate_json(payload)
            except ValueError:
                continue
            if (
                m3_manifest.artifact_id == _expected_m3_artifact_id(m3_config)
                and m3_manifest.generator_version == m3_config.generator_version
                and m3_manifest.mode == mode
                and m3_manifest.seed == seed
                and m3_manifest.config_hash == m3_hash
            ):
                m3_candidates.append((manifest_path.parent, m3_manifest))
            continue
        if (
            manifest.artifact_id == _expected_m2_artifact_id(m2_config)
            and manifest.generator_version == m2_config.generator_version
            and manifest.mode == mode
            and manifest.seed == seed
            and manifest.config_hash == m2_hash
        ):
            m2_candidates.append((manifest_path.parent, manifest))

    if not m2_candidates or not m3_candidates:
        print(
            "PARENT REUSE: REJECTED "
            f"{reuse_from}: no exact M2/M3 manifest pair for mode={mode} seed={seed}; "
            "falling back to a fresh build",
            file=sys.stderr,
        )
        return None

    for m2_path, _ in m2_candidates:
        try:
            m2_input = load_m2_population_artifact(root, m2_path)
        except Exception as exc:  # verification must fail closed for reuse
            print(
                f"PARENT REUSE: REJECTED M2 {m2_path}: {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            continue
        for m3_path, m3_manifest in m3_candidates:
            if (
                m3_manifest.m2_artifact_id != m2_input.manifest.artifact_id
                or m3_manifest.m2_manifest_hash != m2_input.manifest_hash
                or m3_manifest.m2_logical_content_hash != m2_input.manifest.logical_content_hash
            ):
                continue
            try:
                m3_input = load_m3_structure_artifact(root, m3_path)
                if _m3_logical_hash(m3_input) != m3_input.manifest.logical_content_hash:
                    raise ValueError("M3 logical content hash mismatch")
            except Exception as exc:  # verification must fail closed for reuse
                print(
                    f"PARENT REUSE: REJECTED M3 {m3_path}: {type(exc).__name__}: {exc}",
                    file=sys.stderr,
                )
                continue
            print(
                f"PARENT REUSE: REUSED M2={m2_path} M3={m3_path}",
                file=sys.stderr,
            )
            return m2_input, m3_input

    print(
        "PARENT REUSE: REJECTED all matching artifacts; falling back to a fresh build",
        file=sys.stderr,
    )
    return None


def build_population(
    root: Path, config: PopulationGenerationConfig, output_dir: Path
) -> tuple[GeneratedPopulation, PopulationArtifact]:
    generated = generate_population(root, config)
    return generated, write_population_artifact(generated, root, output_dir)


def build_structure(
    root: Path,
    config: StructureGenerationConfig,
    output_dir: Path,
    *,
    population_artifact: Path | None = None,
    population_input: M2PopulationInput | None = None,
) -> tuple[GeneratedStructure, StructureArtifact, M2PopulationInput]:
    if population_input is None:
        if population_artifact is None:
            _, m2_artifact = build_population(
                root,
                PopulationGenerationConfig(mode=config.mode, seed=config.seed),
                output_dir.parent / "populations",
            )
            population_artifact = m2_artifact.artifact_directory
        population_input = load_m2_population_artifact(root, population_artifact)
    generated = generate_structure(root, config, population_input)
    artifact = write_structure_artifact(generated, root, output_dir, population_input)
    return generated, artifact, population_input


def build_network(
    root: Path,
    config: NetworkGenerationConfig,
    m2_input: M2PopulationInput,
    m3_input: M3StructureInput,
    *,
    output_dir: Path | None = None,
    diagnostics: DiagnosticsMode = "full",
    generator: Callable[..., GeneratedNetworks] | None = None,
) -> tuple[GeneratedNetworks, NetworkArtifact | None]:
    generated = (generator or generate_networks)(
        config, m2_input, m3_input, root, diagnostics=diagnostics
    )
    artifact = (
        write_network_artifact(generated, root, output_dir) if output_dir is not None else None
    )
    return generated, artifact


def build_parent(
    root: Path,
    mode: PopulationMode,
    seed: int,
    parent_output: Path,
    *,
    population_artifact: Path | None = None,
    structure_artifact: Path | None = None,
    write_m4: bool = False,
    m4_output: Path | None = None,
    diagnostics: DiagnosticsMode = "full",
    reuse_from: Path | None = None,
) -> ParentBuild:
    """Build the shared, verified M2/M3/M4 parent in the requested location."""

    reused_parents = None
    if population_artifact is None and structure_artifact is None and reuse_from is not None:
        reused_parents = _load_reusable_parents(root, mode, seed, reuse_from)

    if reused_parents is not None:
        m2_input, m3_input = reused_parents
    else:
        if population_artifact is None:
            _, artifact = build_population(
                root,
                PopulationGenerationConfig(mode=mode, seed=seed),
                parent_output / "populations",
            )
            m2_path = artifact.artifact_directory
        else:
            m2_path = population_artifact
        m2_input = load_m2_population_artifact(root, m2_path)

        if structure_artifact is None:
            _, structure_output, _ = build_structure(
                root,
                StructureGenerationConfig(mode=mode, seed=seed),
                parent_output / "structures",
                population_input=m2_input,
            )
            m3_path = structure_output.artifact_directory
        else:
            m3_path = structure_artifact
        m3_input = load_m3_structure_artifact(root, m3_path)
    generated, m4_artifact = build_network(
        root,
        NetworkGenerationConfig(mode=mode, seed=seed),
        m2_input,
        m3_input,
        output_dir=(m4_output or parent_output / "networks") if write_m4 else None,
        diagnostics=diagnostics,
    )
    return ParentBuild(generated, m4_artifact)
