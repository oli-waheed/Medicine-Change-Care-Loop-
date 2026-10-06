<!--
Sync Impact Report
Version change: 1.0.0 → 1.1.0
Modified principles: Evidence-Driven Decision Making; User-Centered Delivery; Quality Before Completion
Added sections: Medicine Change Care Loop Constraints; explicit project-specific safety, data, traceability, evidence, AI-assistive, and scope rules
Removed sections: none
Deferred items: TODO(RATIFICATION_DATE): confirm the original team adoption date before formal ratification.
-->

# Medicine Change Care Loop Constitution

## Core Principles

### I. Evidence-Driven Decision Making
All project decisions must be supported by current repository evidence: specification, plan, task status, code, meeting notes, and review artifacts. Claims without evidence are treated as assumptions until confirmed. The team must explicitly state assumptions, risks, and missing information before moving to a new phase.

### II. User-Centered Delivery
The team prioritizes outcomes that deliver value to the intended users, stakeholders, and course requirements. Every feature or change must be traceable to a defined need, scenario, or requirement. Scope changes must be justified by stakeholder value, not by convenience or novelty.

### III. Shared Accountability
Each team member is accountable for the quality and completeness of their work, including documentation, verification, and communication. Work must be visible, reviewable, and understandable to others; ownership must be clear for each task and decision.

### IV. Quality Before Completion
No work is considered complete until the relevant evidence confirms it is consistent with requirements, tested, and understandable to reviewers. This includes an update to the appropriate specification, plan, tasks, or repository artifacts, as well as a brief summary of what was verified.

### V. Continuous Improvement
The project is expected to evolve through reflection, learning, and corrective action. After each milestone, the team must identify gaps, risks, and lessons learned and adjust plans or practices accordingly.

## Additional Constraints
- The repository must remain a truthful record of team progress; intentionally stale, contradictory, or undocumented work is not acceptable.
- Decisions that affect scope, schedule, or quality must be recorded with rationale, trade-offs, and affected stakeholders.
- The team must distinguish between confirmed facts, assumptions, and open questions, and must not treat unverified assumptions as accomplished work.
- Communication must be clear enough that a reviewer can understand intent, state of work, and outstanding issues without needing informal context.
- Human-in-the-loop safety is mandatory: the system detects and communicates medicine-information changes but never diagnoses, recommends treatment, selects medicine substitutions, decides clinical urgency, or automatically closes clinically relevant cases.
- Simulated data only: all patient and medication records used by the prototype must be simulated. No real patient-identifiable information may be used in development, testing, demos, or stored artifacts.
- Source traceability is mandatory: detected medicine-information changes and review cases must be traceable to their source snapshot, and important status transitions must be recorded.
- Evidence honesty is mandatory: the system must distinguish verified information, inferred information, unknown information, and conflicting information where relevant, and it must not collapse uncertainty into certainty.
- AI is assistive, not authoritative: AI-generated explanations or matching suggestions must be evaluated against deterministic methods and must not independently change case status or replace human review.
- The project must remain within its prototype scope: real patient data, Kanta/EHR integration, pharmacy inventory integration, automatic medicine substitution, autonomous clinical decisions, and production deployment are explicitly out of scope.

## Development Workflow
- Start from evidence: review the current specification, project plan, and repository state before proposing changes.
- Develop in small vertical slices: deliver small working end-to-end pieces instead of completing isolated architectural layers before user-visible progress is demonstrated.
- Break work into tasks that are small, testable, and linked to requirements or goals.
- Update the relevant project artifacts as work progresses; do not leave plans, specs, or documentation stale.
- Verify before claiming completion; review evidence, run validation where applicable, and note any unresolved risks.
- Use GitHub, branches, and pull requests as the default workflow for collaboration and review.
- Maintain automated tests for important business logic and APIs, and perform manual end-to-end testing for key user flows.
- Follow Spec-Driven Development: specification, plan, tasks, review, and implementation updates must remain aligned with the current repository state.
- Hold regular checkpoints to confirm progress, alignment, and any missing information before the next increment.

## Governance
This constitution governs how the team plans, evaluates, and improves the project. It supersedes ad hoc practices when there is a conflict between informal habits and the rules below. All project decisions must remain consistent with the team's stated principles, scope, and evidence standards.

Amendments follow this process:
1. Propose the change with clear rationale and affected section(s).
2. Document the impact on project decisions, workflow, or quality expectations.
3. Review the amendment with the team and update relevant planning or project artifacts.
4. Record the new version, date, and summary of the change.

Versioning policy:
- MAJOR: backward-incompatible changes to governance or core principles
- MINOR: additions or material expansions to principles, workflow, or constraints
- PATCH: clarifications, wording improvements, or non-semantic corrections

Compliance expectations:
- Team members must check whether work aligns with this constitution before claiming completion.
- Reviewers must verify that decisions, documentation, and evidence are traceable to the current project goals.
- Unresolved conflicts, assumptions, or missing evidence must be explicitly documented and addressed before the next phase.

**Version**: 1.1.0 | **Ratified**: TODO(RATIFICATION_DATE): confirm the original team adoption date | **Last Amended**: 2026-10-06
