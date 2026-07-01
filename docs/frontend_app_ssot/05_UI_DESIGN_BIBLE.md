# Project UI Design Bible

## Authority And Boundary

This document is a permanent UI quality reference for the read-only Trader Brain frontend. It adapts reusable UI/UX knowledge from UI-UX-Pro-Max into this project's existing frontend SSOT.

This document is a frontend design reference only. It does not grant strategy acceptance, deployment readiness, paper/live permission, broker mutation, or real-capital permission.

It does not replace Product Mission, Information Architecture, Navigation Flow, Universal Investigation Framework, Candidate Lifecycle, Detail Screen Architecture, Screen Map, Wireframe Architecture, Design System, Component Catalog, or Implementation Architecture.

Hard boundaries:

- Keep top-level navigation as `HOME`, `BRAIN`, `PORTFOLIO`, `ORDERS`, `SYSTEM`.
- Keep `Decision -> Reasoning/Thesis -> Evidence -> Source`.
- Keep missing, stale, unknown, blocked, and source-not-attached states visible.
- Keep the frontend read-only unless a future operating document explicitly changes permission.
- Do not introduce Robinhood, Webull, Toss Securities, retail brokerage, or chart-first consumer trading architecture.

Target product character:

- Bloomberg Terminal discipline.
- Institutional PM dashboard trust.
- Research workstation evidence depth.
- Trading operating system control clarity.
- Consumer-grade usability without consumer brokerage behavior.

## 1. Visual Hierarchy Rules

Why: Operators must know what requires attention before they admire the interface. In this product, visual quality means faster risk detection and clearer evidence review, not decorative polish.

Rules:

- First attention belongs to decision state, authority, blockers, and freshness.
- Second attention belongs to reason/thesis and evidence strength.
- Third attention belongs to supporting metrics, charts, and provenance.
- Risk, stale source, missing source, and disabled action states must never be visually quiet.
- Above the fold must answer: "What is the state, why does it matter, what is blocked, and where is the evidence?"
- A healthy-looking portfolio or candidate summary must not hide stale, missing, or unknown source states.
- Color can support hierarchy, but text labels must carry the meaning.
- Decorative visual elements must never compete with decision, evidence, source, or blocker information.

What users should notice first:

- HOME: portfolio/system attention queue and blocker state.
- BRAIN: candidate review state, blocked/review-only status, source state.
- PORTFOLIO: broker/local separation, exposure, stale position evidence.
- ORDERS: local state, broker-truth state, mutation-disabled status.
- SYSTEM: governance, source freshness, control state, validator visibility.

What must never compete for attention:

- Decorative gradients, oversized illustrations, marketing language, animated ornaments, chart chrome, and active-looking trading actions.

## 2. Typography Rules

Why: Dense financial screens fail when type hierarchy is random. The user should scan rows quickly and still trust that every label, number, and blocker has a stable meaning.

Rules:

- Use a restrained type scale: display, page title, section title, card title, body, caption, badge/label, numeric value.
- Display type is rare. Use it only for top screen identity or one critical portfolio/account metric.
- Page titles orient; they must not consume the first viewport.
- Section titles describe screen structure and should be smaller than page titles.
- Card titles should be compact and scannable, not hero-sized.
- Body text should be readable on phone: default target 16 pt where possible; never use body text below 14 pt for decision-support copy.
- Captions can carry provenance, timestamps, and source refs, but must remain legible.
- Numeric values should use tabular or stable-width rendering where available to prevent row jitter.
- Truncation is allowed only for long source refs or IDs. Decision, blocker, and disabled-reason copy should wrap before it truncates.
- Do not use tight negative letter spacing. Preserve platform defaults unless a tested token requires otherwise.

## 3. Spacing Rules

Why: Spacing is how operators distinguish priority levels under time pressure. Random spacing makes screens feel untrustworthy even when data is correct.

Rules:

- Use a 4/8 point rhythm.
- Screen horizontal inset: 16 px baseline on phone, 20-24 px when width allows.
- Section gap: 20-24 px between major screen sections.
- Card internal padding: 12-16 px for dense cards, 16-20 px for summary cards.
- Card gap: 8-12 px between related elements inside a card.
- List row gap: 8 px minimum between compact rows.
- Touch target area: at least 44 x 44 pt on iOS-style targets; use hit slop or padding when the visual control is smaller.
- Adjacent touch targets need at least 8 px separation.
- Fixed headers, tabs, and bottom bars must reserve top/bottom content inset so scroll content is never hidden.
- Avoid nested card stacks. If a card needs internal grouping, use dividers, headings, or subtle surface changes instead of another card.

## 4. Card Composition Rules

Why: Cards are the main unit of mobile comprehension. Each card must have a predictable grammar so users can compare states across screens.

Global card structure:

