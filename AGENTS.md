# Purpose

Use the minimal sufficient solution. Prohibit over-engineering. Aggressive planning is acceptable; execution should remain lightweight. Every design must prove its necessity for the current task.

# Intent-First Workflow

Before editing:

- Understand the task and relevant code; do not modify code and guess intent afterward.
- State the goal, non-goals, acceptance criteria, and areas explicitly not to change.
- Prefer a root-cause fix over compatibility layers, patch accumulation, or a second implementation.
- Stop when the acceptance criteria are satisfied.

# Reasoning Discipline

Use the least expensive reasoning level sufficient for correctness.

- Requirement interpretation, architecture, scientific semantics, lifecycle ordering, concurrency, provenance, persistent state, identity, and difficult debugging may require stronger reasoning.
- Mechanical implementation, repetitive edits, formatting, routine refactors, and ordinary test execution should use lighter reasoning where available.
- Do not keep maximum reasoning enabled merely because it is available.
- If implementation begins expanding scope or architecture, stop and reconsider the plan rather than spending more reasoning on an unnecessarily larger design.

# Agents and Parallelism

Do not default to spinning up multiple agents. Solve a task in one coherent thread unless decomposition has a clear, concrete benefit. Use parallelism only when it improves the work without fragmenting ownership or reasoning.

# Repository Integrity

This repository may contain previously verified scientific, execution, data, artifact, lifecycle, identity, or provenance contracts.

Before changing an existing subsystem:

1. Read the relevant implementation and current architecture or progress documentation.
2. Identify which existing contracts the task is explicitly allowed to change.
3. Treat all other verified contracts as protected.
4. Do not alter scientific semantics, hashes, artifact schemas, lifecycle ordering, identity rules, persistence rules, or provenance contracts merely to simplify implementation.
5. If satisfying the task requires breaking a protected contract, stop and report the conflict before implementing it.
6. For a corrective milestone, add regression coverage for the exact historical failure being closed, without expanding into unrelated historical coverage.

# Testing

Testing must be proportional to the risk and behavior changed.

1. Run existing tests relevant to the change first.
2. Add tests only when existing tests cannot demonstrate an acceptance criterion or prevent a reproduced regression.
3. Tie every new test to a concrete requirement, invariant, or observed failure.
4. Prefer the smallest deterministic fixture that proves the behavior.
5. Do not add unrelated coverage, frameworks, snapshots, dependencies, or test infrastructure.
6. Do not use test expansion to justify new abstractions.
7. Scientific, lifecycle, identity, provenance, persistence, concurrency, artifact-integrity, and similar high-risk changes may require multiple adversarial tests when one fixture cannot prove the contract.
8. Treat a green test suite as evidence, not proof; inspect material implementation logic before declaring completion.
9. Do not fill unrelated historical coverage gaps during a bounded task.

Before adding a test, answer:

- Which acceptance criterion, invariant, or reproduced failure does it verify?
- Would existing tests detect this regression without it?
- Is it the smallest deterministic fixture that proves the requirement?

Do not delete tests merely because test code is longer than implementation code.

# Failure Modes

Avoid:

- Fixing the surface instead of understanding intent.
- Piling patches on top of patches or adding dual implementations.
- Adding unnecessary compatibility layers or speculative architecture.
- Guessing or searching instead of reading relevant code.
- Using tests to justify scope expansion.
- Accidentally changing a verified contract while fixing a nearby issue.
- Treating passing tests as sufficient proof without inspecting the implementation.
- Implementing around a symptom instead of repairing the authoritative state or lifecycle path.

# Git and Destructive Operations

- Read-only Git operations are always permitted.
- Creating an ordinary branch or commit is permitted unless the task says otherwise.
- Do not perform destructive Git operations such as hard reset, forced checkout, branch deletion, history rewriting, or discarding uncommitted changes unless explicitly instructed.
- Before any operation that could destroy uncommitted or otherwise difficult-to-recover work, stop and obtain explicit user approval.
- Never assume a clean or reset state merely because a task prompt names a base commit; inspect the worktree first.

# Stop Conditions

Stop and reconsider if you start:

- Adding abstractions not required by the current task.
- Designing for hypothetical future use.
- Adding another framework or configuration layer.
- Modifying unrelated files.
- Creating a second implementation for old logic.
- Expanding a bounded fix into a platform rewrite.

A new abstraction is allowed when it is the smallest root-cause fix for duplicated authoritative logic, inconsistent lifecycle behavior, or a verified correctness defect. Justify the necessity.

# Pre-Completion Checklist

- Restate the intent and acceptance criteria.
- Identify protected contracts.
- Change the minimal files.
- Inspect material implementation logic directly.
- Run relevant tests.
- Tie new tests to concrete acceptance criteria or regressions.
- Confirm there is no unrelated scope expansion.
- Confirm no destructive Git work was performed unintentionally.
- Remove debug leftovers.
- Ensure documentation and status claims match actual verification.
- Stop once the acceptance criteria pass.

# General Principles

Understand intent first. Make the smallest root-cause change. Preserve protected contracts. Verify in proportion to risk. Do not build speculative architecture. Stop when acceptance criteria are satisfied.
