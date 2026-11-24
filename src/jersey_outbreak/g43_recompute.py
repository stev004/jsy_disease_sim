"""Independently recompute frozen G43 results from a sealed bundle using the stdlib."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import stat
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Context, Decimal, Inexact, localcontext
from itertools import product
from pathlib import Path
from typing import Any

PREDECLARATION = "2026-11-20-g43-predeclaration.md"
FROZEN_INPUT_SHA256 = {
    PREDECLARATION: "67c3c7c03c1ec0f6176e430098c702a913368de51a9e8793c145094255b71094",
    "2026-11-20-g43-owner-ruling.md": (
        "ba442e94e4791d9c0a502d4656e580c591c4eed2c8ece50fbaecd6a655cd117c"
    ),
    "2026-11-21-g43-owner-clarification-1.md": (
        "55df2b8dd612e297915ef90221f5775e1e2d298d9b8b9913918d3552d65d1804"
    ),
    "2026-11-20-g43-seed-precheck.json": (
        "015c8b6b0d24da99fffd4b0908979199aef756757acaf1612de1e3305cf5a379"
    ),
    "v13_g43_multilibrary.yaml": "118d990be856e5f5783a1d991cba4cd29982ef67bb0891e6a31d9958ff3602d2",
}
DIMENSIONS = (
    "beta",
    "inoculation_day_offset",
    "symptomatic_detection_probability",
    "asymptomatic_detection_probability",
)
WORK_FIELDS = (
    "builds",
    "latent_calls",
    "observation_transforms",
    "candidate_cells",
    "gate_loss_evaluations",
    "gate_blind_records",
    "descriptive_loss_evaluations",
    "descriptive_blind_records",
    "serosurvey_samples",
)
VIEWS = {
    "all_twelve": slice(0, 12),
    "batch1": slice(0, 3),
    "batch2": slice(3, 6),
    "batch3": slice(6, 9),
    "batch4": slice(9, 12),
    "batches_1_2": slice(0, 6),
}
START = date(2025, 1, 6)
LATENT_DAYS = 30
DATES = tuple((START + timedelta(days=index)).isoformat() for index in range(34))
ROUTES = (
    "bus",
    "care_resident",
    "care_staff",
    "community_indoor",
    "community_outdoor",
    "household",
    "school_class",
    "school_cross_class",
    "shared_vehicle",
    "workplace_team",
    "workplace_transient",
)
CHANNELS = ("symptomatic", "asymptomatic")
SHA256SUMS = "SHA256SUMS"


class BundleError(ValueError):
    """Retained evidence cannot substantiate the reported result."""


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _file_digest(path: Path) -> str:
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def _manifest(directory: Path, *, check_modes: bool) -> bytes:
    entries = []
    for path in [directory, *sorted(directory.rglob("*"))]:
        mode = path.lstat().st_mode
        if check_modes and mode & 0o222:
            raise BundleError(f"bundle entry has write bits set: {path}")
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise BundleError(f"non-regular bundle entry: {path}")
        relative = path.relative_to(directory).as_posix()
        if "\n" in relative or "\r" in relative:
            raise BundleError(f"invalid bundle path: {path!r}")
        if relative != SHA256SUMS:
            entries.append(f"{_file_digest(path)}  {relative}\n")
    return "".join(entries).encode()


def verify_bundle(directory: Path) -> None:
    if directory.is_symlink() or not directory.is_dir():
        raise BundleError("bundle root must be a real directory")
    expected = _manifest(directory, check_modes=True)
    try:
        manifest = (directory / SHA256SUMS).read_bytes()
    except FileNotFoundError as exc:
        raise BundleError("bundle SHA256SUMS is missing") from exc
    if manifest != expected:
        raise BundleError("bundle SHA256SUMS content or file set mismatch")


def _latent_chronology(event: Mapping[str, Any]) -> bool:
    # outbreak_runner.py: natural_history.chronology_passed.
    return event["infection_date"] < event["infectious_start_date"] <= event[
        "recovery_date"
    ] and event["symptom_onset_date"] == (
        event["infectious_start_date"] if event["symptomatic"] else None
    )


def _observation_chronology(event: Mapping[str, Any]) -> bool:
    # observation.observe_latent_run: chronology_violations.
    detection = event["detection_date"]
    report = event["report_date"]
    onset = event["symptom_onset_date"]
    return (
        _latent_chronology(event)
        and (
            detection is None
            or (detection >= event["infection_date"] and (onset is None or detection >= onset))
        )
        and (report is None or (detection is not None and report >= detection))
    )


def recompute_p3(truth: Mapping[str, Any]) -> dict[str, bool]:
    """Read only the retained raw sources for the four §10 checks."""
    population = truth["benchmark"]["n_agents"]
    observation_events = truth["observation_events"]
    return {
        "natural_history.chronology_passed": all(
            _latent_chronology(event) for event in truth["transmission_events"]
        ),
        "states.conserved": all(
            row["susceptible"] + row["exposed"] + row["infectious"] + row["recovered"] == population
            for row in truth["daily_epidemic"]
        ),
        "no_report_before_infection": all(map(_observation_chronology, observation_events)),
        "latent_incidence_conservation": sum(
            row["latent_infections"] for row in truth["daily_observed_cases"]
        )
        == len(observation_events),
    }


def _read_json(path: Path) -> Any:
    return json.loads(path.read_bytes())


def table_sha256(table: Mapping[str, Any]) -> str:
    return _digest(_json_bytes(table) + b"\n")


def _table_matches(table: Mapping[str, Any], dates: Sequence[str]) -> bool:
    return (
        set(table) == {"dates", *CHANNELS}
        and table["dates"] == list(dates)
        and all(
            len(table[channel]) == len(dates)
            and all(
                type(value) in (int, float)
                and math.isfinite(value)
                and value >= 0
                and value == int(value)
                for value in table[channel]
            )
            for channel in CHANNELS
        )
    )


def _model_controls_match(
    record: Mapping[str, Any],
    cell: Mapping[str, Any],
    *,
    process_seed: int,
    observation_seed: int,
    config_id: str,
) -> bool:
    run = record["returned_run_config"]
    obs = record["returned_observation_config"]
    rng = record["observation_rng"]
    stream = f"{process_seed}|{observation_seed}|{config_id}|observation".encode()
    stream_seed = int.from_bytes(hashlib.sha256(stream).digest()[:8], "little")
    return (
        run == record["requested_run_config"]
        and obs == record["requested_observation_config"]
        and type(record["n_agents"]) is int
        and record["n_agents"] == 3000
        and type(record["parent_network_seed"]) is int
        and record["parent_network_seed"] == process_seed == run["seed"]
        and run["mode"] == "ci"
        and run["start_date"] == START.isoformat()
        and run["duration_days"] == LATENT_DAYS
        and run["dt_days"] == 1
        and run["beta"] == cell["beta"]
        and run["initial_seed_count"] == 0
        and run["initial_prevalence"] is None
        and run["import_rate_per_day"] == 0
        and run["import_schedule"]
        == {(START + timedelta(days=cell["inoculation_day_offset"])).isoformat(): 10}
        and run["route_multipliers"] == dict.fromkeys(ROUTES, 1.0)
        and run["symptomatic_probability"] == 0.6
        and run["latent_duration"]["family"] == "constant"
        and run["latent_duration"]["mean_days"] == 2
        and run["infectious_duration"]["family"] == "constant"
        and run["infectious_duration"]["mean_days"] == 5
        and run["waning_enabled"] is False
        and obs["observation_seed"] == observation_seed
        and obs["observation_config_id"] == config_id
        and obs["analysis_horizon_tail_days"] == 4
        and obs["day_of_week_effect"] == [1.0] * 7
        and obs["detection_delay"]["kind"] == obs["reporting_delay"]["kind"] == "fixed"
        and obs["detection_delay"]["days"] == [0]
        and obs["reporting_delay"]["days"] == [2]
        and all(obs["parameters"][name]["value"] == cell[name] for name in DIMENSIONS[2:])
        and rng["stream_namespace"] == "observation"
        and rng["stream_key_inputs"]
        == ["latent_replicate_seed", "observation_seed", "observation_config_id"]
        and rng["stream_fingerprint"] == _digest(str(stream_seed).encode())
    )


def provenance_matches(
    record: Mapping[str, Any],
    cell: Mapping[str, Any],
    *,
    library: int | None,
    batch: int | None,
    position: int,
    process_seed: int,
    observation_seed: int,
    hashes: Sequence[str],
    dates: Sequence[str],
    table: Mapping[str, Any],
) -> bool:
    """Check serialized evidence against an independently supplied declaration row."""
    try:
        lineage = record["population_lineage"]
        return (
            record["library"] == library
            and record["batch"] == batch
            and record["position"] == position
            and record["process_seed"] == process_seed
            and record["observation_seed"] == observation_seed
            and record["cell"] == cell
            and tuple(lineage[name] for name in ("m2", "m3", "m4")) == tuple(hashes)
            and _table_matches(table, dates)
            and record["table_sha256"] == table_sha256(table)
            and _model_controls_match(
                record,
                cell,
                process_seed=process_seed,
                observation_seed=observation_seed,
                config_id="v13-g43-target" if library is None else "v13-g43-fit",
            )
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def candidate_binding(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "run": record["returned_run_config"],
        "observation": record["returned_observation_config"],
        "table_sha256": record["table_sha256"],
    }


def binding_hash(records: Sequence[Mapping[str, Any]]) -> str:
    return _digest(_json_bytes(records) + b"\n")


def read_candidate_library(
    directory: Path,
    cells: Sequence[Mapping[str, Any]],
    roster: Sequence[tuple[int, int, int, int, int, Sequence[str]]],
    dates: Sequence[str],
) -> tuple[bool, bool, list[list[Mapping[str, Any]]]]:
    """Read each retained cell in frozen position order, checking P1 and P9."""
    base = directory / "candidate_tables"
    expected = {
        base / str(index) / f"{position:02d}.json"
        for index in range(len(cells))
        for _, _, position, _, _, _ in roster
    }
    actual = set(base.rglob("*.json"))
    complete = actual == expected
    provenance = complete
    library_rows: list[list[Mapping[str, Any]]] = []
    for index, cell in enumerate(cells):
        rows = []
        for number, batch, position, seed, observation_seed, hashes in roster:
            path = base / str(index) / f"{position:02d}.json"
            try:
                record = _read_json(path)
                table = record["table"]
            except (OSError, KeyError, TypeError, ValueError):
                complete = provenance = False
                continue
            rows.append(record)
            provenance &= provenance_matches(
                record,
                cell,
                library=number,
                batch=batch,
                position=position,
                process_seed=seed,
                observation_seed=observation_seed,
                hashes=hashes,
                dates=dates,
                table=table,
            )
        library_rows.append(rows)
    return complete, provenance, library_rows


@dataclass(frozen=True)
class _Dimension:
    name: str
    truth: Decimal
    grid: tuple[Decimal, ...]
    tolerance: Decimal
    bias_limit: Decimal


@dataclass(frozen=True)
class _Seed:
    library: int | None
    batch: int | None
    position: int
    process: int
    observation: int
    hashes: tuple[str, ...]
    replaced: int | None


def _markdown_rows(section: str) -> list[list[str]]:
    return [
        [value.strip().strip("`") for value in line.strip("|").split("|")]
        for line in section.splitlines()
        if line.startswith("| ")
    ]


def _declaration_controls(text: str) -> tuple[list[_Dimension], list[_Seed], list[dict[str, int]]]:
    grid_section = text.split("| Dimension | Truth | Grid | Tolerance | Bias limit |", 1)[1]
    dim_rows = _markdown_rows(grid_section.split("**Changes against", 1)[0])
    dimensions = [
        _Dimension(
            name,
            Decimal(truth),
            tuple(map(Decimal, grid.split(", "))),
            Decimal(tolerance),
            Decimal(bias),
        )
        for name, (_, truth, grid, tolerance, bias) in zip(DIMENSIONS, dim_rows, strict=True)
    ]
    replacements = {
        int(reserve): int(primary)
        for _, _, primary, _, reserve in _markdown_rows(
            text.split("### Exclusions and replacements", 1)[1].split("### Final seed table", 1)[0]
        )[1:]
    }
    seeds = []
    rows = _markdown_rows(
        text.split("### Final seed table (92 seeds)", 1)[1].split("### Unused reserves", 1)[0]
    )[1:]
    for role, library, batch, position, process_id, observation, _, _, *hashes in rows:
        process_seed = int(process_id.split()[0])
        seeds.append(
            _Seed(
                None if role == "target" else int(library),
                None if role == "target" else int(batch),
                int(position),
                process_seed,
                int(observation),
                tuple(hashes),
                replacements.get(process_seed),
            )
        )
    work_rows = _markdown_rows(
        text.split("| Quantity | Shared panel | Per library | Formula | **Total** |", 1)[1].split(
            "The reference evaluations", 1
        )[0]
    )
    columns = [
        dict(
            zip(
                WORK_FIELDS,
                (
                    int(row[index].split(" = ")[-1].strip("*").replace(",", ""))
                    if row[index] != "—"
                    else 0
                    for row in work_rows
                ),
                strict=True,
            )
        )
        for index in (1, 2, 4)
    ]
    return dimensions, seeds, columns


def _cell_payload(values: Sequence[Decimal]) -> dict[str, Any]:
    beta, offset, symptomatic, asymptomatic = values
    return dict(
        zip(
            DIMENSIONS,
            (float(beta), int(offset), float(symptomatic), float(asymptomatic)),
            strict=True,
        )
    )


def _p2_and_p3(raw: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, bool]]:
    events = raw["transmission_events"]
    counts: dict[str, Counter[str]] = {channel: Counter() for channel in CHANNELS}
    for event in raw["observation_events"]:
        report = event["report_date"]
        if report in DATES:
            counts["symptomatic" if event["symptomatic"] else "asymptomatic"][report] += 1
    table = {
        "dates": list(DATES),
        **{channel: [float(counts[channel][day]) for day in DATES] for channel in CHANNELS},
    }
    conditions = {
        "inoculation_acquisitions": sum(event["imported"] for event in events) == 10,
        "local_secondary_infections": any(event["source_kind"] == "local" for event in events),
        "symptomatic_reports": bool(counts["symptomatic"]),
        "asymptomatic_reports": bool(counts["asymptomatic"]),
        "nonzero_combined_report_dates": len(
            counts["symptomatic"].keys() | counts["asymptomatic"].keys()
        )
        >= 3,
        **recompute_p3(raw),
    }
    return table, conditions


def _roots(table: Mapping[str, Any]) -> tuple[float, ...]:
    return tuple(math.sqrt(count + 3.0 / 8.0) for channel in CHANNELS for count in table[channel])


def _library_surfaces(
    records: Sequence[Sequence[Mapping[str, Any]]],
    targets: Mapping[int, tuple[float, ...]],
    cells: Sequence[Mapping[str, Any]],
    positions: slice,
) -> dict[int, list[dict[str, Any]]]:
    surfaces: dict[int, list[dict[str, Any]]] = {seed: [] for seed in targets}
    for cell, rows in zip(cells, records, strict=True):
        view = rows[positions]
        config_hash = binding_hash([candidate_binding(record) for record in view])
        means = tuple(
            sum(values) / len(view)
            for values in zip(*(_roots(record["table"]) for record in view), strict=True)
        )
        for target, observed in targets.items():
            score = 0.0
            for actual, expected in zip(observed, means, strict=True):
                score += (actual - expected) ** 2
            surfaces[target].append(
                {**cell, "config_hash": config_hash, "objective": score / (2.0 * len(DATES))}
            )
    return surfaces


def _recompute_fit(
    surface: list[dict[str, Any]], dimensions: Sequence[_Dimension]
) -> dict[str, Any]:
    minimum = min(row["objective"] for row in surface)
    tau = 1e-12 * max(1.0, minimum)
    minimizers = [
        {key: row[key] for key in DIMENSIONS}
        for row in surface
        if abs(row["objective"] - minimum) <= tau
    ]
    tied = len(minimizers) != 1
    profiles = []
    for dimension in dimensions:
        name = dimension.name
        values = list(map(float, dimension.grid))
        by_value = dict.fromkeys(values, math.inf)
        for row in surface:
            value = float(row[name])
            by_value[value] = min(by_value[value], row["objective"])
        profiled = list(by_value.values())
        best = min(profiled)
        profile_tie = sum(abs(value - best) <= tau for value in profiled) > 1
        second = min((value for value in profiled if value > best + tau), default=None)
        gap = None if second is None else (second - best) / max(best, 1e-12)
        profiles.append(
            {
                "dimension": name,
                "values": values,
                "profiled_objectives": profiled,
                "minimum": best,
                "second_minimum": second,
                "numerical_tie": profile_tie,
                "relative_gap": gap,
                "identified": not profile_tie and gap is not None and gap >= 0.05,
            }
        )
    hashed_fields = {
        "selected": None if tied else minimizers[0],
        "minimum_objective": minimum,
        "profiles": profiles,
        "numerical_tie": tied,
        "loss_surface": surface,
    }
    return {
        **hashed_fields,
        "global_minimizers": minimizers,
        "tie_tolerance": tau,
        "identified": not tied and all(profile["identified"] for profile in profiles),
        "estimate_hash": _digest(_json_bytes(hashed_fields)),
    }


def _recovery(
    fits: Sequence[Mapping[str, Any]], dimensions: Sequence[_Dimension]
) -> dict[str, Any]:
    hits = dict.fromkeys(DIMENSIONS, 0)
    boundaries = dict.fromkeys(DIMENSIONS, 0)
    errors: dict[str, list[Decimal]] = {name: [] for name in DIMENSIONS}
    joint = ties = 0
    n = len(fits)
    with localcontext(Context(traps=[Inexact])):
        for fit in fits:
            if fit["numerical_tie"]:
                ties += 1
                continue
            all_hit = True
            for spec, profile in zip(dimensions, fit["profiles"], strict=True):
                name = spec.name
                # Map the selected numeric grid value back to its declared decimal.
                selected = next(
                    value for value in spec.grid if float(value) == fit["selected"][name]
                )
                error = selected - spec.truth
                hit = profile["identified"] and abs(error) <= spec.tolerance
                hits[name] += int(hit)
                boundaries[name] += int(selected in (spec.grid[0], spec.grid[-1]))
                errors[name].append(error)
                all_hit &= hit
            joint += all_hit
        biases = {
            name: sum(values, Decimal(0)) / n if len(values) == n else None
            for name, values in errors.items()
        }
        bias_margins = {
            spec.name: None if (bias := biases[spec.name]) is None else spec.bias_limit - abs(bias)
            for spec in dimensions
        }
        predicates = {
            "P4": ties == 0,
            "P5": all(5 * value >= 4 * n for value in hits.values()),
            "P6": 5 * joint >= 3 * n,
            "P7": all(margin is not None and margin >= 0 for margin in bias_margins.values()),
            "P8": all(5 * value <= n for value in boundaries.values()),
        }
    margins = [
        *(count - 16 for count in hits.values()),
        joint - 12,
        *(4 - count for count in boundaries.values()),
    ]
    return {
        "recovery": predicates,
        "hits": hits,
        "joint_hits": joint,
        "boundary_counts": boundaries,
        "mean_bias": {name: None if bias is None else str(bias) for name, bias in biases.items()},
        "bias_margins": {
            name: None if margin is None else str(margin) for name, margin in bias_margins.items()
        },
        "count_margins": margins,
        "min_count_margin": min(margins),
        "at_threshold": 0 in margins,
        "tie_count": ties,
    }


def _blind_path(view: str, seed: int) -> str:
    if view == "all_twelve":
        return f"blind_estimates/{seed}.json"
    return f"descriptive_estimates/{view}/{seed}.json"


def _blind_file_checks(
    path: Path,
    entry: Mapping[str, Any],
    *,
    view: str,
    seed: int,
    target_sha: str,
    expected_fit: Mapping[str, Any],
) -> tuple[bool, bool]:
    try:
        data = path.read_bytes()
        fit = json.loads(data)
        return len(fit["loss_surface"]) == 625, (
            entry
            == {
                "view": view,
                "target_seed": seed,
                "path": _blind_path(view, seed),
                "sha256": _digest(data),
                "estimate_hash": expected_fit["estimate_hash"],
                "target_sha256": target_sha,
            }
            and _json_bytes(fit) == _json_bytes(expected_fit)
        )
    except (OSError, KeyError, TypeError, ValueError):
        return False, False


def _recompute_library(
    directory: Path,
    number: int,
    seeds: Sequence[_Seed],
    cells: Sequence[Mapping[str, Any]],
    targets: Mapping[int, tuple[float, ...]],
    target_hashes: Mapping[int, str],
    dimensions: Sequence[_Dimension],
    work_ok: bool,
) -> tuple[dict[str, bool], dict[str, dict[str, Any]]]:
    roster = [
        (number, seed.batch, seed.position, seed.process, seed.observation, seed.hashes)
        for seed in seeds
        if seed.library == number and seed.batch is not None
    ]
    complete, provenance, records = read_candidate_library(directory, cells, roster, DATES)
    integrity = {"P1": complete, "P9": provenance, "P10": work_ok}
    if not all(integrity.values()):
        return integrity, {}
    paths = {_blind_path(view, seed) for view in VIEWS for seed in targets}
    actual = {
        path.relative_to(directory).as_posix()
        for prefix in ("blind_estimates", "descriptive_estimates")
        for path in (directory / prefix).rglob("*.json")
    }
    integrity["P1"] &= paths == actual
    try:
        index = _read_json(directory / "blind_readback_hashes.json")
        by_path = {row["path"]: row for row in index}
        integrity["P9"] &= len(index) == len(paths) and set(by_path) == paths
    except (OSError, KeyError, TypeError, ValueError):
        integrity["P9"] = False
    if not all(integrity.values()):
        return integrity, {}
    metrics = {}
    for view, positions in VIEWS.items():
        fits = []
        for seed, surface in _library_surfaces(records, targets, cells, positions).items():
            fit = _recompute_fit(surface, dimensions)
            fits.append(fit)
            relative = _blind_path(view, seed)
            file_complete, provenance = _blind_file_checks(
                directory / relative,
                by_path.get(relative, {}),
                view=view,
                seed=seed,
                target_sha=target_hashes[seed],
                expected_fit=fit,
            )
            integrity["P1"] &= file_complete
            integrity["P9"] &= provenance
        metrics[view] = _recovery(fits, dimensions)
    return integrity, metrics


def _work_matches(record: Mapping[str, Any], caps: Mapping[str, int]) -> bool:
    measured = record.get("measured")
    return (
        isinstance(measured, dict)
        and all(type(count) is int for count in measured.values())
        and measured == caps
    )


_STATUS_PREFIX = (
    "Phase 0: FAIL (2026-09-24); Phase 0b: FAIL (2026-09-26); "
    "G35-B: B FAIL, i PASS, ii FAIL, iii FAIL; G43: "
)


def _void(cause: str) -> dict[str, Any]:
    return {"software_status": "VOID", "cause": cause, "status_phrase": _STATUS_PREFIX + "VOID"}


def _render_reading(text: str, across: Mapping[str, Any], libraries: Mapping[str, Any]) -> str:
    section = text.split("## 7.4", 1)[1].split("### 7.5", 1)[0]
    templates = dict(re.findall(r'^\*\*([A-Z-]+)\.\*\* "([^"]+)"', section, re.MULTILINE))
    reading_class = across["class"]
    reading = templates[reading_class]
    if reading_class == "NO-READING":
        cause_template = re.search(r'Cause sentence, `shared_panel`: "([^"]+)"', section)
        if cause_template is None:
            raise BundleError("frozen shared-panel reading template missing")
        failed = "; ".join(
            f"{seed}: {', '.join(names)}"
            for seed, names in across["cause"]["failed_conditions"].items()
        )
        cause = cause_template[1].replace("<target seeds: failed conditions>", failed)
        return reading.replace("<Cause sentence.>", cause).replace("<k′>", str(across["k_prime"]))
    failing, passing_margins = [], []
    for number, library in libraries.items():
        if library["scientific_status"] == "PASS":
            passing_margins.append(library["min_count_margin"])
            continue
        details = {
            "P4": f"{library['tie_count']}/20 ties",
            "P5": ", ".join(f"{name}={count}/20" for name, count in library["hits"].items()),
            "P6": f"{library['joint_hits']}/20 joint hits",
            "P7": ", ".join(
                f"{name}={'undefined' if value is None else value}"
                for name, value in library["mean_bias"].items()
            ),
            "P8": ", ".join(
                f"{name}={count}/20" for name, count in library["boundary_counts"].items()
            ),
        }
        failures = [f"{key} ({details[key]})" for key in details if not library["predicates"][key]]
        failing.append(f"L{number}: {', '.join(failures)}")
    replacements = {
        "<k>": str(across["k"]),
        "<6 − k>": str(6 - across["k"]),
        "<ℓ: predicates with counts>": "; ".join(failing),
        "<d>": str(min(passing_margins, default=0)),
        "<n>": str(sum(library["at_threshold"] for library in libraries.values())),
    }
    for field, value in replacements.items():
        reading = reading.replace(field, value)
    return reading


def _reference_sentences(text: str, across: Mapping[str, Any]) -> list[str]:
    source = text.split("**Disclosure sentences", 1)[1].split("For CONSISTENT-PASS", 1)[0]
    sentences = re.findall(r'\*\* "([^"]+)"', source)
    return [
        sentence.replace("<k′>", str(across["k_prime"])).replace("<m>", str(across["m"]))
        for key, sentence in zip(("s1", "s2"), sentences, strict=True)
        if across[key]
    ]


def _verify_seed_ledger(directory: Path, seeds: Sequence[_Seed]) -> bool:
    expected = [
        {
            "role": "target" if seed.library is None else "candidate",
            "library": seed.library,
            "batch": seed.batch,
            "position": seed.position,
            "process_seed": seed.process,
            "observation_seed": seed.observation,
            "observation_config_id": "v13-g43-target" if seed.library is None else "v13-g43-fit",
            "replaces_process_seed": seed.replaced,
        }
        for seed in seeds
    ]
    return _read_json(directory / "seed_ledger.json") == expected


def _recompute_panel(
    directory: Path,
    seeds: Sequence[_Seed],
    truth: Mapping[str, Any],
    work_ok: bool,
    seed_ledger_ok: bool,
) -> tuple[dict[str, bool], dict[str, Any], dict[int, tuple[float, ...]], dict[int, str]]:
    raw_dir = directory / "latent_truth"
    raw_paths = {raw_dir / f"{row.process}.json" for row in seeds}
    table_paths = {directory / f"{row.process}.json" for row in seeds}
    complete = raw_paths == set(raw_dir.glob("*.json")) and table_paths == {
        path for path in directory.glob("*.json") if path.stem.isdecimal()
    }
    try:
        provenance_rows = _read_json(directory / "target_provenance.json")
        provenance_by_seed = {record["process_seed"]: record for record in provenance_rows}
        provenance = seed_ledger_ok and [record["process_seed"] for record in provenance_rows] == [
            row.process for row in seeds
        ]
    except (OSError, KeyError, TypeError, ValueError):
        provenance = False
        provenance_by_seed = {}
    targets = {}
    target_hashes = {}
    failures = {}
    p2 = p3 = complete
    if complete:
        for row in seeds:
            seed = row.process
            table_path = directory / f"{seed}.json"
            table = _read_json(table_path)
            raw = _read_json(raw_dir / f"{seed}.json")
            record = provenance_by_seed.get(seed, {})
            latent_days = raw.get("daily_epidemic")
            observed_days = raw.get("daily_observed_cases")
            complete &= (
                isinstance(latent_days, list)
                and len(latent_days) == LATENT_DAYS
                and record.get("returned_run_config", {}).get("duration_days") == LATENT_DAYS
                and table.get("dates") == list(DATES)
                and isinstance(observed_days, list)
                and tuple(day.get("date") for day in observed_days) == DATES
            )
            if not latent_days:
                # An absent state series provides no conservation evidence.
                p3 = False
                continue
            rebuilt, conditions = _p2_and_p3(raw)
            target_hashes[seed] = _file_digest(table_path)
            targets[seed] = _roots(table)
            provenance &= (
                table == rebuilt
                and target_hashes[seed] == table_sha256(table)
                and raw["benchmark"]["n_agents"] == 3000
                and provenance_matches(
                    record,
                    truth,
                    library=None,
                    batch=None,
                    position=row.position,
                    process_seed=seed,
                    observation_seed=row.observation,
                    hashes=row.hashes,
                    dates=DATES,
                    table=table,
                )
            )
            p2 &= all(tuple(conditions.values())[:5])
            p3 &= all(tuple(conditions.values())[5:])
            failed = [condition for condition, passed in conditions.items() if not passed]
            if failed:
                failures[str(seed)] = failed
    return (
        {
            "P1": complete,
            "P2": p2,
            "P3": p3,
            "P9": provenance,
            "P10": work_ok,
        },
        failures,
        targets,
        target_hashes,
    )


def _check_frozen_inputs(directory: Path) -> str:
    frozen = directory / "frozen_inputs"
    if _read_json(frozen / "sha256.json") != FROZEN_INPUT_SHA256:
        raise BundleError("frozen-input digest index differs from the independently pinned values")
    for name, digest in FROZEN_INPUT_SHA256.items():
        if _file_digest(frozen / name) != digest:
            raise BundleError(f"frozen-input digest mismatch: {name}")
    return (frozen / PREDECLARATION).read_text(encoding="utf-8")


def _validate_void_summary(directory: Path, summary: Mapping[str, Any]) -> dict[str, Any]:
    cause = summary.get("cause")
    expected = _void(cause) if isinstance(cause, str) and cause else None
    outputs = {
        "class",
        "reading",
        "scientific_status",
        "reference_sentences",
        "k",
        "k_prime",
        "m",
        "m_by_library",
        "verdicts",
        "s1",
        "s2",
    }
    if (
        expected is None
        or summary.get("status_phrase") != expected["status_phrase"]
        or outputs.intersection(summary)
        or (directory / "g43_across_library.json").exists()
    ):
        raise BundleError("invalid VOID status, cause or scientific output")
    return expected


def recompute_bundle(directory: Path) -> dict[str, Any]:
    """Recompute results without reading campaign descriptives or conclusion files."""
    verify_bundle(directory)
    summary = _read_json(directory / "campaign_summary.json")
    if summary["software_status"] == "VOID":
        return _validate_void_summary(directory, summary)
    if summary["software_status"] != "PASS":
        raise BundleError("unknown software status")

    text = _check_frozen_inputs(directory)
    dimensions, seeds, (shared_caps, library_caps, total_caps) = _declaration_controls(text)
    work = summary["measured_work"]
    panel, failed_targets, targets, target_hashes = _recompute_panel(
        directory / "targets",
        [row for row in seeds if row.library is None],
        _cell_payload([spec.truth for spec in dimensions]),
        _work_matches(work["shared_panel"], shared_caps),
        _verify_seed_ledger(directory, seeds),
    )
    failed_integrity = [f"shared panel {key}" for key in ("P1", "P9", "P10") if not panel[key]]
    if not _work_matches(work["totals"], total_caps):
        failed_integrity.append("total P10")
    if failed_integrity:
        return _void(", ".join(failed_integrity))

    cells = [_cell_payload(values) for values in product(*(spec.grid for spec in dimensions))]
    libraries, references = {}, {}
    for number in range(1, 7):
        integrity, evaluations = _recompute_library(
            directory / f"library_{number}",
            number,
            seeds,
            cells,
            targets,
            target_hashes,
            dimensions,
            _work_matches(work["libraries"][f"L{number}"], library_caps),
        )
        failed = [f"L{number} {key}" for key, passed in integrity.items() if not passed]
        if failed:
            failed_integrity.extend(failed)
            continue
        gate = evaluations.pop("all_twelve")
        nonrecovery_ok = all(panel.values()) and all(integrity.values())
        recovery_met = all(gate["recovery"].values())
        libraries[str(number)] = {
            "predicates": {**panel, **gate["recovery"]},
            "groups": {
                "shared_panel": panel,
                "library_integrity": integrity,
                "recovery": gate["recovery"],
            },
            "nonrecovery_ok": nonrecovery_ok,
            "recovery_met": recovery_met,
            "scientific_status": "PASS" if nonrecovery_ok and recovery_met else "FAIL",
            **{name: value for name, value in gate.items() if name != "recovery"},
        }
        references[str(number)] = {
            view: {
                "replicates": VIEWS[view].stop - VIEWS[view].start,
                **{
                    key: ref[key]
                    for key in ("hits", "joint_hits", "boundary_counts", "mean_bias", "tie_count")
                },
                "criteria_4_to_8_met": all(ref["recovery"].values()),
                "label": "descriptive_not_a_gate",
            }
            for view, ref in evaluations.items()
        }
    if failed_integrity:
        return _void(", ".join(failed_integrity))
    verdicts = {number: lib["scientific_status"] for number, lib in libraries.items()}
    k = sum(value == "PASS" for value in verdicts.values())
    k_prime = sum(lib["recovery_met"] for lib in libraries.values())
    by_library = {
        number: sum(batch[f"batch{i}"]["criteria_4_to_8_met"] for i in range(1, 5))
        for number, batch in references.items()
    }
    m = sum(by_library.values())
    eligible = panel["P2"] and panel["P3"]
    reading_class = (
        ("CONSISTENT-FAIL" if k == 0 else "CONSISTENT-PASS" if k == 6 else "MIXED")
        if eligible
        else "NO-READING"
    )
    across = {
        "verdicts": verdicts,
        "k": k,
        "k_prime": k_prime,
        "m": m,
        "m_by_library": by_library,
        "libraries_not_met_with_a_batch_met": sum(
            not library["recovery_met"] and by_library[number] > 0
            for number, library in libraries.items()
        ),
        "s1": eligible and m > 0 and 4 * k_prime <= m,
        "s2": eligible and m == 24,
        "class": reading_class,
    }
    if not eligible:
        across["cause"] = {"cause": "shared_panel", "failed_conditions": failed_targets}
    across["reading"] = _render_reading(text, across, libraries)
    return {
        "software_status": "PASS",
        "status_phrase": _STATUS_PREFIX
        + ", ".join(f"L{number} {value}" for number, value in verdicts.items()),
        "across_library": across,
        "libraries": libraries,
        "references": references,
        "reference_sentences": _reference_sentences(text, across),
    }


def _verify_report(directory: Path, result: Mapping[str, Any]) -> None:
    summary = _read_json(directory / "campaign_summary.json")
    across = result["across_library"]
    common = {
        "scientific_status": across["verdicts"],
        "class": across["class"],
        "reading": across["reading"],
        "reference_sentences": result["reference_sentences"],
        "status_phrase": result["status_phrase"],
    }
    if _read_json(directory / "g43_across_library.json") != across or any(
        summary[key] != value for key, value in common.items()
    ):
        raise BundleError("recomputed across-library results differ from retained results")
    for number, library in result["libraries"].items():
        path = directory / f"library_{number}"
        retained = _read_json(path / "recovery_evaluation.json")
        refs = _read_json(path / "reference_evaluations.json")
        if any(retained[key] != value for key, value in library.items()) or (
            refs["evaluations"] != result["references"][number]
            or refs["m_library"] != across["m_by_library"][number]
        ):
            raise BundleError(f"recomputed L{number} evaluations differ from retained results")
    targets = directory / "targets"
    diagnostics = _read_json(targets / "truth_diagnostics.json")
    for path in sorted((targets / "latent_truth").glob("*.json")):
        raw = _read_json(path)
        _, conditions = _p2_and_p3(raw)
        reported_p3 = {
            "natural_history.chronology_passed": raw["natural_history"]["chronology_passed"],
            "states.conserved": raw["states"]["conserved"],
            "no_report_before_infection": raw["observation_diagnostics"][
                "no_report_before_infection"
            ],
            "latent_incidence_conservation": raw["observation_diagnostics"][
                "latent_incidence_conservation"
            ],
        }
        if diagnostics[path.stem]["conditions"] != conditions or any(
            conditions[name] is not flag for name, flag in reported_p3.items()
        ):
            raise BundleError(f"recomputed target conditions differ for {path.stem}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args(argv)
    try:
        result = recompute_bundle(args.bundle)
        if result["software_status"] != "VOID":
            _verify_report(args.bundle, result)
    except (BundleError, OSError, KeyError, TypeError, ValueError) as exc:
        print(f"G43 recomputation discrepancy: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