- Header: object name, decision/status, authority/freshness badge.
- Body: the most important reason, evidence, metric, or state.
- Meta: timestamp, source, provenance, generated/read-path state.
- Status: blocker, stale/missing/unknown, validation, risk severity.
- Action: read-only navigation or disabled action explanation only.

Summary Cards:

- Lead with the summary value or state.
- Show source freshness in the header or first row.
- Limit to one primary metric and two supporting metrics.
- Why: summary cards are for orientation, not full investigation.

Evidence Cards:

- Lead with the evidence claim, then source, timestamp, and freshness.
- Show missing provenance as a visible blocker.
- Why: evidence without provenance is operationally dangerous.

Risk Cards:

- Lead with severity, blocker reason, and current control state.
- Use text plus color; never color alone.
- Why: risk must interrupt false confidence.

Position Cards:

- Separate broker truth, local runtime record, market value, and thesis state.
- Never merge local and broker truth into one happy status.
- Why: reconciliation ambiguity must stay visible.

Chain Cards:

- Show layer, state, source/provenance refs, and missing layer blocker.
- Prefer vertical step composition over decorative flow diagrams on phone.
- Why: chain detail is provenance audit, not visual storytelling.

Order Cards:

- Lead with local state and broker-truth state.
- Show mutation permission as disabled/forbidden when applicable.
- Why: order UI must not look executable while governance blocks mutation.

System Cards:

- Lead with governance, source freshness, control state, or validator state.
- Avoid green "all good" summaries when any required state is unknown.
- Why: SYSTEM is the canonical safety and source-health surface.

## 5. Dashboard Rules

Why: Dashboards should reduce cognitive load, not maximize card count. The user should understand the operating state before scrolling.

Global dashboard rules:

- Above the fold: maximum three primary cards.
- Visible primary actions: maximum one per card, and only read-only unless disabled with reason.
- Total first-level sections: 4-6 per tab.
- Use vertical rhythm and card order to encode priority.
- Avoid table-first layouts on phone; use compact list rows with expandable detail routes.

HOME:

- Order: portfolio/system attention, blockers, brain snapshot, freshness, latest review items.
- Above fold must show blocker or stale state if present.

BRAIN:

- Order: review-only/blocked candidate summary, scanner groups, source state, evidence strength.
- Candidate rows must not invent confidence, score, or rank.

PORTFOLIO:

- Order: account/position summary, broker/local reconciliation, exposure/risk, source state.
- Position cards must distinguish "unknown" from "zero".

ORDERS:

- Order: order-state summary, local/broker truth rows, disabled action reason, reconciliation blockers.
- No active submit, cancel, execute, approve, or reject affordance.

SYSTEM:

- Order: governance hard state, source freshness, control state, validators, artifacts.
- SYSTEM may be dense, but every dense row needs status text.

## 6. Detail Screen Rules

Why: Detail screens are audit workspaces. They must preserve the required decision frame and let users move from summary to proof without losing risk context.

Global order:

1. Decision Summary
2. Thesis / Logic
3. Validation / Readiness
4. Evidence
5. Risk
6. Next Action

Rules:

- The six-section order is mandatory for Candidate, Position, Chain, Risk, and Order detail variants unless a current SSOT document defines an explicit extension.
- Keep Decision Summary and current blocker state visible early.
- Expansion/collapse is allowed only below the first summary block.
- Collapsed sections must still show state, count, severity, and freshness.
- Evidence lists must show label, value, source, freshness, and provenance.
- Risk presentation must include blockers, stale/unknown source state, and control implications.
- Next Action must distinguish allowed read-only actions from disabled trading actions.

Screen-specific rules:

- Candidate Detail: do not create a candidate-to-buy flow; show lifecycle as review/blocked state only.
- Position Detail: show broker truth and local runtime record separately.
- Chain Detail: show missing L0-L7 layers as blockers or unknowns, not absent rows.
- Risk Detail: show kill-switch/control-state evidence before secondary diagnostics.
- Order Detail: show order purpose, state, evidence, disabled action context, and broker-truth uncertainty.

## 7. Mobile UX Rules

Why: The current near-term preview is phone-first. Mobile quality is not a smaller desktop; it is a priority system for quick, safe review.

Rules:

- Design for one-hand scanning first, full investigation second.
- Put primary read-only navigation and safety context within thumb reach when possible.
- Minimum touch target: 44 x 44 pt; adjacent touch targets need 8 px spacing.
- Use bottom tabs only for the fixed five top-level destinations.
- Bottom sheets may show provenance, blocker explanation, filter controls, or source details. They must not become primary navigation.
- Modals are for blocking confirmation, explanation, or focused inspection only. Every modal/sheet needs a clear close path.
- Avoid horizontal swipe as the only way to access critical actions or evidence.
- Preserve scroll position and filter state when returning from detail.
- Avoid nested vertical scroll areas inside mobile screens.
- Keep first viewport useful at 375 px width.
- If content is hidden behind a fixed tab bar, the screen fails.

