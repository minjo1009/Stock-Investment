# Lean Implementation Discipline

## Purpose

This operating note adapts the Ponytail lesson for this project: write only
what the task needs, but do not weaken validation, source discipline, security,
accessibility, or project status boundaries.

Reference source:

- `https://github.com/DietrichGebert/ponytail`
- `https://github.com/DietrichGebert/ponytail/blob/main/benchmarks/results/2026-06-18-agentic.md`

## Core Rule

Be lazy about the solution, not about understanding.

Before choosing an implementation, read the files that the change actually
touches and trace the relevant flow. Then stop at the first safe rung:

1. Does this need to exist? If not, skip it.
2. Is it already in this codebase? Reuse it.
3. Does the standard library, shell, SQL, browser, or native platform already
   do it? Use that.
4. Does an installed dependency already solve it? Use the existing dependency.
5. Can a one-line or local edit solve it? Keep it local.
6. Only then add the smallest new implementation that works.

## Project-Specific Application

- Do not add a new framework, package, scheduler, DB table, replay path, or
  abstraction unless the request truly needs it.
- Prefer existing validators, manifests, reports, and registry patterns over
  new governance formats.
- Prefer local helpers already used in the touched area over new generic
  helpers.
- Prefer deletion, configuration removal, or documentation of an existing path
  when that fully solves the task.
- Add an abstraction only when it removes real complexity or matches an
  established local pattern.
- Keep changes in the smallest owner lane that can solve the request.

## Never Cut

The lean path may not remove or soften:

- source provenance and as-of discipline
- missing-source reporting
- no inferred lifecycle matching
- no symbol/date/price/time proximity fallback
- outcome, PnL, and label leakage boundaries
- validation authority wording
- security, secret masking, and data-loss protection
- accessibility and user-visible readability
- strategy acceptance, deployment readiness, broker-truth, paper/live, and
  real-capital boundaries

## Pre-Edit Checklist

Before implementation, state or verify:

- Objective: what user-visible problem is being solved.
- Assumption: why a smaller path is enough.
- Reuse check: what existing code, docs, validators, platform features, or
  dependencies were considered.
- Validation authority: which lane can verify the change, and what a pass does
  not mean.

## Review Checklist

Before closeout, ask:

- Did this add code where deleting, reusing, or documenting existing behavior
  would have worked?
- Did this create a new abstraction with only one real caller?
- Did this add defensive handling for an unsupported or impossible path?
- Did this introduce a dependency, config, table, route, or scheduler not
  required by the request?
- Did this preserve all project status boundaries?

## Authority

This is an operating discipline document. It can guide implementation choices,
reports, and review comments. It does not validate a trading strategy, approve
deployment, prove broker truth, permit paper/live orders, or permit real
capital.

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
