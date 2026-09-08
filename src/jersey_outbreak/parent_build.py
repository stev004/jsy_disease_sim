"""Shared M2/M3/M4 parent construction and stage entry points."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .network_artifacts import NetworkArtifact, write_network_artifact
from .network_generator import GeneratedNetworks, generate_networks
from .network_schemas import NetworkGenerationConfig
from .population_artifacts import PopulationArtifact, write_population_artifact
from .population_generator import GeneratedPopulation, generate_population
from .population_schemas import PopulationGenerationConfig, PopulationMode
from .population_structure_artifacts import (
    M2PopulationInput,
    M3StructureInput,
    StructureArtifact,
    load_m2_population_artifact,
    load_m3_structure_artifact,
    write_structure_artifact,
)
from .population_structure_generator import GeneratedStructure, generate_structure
from .population_structure_schemas import StructureGenerationConfig

DiagnosticsMode = Literal["full", "internal"]


@dataclass(frozen=True)
class ParentBuild:
    generated: GeneratedNetworks
    m4_artifact: NetworkArtifact | None


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
) -> ParentBuild:
    """Build the shared, verified M2/M3/M4 parent in the requested location."""

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