## 8. Accessibility Rules

Why: Accessibility is an accuracy feature. If state is not perceivable through text, structure, and screen-reader semantics, it can be misread during operation.

Rules:

- Normal body text should meet at least 4.5:1 contrast against its surface.
- Secondary text should remain legible and should not be pale gray on light surfaces.
- Status cannot rely on color alone. Use text labels such as `STALE`, `UNKNOWN`, `BLOCKED`, `MISSING`, `SOURCE_NOT_ATTACHED`, `CHART_MISSING`.
- Icon-only controls require accessible labels.
- Interactive elements need semantic role/trait/state.
- Disabled actions need disabled semantics plus visible reason.
- Read-only is not the same as disabled; read-only means inspectable without mutation.
- Dynamic status updates should be announced where platform support exists.
- Support text scaling without clipping critical labels.
- Charts need textual summaries or data alternatives for key values.
- Motion must respect reduced-motion settings.

## 9. Loading / Empty / Error / Stale Rules

Why: In this system, absence of data is not negative evidence. States must explain what is missing and what the user can safely do next.

Loading:

- Show skeleton or progress when data takes more than a short moment to appear.
- Preserve layout space to avoid jumpy dashboards.
- Example: "Loading read-only source snapshot. No trading authority is inferred."

Empty:

- Empty means no rows in the selected read model, not no risk.
- Example: "No review rows in this fixture. This is not evidence of no candidates."

No Evidence:

- Show as `NO_EVIDENCE` or equivalent visible state with source/provenance gap.
- Example: "No source-backed evidence attached."

Missing Data:

- Show required field/source missing and affected screen section.
- Example: "Broker truth missing. Local record cannot be treated as account truth."

Blocked:

- Show blocker reason, severity, source refs, and required governance/data change.
- Example: "Blocked: source gate closed. Review only."

Error:

- State cause, scope, and safe recovery.
- Example: "Fixture parse failed. Screen remains read-only and not authority."

Stale Data:

- Show observed/generated time when available.
- Example: "Stale source. Do not treat current summary as fresh permission."

Recovery Required:

- Provide a read-only next step, not a trade action.
- Example: "Open source audit" or "Inspect blocker report."

## 10. Interaction Rules

Why: Interactions must make the UI feel responsive while preserving safety. A user should never wonder whether tapping something could mutate state.

Rules:

- Taps must produce visible feedback within roughly 100-150 ms when feasible.
- Card taps should navigate to read-only detail or expand local information.
- A card that is not tappable should not look tappable.
- Accordions are allowed for secondary sections; the current status must be visible while collapsed.
- Bottom sheets are allowed for source/provenance, filters, and blocker details.
- Modals are allowed for high-severity explanations or future confirmations, but current trading mutation remains disabled.
- Confirmation flows must exist before any future destructive or mutation-capable action is ever enabled.
- Disabled action taps may show "why disabled"; they must not call mutation handlers.
- Avoid gesture-only interactions for evidence, source, blocker, or order controls.

## 11. Motion Rules

Why: Motion should clarify state change, not create excitement. Institutional interfaces should feel steady, fast, and interruptible.

Allowed motion:

- Press feedback through opacity, color, or small non-layout-shifting scale.
- Expand/collapse transitions for accordions and sheets.
- Skeleton/loading shimmer if reduced motion is respected.
- Refresh indicator for read-only data reloads.
- Status transitions that help users see what changed.

Forbidden motion:

- Decorative looping animation on operational screens.
- Flashing live-looking market pulses without pause/reduced-motion handling.
- Animations that move neighboring content unexpectedly.
- Motion that implies execution, fill, profit, or live trading readiness.
- Long transitions above 500 ms for core navigation.

Timing:

- Micro-interactions: 150-300 ms.
- Exit transitions should be shorter than enter transitions.
- Refresh or loading animation must not block scrolling or navigation.

## 12. Information Density Rules

Why: This product needs high information density, but density without hierarchy becomes operational fog.

Rules:

- Maximum three primary cards above the fold.
- Maximum one dominant metric per summary card.
- Maximum three supporting metrics per card unless the card is a dense list row.
- Maximum six first-level sections per top-level screen.
- Maximum six required sections in a detail frame, matching the universal detail contract.
- Maximum two nested disclosure levels on phone.
- Maximum one visible action cluster per screen region.
- Long lists over roughly 50 rows should use virtualization or paging when implemented in app code.
- Charts should avoid more than six simultaneous visible series on phone.
- Network, treemap, sankey, and 3D charts are supplementary only and require list/table alternatives.

