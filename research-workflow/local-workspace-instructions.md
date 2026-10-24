# Codex Research Execution Rules

This folder is the only project workspace for this doctoral study. Do not inspect, import, or align with files in any older project folder unless the user explicitly names a file to import. Do not inspect PowerPoint files unless explicitly requested.

## Tutorial organization

Keep all new tutorials, study routes, glossaries, and learning exercises under the top-level `教程/` directory, organized by topic. Treat `教程/README.md` as the tutorial index. `learning/first-part/` is a compatibility symlink to the canonical `教程/第一部分/`; do not create or maintain a second copy there. Keep research papers and paper analyses under `literature/`.

## Project snapshots

Keep point-in-time project snapshots under the top-level `项目快照/` directory. Create one when the user asks or when a material change to the research goal, stage, next gate, timeline, or external blocker makes a fresh user-facing snapshot useful. Use a dated filename, record the as-of time and evidence limits, update `项目快照/README.md`, and preserve older snapshots rather than overwriting them. Snapshots summarize the project; `research-workflow/state.yaml`, `research-workflow/next-task.yaml`, and the latest stage report remain authoritative for execution.

## Mandatory startup sequence

Whenever the user says `开始`, `继续`, `执行下一步`, or asks Codex to advance the research:

1. Use the `run-doctoral-hpc-research` skill.
2. Read this file, `/Users/carsoncui/.codex/user_profile.md`, `START_HERE.md`, `research-workflow/state.yaml`, `research-workflow/next-task.yaml`, and the latest report named by `latest_report` in the state file.
3. Run the skill's workspace inspector on this folder.
4. Select the earliest incomplete prerequisite stage. Execute only the bounded task in `research-workflow/next-task.yaml` unless the user explicitly changes scope.
5. Explain the step, prerequisites, artifacts, metrics, and pass condition before changing files.
6. Use the smallest deterministic test before any larger experiment.
7. Update state, task status, evidence matrices when applicable, and a dated stage report after every material step.
8. If local execution is inadequate, read `configs/remote_execution.yaml` and `research-workflow/remote-execution-runbook.md`. Do not attempt SSH until the host alias is configured and the user has authorized access.
9. Before 2026-10-01, follow `configs/pre_enrollment_plan.yaml`: server access is unavailable and remote execution is documentation-only.
10. Read `research-workflow/PROGRESS.md` and `research-workflow/progress-ledger.yaml` before resuming a segment.
11. For any local code or experiment, read `configs/local_environment_policy.yaml`, register created runtime resources, and use disposable segment-scoped environments.

For every HPC/systems paper, paper link, or reader summary handled in this research workspace, also load and apply the `read-hpc-systems-papers` skill. Check the primary text, identify the evidence type and evaluation boundary, and map the result to the current P1 scope before updating literature records. This preference remains active for subsequent paper-review turns.

## Evidence and safety rules

- Treat `traces/raw/` and `results/raw/` as append-only once created.
- Label evidence as exactly one of: `derived analysis`, `local CPU/GPU measurement`, `trace-driven simulation`, or `small Slurm/pilot testbed`.
- Never describe simulation as production-cluster evidence.
- Do not modify production Slurm, use root, toggle MIG on shared hardware, spend cloud credits, contact third parties, publish, or submit papers without explicit permission.
- MIG is optional. Running-task migration and reinforcement learning are out of the initial scope.
- Define metrics, denominators, exclusions, seeds, thresholds, and equivalence margins before inspecting final experimental results.
- Preserve negative results and failures.
- Remove AppleDouble `._*` files created in this workspace before handoff; never clean outside this workspace.
- Keep the local workspace as the source of truth for remote execution. Never store passwords/private keys, disable host-key checking, use `rsync --delete`, or inspect unrelated remote directories.
- After a bounded local segment's final result is validated, preserve evidence and remove its registered virtualenv, temporary containers/images/volumes, caches, temp files, and background processes before handoff. Never use global prune or broad process killing.

## Segment handoff rules

At the end of every bounded segment:

1. Create the detailed report from `research-workflow/templates/segment-summary.md`.
2. Update `research-workflow/PROGRESS.md` for the user.
3. Append/update `research-workflow/progress-ledger.yaml` for Codex.
4. Update state, next-task segment progress, and `local-resource-registry.yaml`.
5. Complete and verify local cleanup before the final response.
6. Stop after reporting. Do not begin the next segment until the user asks to continue.

## Research boundary

The object is an AI-coupled scientific workflow with feedback among simulation, training, inference/selection, and analysis—not a queue of unrelated scientific and AI jobs. Existing workflow runtimes must be reused. The proposed contribution is an interpretable, workflow-semantic resource controller; the runtime itself is not the novelty claim.

## Grounded research and consistent terminology

This is the user's explicit standing requirement for this and future research projects. Work from the actual Japanese laboratory setting: available equipment, access rules, time, budget, skills, and adviser expectations. Do not replace concrete research with grand, vague narratives or claims about what all Japanese research requires.

- Begin each proposed study with a bounded execution card: exact object/data, solver and AI model, hardware and software, controlled action, fixed factors, baselines, primary outcome and units, smallest runnable experiment, cost cap, and pass/failure criteria. Identify proposed versus confirmed values. Broader motivation must lead to this concrete study.
- Prefer a modest experiment that can run, be reproduced and be explained. Method adaptations, different hardware, careful measurements and exploratory results may be valuable despite literature overlap. Describe the supported contribution without invented superiority, first-ever claims, or guaranteed publication.
- Presentations follow the same logic: concrete setting and current bottleneck, why it matters, bounded objective, executable method, fair comparison, observed/expected outcome, actual progress and next action. Clearly label plans, literature facts and measured results. Do not inflate an exploratory study into a universal platform.
- Maintain one canonical project glossary at `教程/研究规范/术语与定义.md`. Read it when preparing current research plans, experiments or presentations. Define new substantive terms there before using them as central claims. Include preferred Chinese/Japanese/English names, meaning, measurement or operational rule, units, scope and common confusions where applicable.
- Use the same term, symbol, unit and event boundary across plan, configuration, code, figure, manuscript and slides. Expand abbreviations on first use; do not invent overlapping names or silently change a definition. Mark project-specific and provisional definitions explicitly. Version material definition changes before new experiments.
- Match the breadth of a claim to the tested object and hardware. Archive historical wording; synchronize active artifacts when definitions change. Do not inspect or modify PowerPoint without an explicit PPT request.

The plain-language implementation standard is `教程/研究规范/研究与汇报基本规范.md`.

## Completion rule

Do not mark a stage complete because documents or code merely exist. Apply the exact exit condition in `research-workflow/state.yaml` and `research-workflow/next-task.yaml`. If evidence is insufficient, report `REPEAT` and set one precise next task.
