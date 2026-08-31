"""Adversarial contracts for corrective milestone C5."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from jersey_outbreak.ensemble import run_ensemble
from jersey_outbreak.hashing import canonical_json_bytes, sha256_bytes
from jersey_outbreak.intervention_analysis import compare_intervention_runs
from jersey_outbreak.intervention_artifacts import (
    verify_intervention_artifact,
    write_intervention_artifact,
)
from jersey_outbreak.intervention_schemas import (
    InterventionConfig,
    ScenarioConfig,
    TargetPopulation,
)
from jersey_outbreak.interventions import (
    NON_NURSING_CARE_SETTING_TYPES,
    NURSING_CARE_SETTING_TYPES,
    InterventionManager,
)
from jersey_outbreak.outbreak_runner import run_outbreak


def _scenario(config, intervention, scenario_id="c5-neutral"):
    return ScenarioConfig(
        scenario_id=scenario_id,
        seed=config.seed,
        start_date=config.start_date,
        duration_days=config.duration_days,
        interventions=() if intervention is None else (intervention,),
        sensitivity_config_ids=("baseline",),
    )


def _assert_exact_latent(left, right) -> None:
    assert left.daily_epidemic == right.daily_epidemic
    assert left.daily_route == right.daily_route
    assert left.daily_age == right.daily_age
    assert left.daily_parish == right.daily_parish
    assert left.transmission_events == right.transmission_events
    assert left.latent_outcome_hash == right.latent_outcome_hash
    assert left.logical_content_hash == right.logical_content_hash


def _all_detected(base):
    parameters = {
        key: parameter.model_copy(
            update={
                "value": 1.0
                if key
                in {"symptomatic_detection_probability", "asymptomatic_detection_probability"}
                else parameter.value
            }
        )
        for key, parameter in base.parameters.items()
    }
    fixed = base.reporting_delay.model_copy(update={"kind": "fixed", "days": (0,)})
    return base.model_copy(
        update={
            "observation_config_id": "c5-all-detected",
            "parameters": parameters,
            "detection_delay": fixed,
            "reporting_delay": fixed,
            "day_of_week_effect": (1.0,) * 7,
            "analysis_horizon_tail_days": None,
        }
    )


@pytest.mark.parametrize(
    "intervention",
    [
        InterventionConfig(
            intervention_id="neutral-isolation",
            type="case_isolation",
            duration_days=2,
            adherence=0.0,
        ),
        InterventionConfig(
            intervention_id="neutral-quarantine",
            type="household_quarantine",
            duration_days=2,
            adherence=0.0,
        ),
        InterventionConfig(
            intervention_id="neutral-school",
            type="school_closure",
            start_date=date(2025, 1, 6),
        ),
        InterventionConfig(
            intervention_id="neutral-wfh",
            type="workplace_reduction",
            start_date=date(2025, 1, 6),
            adherence=1.0,
            workplace_multiplier=1.0,
            commute_multiplier=1.0,
            additional_wfh_fraction=0.0,
        ),
        InterventionConfig(
            intervention_id="neutral-community",
            type="community_reduction",
            start_date=date(2025, 1, 6),
        ),
        InterventionConfig(
            intervention_id="neutral-care",
            type="care_home_protection",
            start_date=date(2025, 1, 6),
        ),
        InterventionConfig(
            intervention_id="neutral-vaccine-coverage",
            type="vaccination",
            start_date=date(2025, 1, 6),
            coverage_target=0.0,
            efficacy_susceptibility=1.0,
        ),
        InterventionConfig(
            intervention_id="neutral-vaccine-efficacy",
            type="vaccination",
            start_date=date(2025, 1, 6),
            coverage_target=1.0,
            efficacy_susceptibility=0.0,
            efficacy_infectiousness=0.0,
        ),
        InterventionConfig(
            intervention_id="neutral-mask-experimental",
            type="masking",
            start_date=date(2025, 1, 6),
            route_effects={"community_indoor": 1.0},
        ),
        InterventionConfig(
            intervention_id="neutral-gathering-experimental",
            type="gathering_reduction",
            start_date=date(2025, 1, 6),
            route_effects={"community_indoor": 1.0},
        ),
    ],
    ids=lambda item: item.intervention_id,
)
def test_each_neutral_family_is_exact_under_nonzero_beta(
    m6_network, m6_parameters, m6_base_config, m6_observation_config, intervention
) -> None:
    config = m6_base_config.model_copy(
        update={"beta": 0.35, "duration_days": 4, "initial_seed_count": 8}
    )
    observation = (
        m6_observation_config
        if intervention.type in {"case_isolation", "household_quarantine"}
        else None
    )
    baseline = run_outbreak(m6_network, config, m6_parameters, observation_config=observation)
    attached = run_outbreak(
        m6_network,
        config,
        m6_parameters,
        observation_config=observation,
        scenario=_scenario(config, intervention, intervention.intervention_id),
    )
    _assert_exact_latent(attached, baseline)
    assert all(
        row["representation"] == "canonical_reused" for row in attached.intervention_route_effects
    )


def test_empty_manager_is_instantiated_and_exact(m6_network, m6_parameters, m6_base_config) -> None:
    config = m6_base_config.model_copy(
        update={"beta": 0.35, "duration_days": 4, "initial_seed_count": 8}
    )
    baseline = run_outbreak(m6_network, config, m6_parameters)
    attached = run_outbreak(
        m6_network,
        config,
        m6_parameters,
        scenario=_scenario(config, None, "empty-manager"),
    )
    _assert_exact_latent(attached, baseline)
    assert attached.intervention_diagnostics["attached"] is True
    assert attached.intervention_diagnostics["intervention_ids"] == []
    assert attached.intervention_route_effects


def test_calendar_horizon_is_number_of_dated_points(
    m6_network, m6_parameters, m6_base_config
) -> None:
    config = m6_base_config.model_copy(
        update={"start_date": date(2025, 1, 6), "duration_days": 4, "beta": 0.0}
    )
    default_end = InterventionConfig(
        intervention_id="default-end",
        type="community_reduction",
        start_date=date(2025, 1, 7),
        indoor_multiplier=0.5,
    )
    one_day = InterventionConfig(
        intervention_id="one-day",
        type="school_closure",
        start_date=date(2025, 1, 7),
        end_date=date(2025, 1, 7),
        class_multiplier=0.0,
    )
    scenario = ScenarioConfig(
        scenario_id="calendar-boundaries",
        start_date=config.start_date,
        duration_days=config.duration_days,
        interventions=(default_end, one_day),
    )
    result = run_outbreak(m6_network, config, m6_parameters, scenario=scenario)
    assert [row["date"] for row in result.daily_epidemic] == [
        "2025-01-06",
        "2025-01-07",
        "2025-01-08",
        "2025-01-09",
    ]
    states = {(row["intervention_id"], row["date"]): row for row in result.intervention_state}
    assert states[("default-end", "2025-01-09")]["route_intervention_active"] is True
    assert states[("one-day", "2025-01-07")]["route_intervention_active"] is True
    assert states[("one-day", "2025-01-08")]["route_intervention_active"] is False


@pytest.mark.parametrize(
    ("family", "start_action", "release_action", "state_key"),
    [
        ("case_isolation", "agent_entered_isolation", "agent_left_isolation", "active_agents"),
        (
            "household_quarantine",
            "household_entered_quarantine",
            "household_released",
            "active_households",
        ),
    ],
)
def test_detection_state_events_reconcile_and_release(
    m6_network,
    m6_parameters,
    m6_base_config,
    m6_observation_config,
    family,
    start_action,
    release_action,
    state_key,
) -> None:
    config = m6_base_config.model_copy(
        update={"duration_days": 5, "beta": 0.0, "initial_seed_count": 3}
    )
    intervention = InterventionConfig(
        intervention_id=family,
        type=family,
        duration_days=2,
        adherence=1.0,
    )
    result = run_outbreak(
        m6_network,
        config,
        m6_parameters,
        observation_config=_all_detected(m6_observation_config),
        scenario=_scenario(config, intervention, f"reconcile-{family}"),
    )
    events = [event for event in result.intervention_events if event["intervention_id"] == family]
    assert any(event["action"] == start_action for event in events)
    assert any(event["action"] == release_action for event in events)
    rows = [row for row in result.intervention_state if row["intervention_id"] == family]
    for previous, current in zip(rows, rows[1:], strict=False):
        if family == "case_isolation":
            assert current[state_key] == (
                previous[state_key] + current["new_activations"] - current["new_releases"]
            )
        else:
            # Household state reconciles in household units; member burden is
            # separately exposed as active_agents.
            assert current[state_key] == (
                previous[state_key] + current["new_activations"] - current["new_releases"]
            )


@pytest.mark.parametrize("family", ["case_isolation", "household_quarantine"])
def test_repeated_detection_extends_state_and_releases_at_maximum_end(m6_network, family) -> None:
    config = InterventionConfig(
        intervention_id=family,
        type=family,
        duration_days=3,
        adherence=1.0,
    )
    manager = InterventionManager(
        m6_network,
        (config,),
        run_seed=123,
        start_date=date(2025, 1, 6),
        duration_days=8,
    )
    manager.setattribute("sim", SimpleNamespace(t=SimpleNamespace(now=lambda _kind: "2025-01-08")))
    if family == "case_isolation":
        agent_id = m6_network.agent_ids[0]
        manager._isolation_until[family] = np.full(len(m6_network.agent_ids), -1, dtype=np.int64)
    else:
        agent_id = next(
            row["agent_id"]
            for row in m6_network.m2_input.residents
            if row.get("household_id") is not None
        )
        manager._quarantine_until[family] = {}
    uid = manager._uid_by_agent_id[agent_id]
    event = SimpleNamespace(
        agent_id=agent_id,
        agent_uid=uid,
        detection_date="2025-01-06",
        detection_reason="controlled-repeat",
        detection_time_index=0,
    )
    manager._pending_detection_actions = [(1, family, event), (2, family, event)]
    manager._apply_detection_actions(1)
    manager._apply_detection_actions(2)
    assert manager.event_log[-1]["action"] in {"isolation_extended", "quarantine_extended"}
    if family == "case_isolation":
        assert manager._isolation_until[family][uid] == 5
    else:
        household_id = str(manager._m2_by_agent[agent_id]["household_id"])
        assert manager._quarantine_until[family][household_id] == 5
    manager._release_detection_states(5)
    assert manager.event_log[-1]["action"] in {"agent_left_isolation", "household_released"}


def test_care_target_truth_table_excludes_every_other_communal_type(m6_network) -> None:
    types = {row["setting_type"] for row in m6_network.m2_input.communal_settings}
    manager = InterventionManager(
        m6_network, (), run_seed=123, start_date=date(2025, 1, 6), duration_days=1
    )
    expected = {
        "nursing": set(NURSING_CARE_SETTING_TYPES),
        "non_nursing": set(NON_NURSING_CARE_SETTING_TYPES),
        "both": set(NURSING_CARE_SETTING_TYPES | NON_NURSING_CARE_SETTING_TYPES),
    }
    for target, allowed in expected.items():
        intervention = InterventionConfig(
            intervention_id=f"care-{target}",
            type="care_home_protection",
            start_date=date(2025, 1, 6),
            care_target=target,
        )
        for setting_id, setting_type in manager._care_type_by_setting.items():
            assert manager._care_target_matches_setting(intervention, setting_id) is (
                setting_type in allowed
            )
    assert types - expected["both"]


def test_modifier_order_is_exactly_canonical(m6_network, m6_parameters, m6_base_config) -> None:
    config = m6_base_config.model_copy(
        update={"beta": 0.35, "duration_days": 4, "initial_seed_count": 8}
    )
    items = tuple(
        InterventionConfig(
            intervention_id=intervention_id,
            type="masking",
            start_date=config.start_date,
            route_effects={"community_indoor": multiplier},
        )
        for intervention_id, multiplier in (("a", 0.1), ("b", 0.2), ("c", 0.3))
    )
    first_scenario = ScenarioConfig(
        scenario_id="composition", interventions=items, start_date=config.start_date
    )
    reverse_scenario = ScenarioConfig(
        scenario_id="composition",
        interventions=tuple(reversed(items)),
        start_date=config.start_date,
    )
    first = run_outbreak(m6_network, config, m6_parameters, scenario=first_scenario)
    reverse = run_outbreak(m6_network, config, m6_parameters, scenario=reverse_scenario)
    _assert_exact_latent(first, reverse)
    assert first.scenario_hash == reverse.scenario_hash
    assert first.intervention_route_effects == reverse.intervention_route_effects


def test_zero_school_and_community_multipliers_remove_active_route_attribution(
    m6_network, m6_parameters, m6_base_config
) -> None:
    config = m6_base_config.model_copy(
        update={"beta": 0.6, "duration_days": 4, "initial_seed_count": 20}
    )
    scenario = ScenarioConfig(
        scenario_id="zero-routes",
        start_date=config.start_date,
        duration_days=config.duration_days,
        interventions=(
            InterventionConfig(
                intervention_id="school-zero",
                type="school_closure",
                start_date=config.start_date,
                class_multiplier=0.0,
                cross_class_multiplier=0.0,
            ),
            InterventionConfig(
                intervention_id="community-zero",
                type="community_reduction",
                start_date=config.start_date,
                indoor_multiplier=0.0,
                outdoor_multiplier=0.0,
            ),
        ),
    )
    result = run_outbreak(m6_network, config, m6_parameters, scenario=scenario)
    suppressed = {
        "school_class",
        "school_cross_class",
        "community_indoor",
        "community_outdoor",
    }
    assert not any(event["route_id"] in suppressed for event in result.transmission_events)
    assert all(
        row["effective_edge_count"] == 0
        for row in result.intervention_route_effects
        if row["route_id"] in suppressed
    )


def test_full_run_identity_mutations_change_hash(m6_base_config) -> None:
    base_intervention = InterventionConfig(
        intervention_id="isolation", type="case_isolation", duration_days=3, adherence=0.5
    )
    base_scenario = ScenarioConfig(scenario_id="identity", interventions=(base_intervention,))

    def identity(run_config, scenario=base_scenario):
        return scenario.run_hash(
            disease_config_hash="d" * 64,
            network_hash="4" * 64,
            observation_config_hash="o" * 64,
            seed=run_config.seed,
            start_date=run_config.start_date,
            duration_days=run_config.duration_days,
            run_config_hash=sha256_bytes(canonical_json_bytes(run_config.model_dump(mode="json"))),
            m2_hash="2" * 64,
            m3_hash="3" * 64,
            jos_model_versions={"m5": "5.0.0", "m7": "7.0.0"},
        )

    baseline = identity(m6_base_config)
    mutations = [
        m6_base_config.model_copy(update={"beta": 0.12}),
        m6_base_config.model_copy(update={"seed": 999}),
        m6_base_config.model_copy(update={"duration_days": 9}),
        m6_base_config.model_copy(update={"start_date": date(2025, 2, 1)}),
        m6_base_config.model_copy(update={"import_schedule": {"2025-01-07": 2}}),
    ]
    assert all(identity(item) != baseline for item in mutations)
    changed_scenarios = [
        ScenarioConfig(
            scenario_id="identity",
            interventions=(base_intervention.model_copy(update={"adherence": 0.6}),),
        ),
        ScenarioConfig(
            scenario_id="identity",
            interventions=(
                InterventionConfig(
                    intervention_id="community",
                    type="community_reduction",
                    start_date=date(2025, 1, 6),
                    indoor_multiplier=0.8,
                ),
            ),
        ),
        ScenarioConfig(
            scenario_id="identity",
            interventions=(
                InterventionConfig(
                    intervention_id="vaccine",
                    type="vaccination",
                    start_date=date(2025, 1, 6),
                    efficacy_susceptibility=0.7,
                ),
            ),
        ),
    ]
    assert all(identity(m6_base_config, item) != baseline for item in changed_scenarios)


def test_import_attempts_are_not_backfilled_after_protection(
    m6_network, m6_parameters, m6_base_config
) -> None:
    config = m6_base_config.model_copy(
        update={
            "duration_days": 2,
            "beta": 0.0,
            "initial_seed_count": 0,
            "import_schedule": {"2025-01-06": 20},
        }
    )
    baseline = run_outbreak(m6_network, config, m6_parameters)

    def protected(efficacy, campaign_id):
        return run_outbreak(
            m6_network,
            config,
            m6_parameters,
            scenario=_scenario(
                config,
                InterventionConfig(
                    intervention_id=campaign_id,
                    type="vaccination",
                    start_date=config.start_date,
                    rollout_rate=1.0,
                    coverage_target=1.0,
                    uptake_probability=1.0,
                    efficacy_susceptibility=efficacy,
                ),
                f"import-{campaign_id}",
            ),
        )

    partial = protected(0.5, "partial-protection")
    full = protected(1.0, "full-protection")
    assert baseline.diagnostics["imports"]["realized_exposure_attempts"] == 20
    assert full.diagnostics["imports"]["realized_exposure_attempts"] == 20
    assert baseline.diagnostics["imports"]["realized_imports"] == 20
    assert 0 < partial.diagnostics["imports"]["realized_imports"] < 20
    assert full.diagnostics["imports"]["realized_imports"] == 0


def test_wfh_and_vaccination_family_metrics_reconcile(
    m6_network, m6_parameters, m6_base_config
) -> None:
    config = m6_base_config.model_copy(
        update={"duration_days": 5, "beta": 0.0, "initial_seed_count": 0}
    )
    wfh = InterventionConfig(
        intervention_id="wfh-one-day",
        type="workplace_reduction",
        start_date=config.start_date,
        end_date=config.start_date,
        target=TargetPopulation(worker_only=True),
        additional_wfh_fraction=1.0,
    )
    vaccine = InterventionConfig(
        intervention_id="vaccine-metrics",
        type="vaccination",
        start_date=config.start_date,
        rollout_rate=0.25,
        coverage_target=0.5,
        uptake_probability=1.0,
        protection_delay_days=1,
        efficacy_susceptibility=1.0,
        waning_days=3,
    )
    result = run_outbreak(
        m6_network,
        config,
        m6_parameters,
        scenario=ScenarioConfig(
            scenario_id="family-metrics",
            start_date=config.start_date,
            duration_days=config.duration_days,
            interventions=(wfh, vaccine),
        ),
    )
    wfh_rows = [row for row in result.intervention_state if row["intervention_id"] == "wfh-one-day"]
    assert wfh_rows[0]["active_agents"] == wfh_rows[0]["new_wfh_entries"]
    assert wfh_rows[0]["new_activations"] == wfh_rows[0]["new_wfh_entries"]
    assert wfh_rows[1]["active_agents"] == 0
    assert wfh_rows[1]["wfh_exits"] == wfh_rows[0]["active_agents"]
    assert wfh_rows[1]["new_releases"] == wfh_rows[1]["wfh_exits"]

    vaccine_rows = [
        row for row in result.intervention_state if row["intervention_id"] == "vaccine-metrics"
    ]
    assert all(row["doses_administered"] == row["newly_vaccinated"] for row in vaccine_rows)
    assert all(row["new_activations"] == row["doses_administered"] for row in vaccine_rows)
    assert any(row["protection_became_effective"] for row in vaccine_rows)
    assert any(row["protection_waned"] for row in vaccine_rows)
    for previous, current in zip(vaccine_rows, vaccine_rows[1:], strict=False):
        assert current["currently_protected"] == (
            previous["currently_protected"]
            + current["protection_became_effective"]
            - current["protection_waned"]
        )


def test_vaccine_acceptance_is_stable_and_seeded(m6_network) -> None:
    campaign = InterventionConfig(
        intervention_id="stable-campaign",
        type="vaccination",
        start_date=date(2025, 1, 6),
        uptake_probability=0.5,
    )
    first = InterventionManager(
        m6_network, (campaign,), run_seed=123, start_date=date(2025, 1, 6), duration_days=3
    )
    same = InterventionManager(
        m6_network, (campaign,), run_seed=123, start_date=date(2025, 1, 6), duration_days=3
    )
    changed = InterventionManager(
        m6_network, (campaign,), run_seed=999, start_date=date(2025, 1, 6), duration_days=3
    )
    ids = m6_network.agent_ids
    accepted = [first._vaccine_accepts(campaign, agent_id) for agent_id in ids]
    assert accepted == [same._vaccine_accepts(campaign, agent_id) for agent_id in ids]
    assert accepted != [changed._vaccine_accepts(campaign, agent_id) for agent_id in ids]
    decliner = next(agent_id for agent_id in ids if not first._vaccine_accepts(campaign, agent_id))
    assert all(not first._vaccine_accepts(campaign, decliner) for _ in range(3))


def test_wfh_targeting_is_job_aware_for_multijob_worker(m6_network) -> None:
    manager = InterventionManager(
        m6_network, (), run_seed=123, start_date=date(2025, 1, 6), duration_days=1
    )
    workers_by_workplace = {
        workplace: {
            agent_id
            for agent_id, jobs in manager._jobs_by_agent.items()
            for job in jobs
            if job["workplace_id"] == workplace
        }
        for workplace in {
            job["workplace_id"] for jobs in manager._jobs_by_agent.values() for job in jobs
        }
    }
    agent_id, jobs, primary, secondary = next(
        (agent_id, jobs, primary, secondary)
        for agent_id, jobs in manager._jobs_by_agent.items()
        if len(jobs) > 1
        for primary in [next(job for job in jobs if job["job_role"] == "primary")]
        for secondary in [next((job for job in jobs if job["sector"] != primary["sector"]), None)]
        if secondary is not None
        and workers_by_workplace[primary["workplace_id"]]
        - workers_by_workplace[secondary["workplace_id"]]
        - {agent_id}
        and workers_by_workplace[secondary["workplace_id"]] - {agent_id}
    )
    intervention = InterventionConfig(
        intervention_id="secondary-only",
        type="workplace_reduction",
        start_date=date(2025, 1, 6),
        target=TargetPopulation(employment_sectors=(secondary["sector"],)),
        additional_wfh_fraction=1.0,
    )
    targeted = manager._targeted_jobs(intervention, agent_id)
    assert secondary in targeted
    assert primary not in targeted
    assert manager._commute_agent_targeted(intervention, agent_id) is False
    primary_colleague = next(
        iter(
            workers_by_workplace[primary["workplace_id"]]
            - workers_by_workplace[secondary["workplace_id"]]
            - {agent_id}
        )
    )
    secondary_colleague = next(iter(workers_by_workplace[secondary["workplace_id"]] - {agent_id}))
    assert (
        manager._edge_multiplier(
            intervention,
            "workplace_team",
            agent_id,
            primary_colleague,
            date(2025, 1, 6),
            0,
        )
        == 1.0
    )
    assert (
        manager._edge_multiplier(
            intervention,
            "workplace_team",
            agent_id,
            secondary_colleague,
            date(2025, 1, 6),
            0,
        )
        == 1.0
    )

    suppress_targeted_job = intervention.model_copy(update={"workplace_multiplier": 0.0})
    assert (
        manager._edge_multiplier(
            suppress_targeted_job,
            "workplace_team",
            agent_id,
            primary_colleague,
            date(2025, 1, 6),
            0,
        )
        == 1.0
    )
    assert (
        manager._edge_multiplier(
            suppress_targeted_job,
            "workplace_team",
            agent_id,
            secondary_colleague,
            date(2025, 1, 6),
            0,
        )
        == 0.0
    )


def test_complete_m7_artifact_verifies_and_rejects_missing_latent_output(
    m6_network, m6_parameters, m6_base_config, tmp_path: Path
) -> None:
    config = m6_base_config.model_copy(update={"duration_days": 2})
    result = run_outbreak(
        m6_network,
        config,
        m6_parameters,
        scenario=_scenario(config, None, "artifact-completeness"),
    )
    artifact = write_intervention_artifact(result, Path.cwd(), tmp_path)
    verified = verify_intervention_artifact(artifact.artifact_directory)
    assert verified.latent_outcome_hash == result.latent_outcome_hash
    assert verified.run_config_hash == result.run_config_hash
    latent_route = next(
        artifact.artifact_directory.glob("latent_outputs/jos-outbreak-m5-*/daily_route.parquet")
    )
    latent_route.unlink()
    with pytest.raises(ValueError, match="incomplete"):
        verify_intervention_artifact(artifact.artifact_directory)


def test_matched_comparison_and_intervention_ensemble_retain_c5_metrics(
    m6_network,
    m6_parameters,
    m6_base_config,
    m6_observation_config,
    tmp_path: Path,
) -> None:
    config = m6_base_config.model_copy(
        update={"duration_days": 2, "beta": 0.2, "initial_seed_count": 4}
    )
    intervention = InterventionConfig(
        intervention_id="ensemble-community",
        type="community_reduction",
        start_date=config.start_date,
        indoor_multiplier=0.5,
    )
    scenario = _scenario(config, intervention, "matched-and-ensemble")
    baseline = run_outbreak(m6_network, config, m6_parameters)
    treated = run_outbreak(m6_network, config, m6_parameters, scenario=scenario)
    comparison = compare_intervention_runs(baseline, treated, comparison_id="c5-matched")
    assert comparison.paired_seed_comparison
    assert {row["seed"] for row in comparison.scenario_comparison} == {config.seed}

    ensemble = run_ensemble(
        tmp_path,
        m6_network,
        m6_parameters,
        config,
        m6_observation_config,
        (123,),
        ensemble_id="c5-intervention-metrics",
        scenario=scenario,
    )
    metrics = {
        row["metric"]
        for row in ensemble.replicate_trajectories[123]
        if row["scope"] == "intervention"
    }
    assert {
        "intervention_route_active",
        "intervention_affected_routes",
        "intervention_new_activations",
        "intervention_new_releases",
    } <= metrics
    assert ensemble.replicate_records[0].scenario_hash is not None
    assert ensemble.scenario_hash is not None
    assert ensemble.diagnostics["replicate_scenario_run_hashes"]["123"] == (
        ensemble.replicate_records[0].scenario_hash
    )