## 13. Component Quality Rules

Why: Component quality determines whether future UI work scales. Every component should make safe behavior easier than unsafe behavior.

Rules:

- Components must be reusable, props-driven, and free of hidden trading side effects.
- Domain components must map to the frontend read-model contract.
- Do not invent fields such as confidence, rank, score, permission, broker truth, or source freshness.
- Every status component needs text, tone, and accessibility semantics.
- Every disabled action component needs reason and required governance change.
- Every chart component needs source attachment or explicit absence.
- Every component should have Storybook or equivalent isolated coverage for fresh, stale, missing, unknown, blocked, and disabled states when applicable.
- Use one icon family/style per hierarchy level.
- Use semantic tokens rather than ad hoc colors.
- Keep radius at 8 px or less unless native platform convention or an approved token says otherwise.
- Minimal elevation is preferred; use borders and spacing for hierarchy first.

## 14. Anti-Patterns

Why: Anti-patterns are where UI polish becomes operational risk. The following are forbidden or strongly discouraged.

Bad dashboard patterns:

- Green "healthy" summaries that hide stale, missing, or unknown states.
- Too many primary cards above the fold.
- KPI walls without decision or blocker context.
- Treating validator pass as readiness.

Bad mobile patterns:

- Dense desktop tables squeezed into phone width.
- Critical actions or evidence hidden behind gestures.
- Content hidden under bottom tabs.
- Tiny tap targets or icon-only controls without labels.

Bad card patterns:

- Nested cards inside cards.
- Cards with no status, no source, or no meta.
- Cards that look tappable but do nothing.
- Cards that mix broker truth and local runtime truth.

Bad typography patterns:

- Hero-sized titles inside compact operational cards.
- Body text below 14 pt for decision-support copy.
- Low-contrast gray captions used for critical state.
- Random font weights and inconsistent numeric alignment.

Bad chart usage:

- Source-free charts treated as evidence.
- Red/green-only signal encoding.
- Pie/donut as primary analysis in accessibility-sensitive contexts.
- Candles without OHLC/source table or summary.
- 3D, network, treemap, or sankey charts as the sole representation.

Bad trading UI patterns:

- Active-looking buy, sell, submit, execute, approve, cancel, or broker-sync controls.
- Retail brokerage calls to action.
- Chart-first screens that bury evidence, source, or risk.
- Profit/loss celebration visuals.
- Lifecycle states promoted into top-level navigation.

Bad information density patterns:

- More than two nested disclosure levels on phone.
- More than one primary action cluster in the same viewport.
- Long ungrouped lists without filters, sections, or virtualization.
- Evidence rows without provenance.

Bad interaction patterns:

- Disabled controls that silently do nothing.
- Modals without clear dismissal.
- Hover-only affordances on mobile.
- Motion that shifts layout or creates false urgency.

## 15. Visual QA Checklist

Why: Future Codex UI work needs a repeatable gate. The goal is not subjective beauty; it is operational clarity, trust, and mobile usability.

Use this checklist before every frontend merge or visual handoff. Score each category from 0 to 2.

Scoring:

- 0: fails or missing.
- 1: present but weak or inconsistent.
- 2: strong and repeatable.

Categories:

| Category | Review questions |
| --- | --- |
| Readability | Are primary text, captions, numbers, source refs, and disabled reasons legible on phone? |
| Hierarchy | Does the first viewport show decision state, blockers, freshness, and evidence path before secondary detail? |
| Spacing | Does the screen use 4/8 rhythm, safe-area clearance, and no content hidden behind fixed UI? |
| Consistency | Do cards, badges, typography, icons, and status tones match existing component patterns? |
| Usability | Are touch targets at least 44 pt, tap feedback visible, and navigation/back behavior predictable? |
| Trustworthiness | Are source freshness, provenance, unknowns, blockers, and disabled states explicit? |
| Institutional Quality | Does the screen feel calm, dense, evidence-forward, and free of retail brokerage tropes? |
| Mobile Quality | Does the 375 px width work without clipping, horizontal scroll, or unreadable compression? |

Automatic fail conditions:

- Active trading mutation affordance appears.
- Top-level navigation changes.
- Missing/stale/unknown/source-not-attached state is hidden.
- Fixture or screenshot evidence is described as authority.
- Chart appears without source attachment or explicit absence.
- Color is the only status indicator.
- Important content is clipped or hidden under bottom navigation.

Minimum merge expectation:

- No automatic fail.
- Score at least 12 of 16.
- Any score of 0 must have a documented blocker or patch plan.

Validation notes:

- Screenshot QA evidence is visual evidence only.
- Storybook coverage is component health evidence only.
- Typecheck/lint/test pass is not strategy acceptance, deployment readiness, paper permission, live permission, broker truth, or real-capital permission.
