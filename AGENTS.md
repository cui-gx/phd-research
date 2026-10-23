# Doctoral Research — Codex Instructions

## Read-first context

Before proposing or making research-related changes, read the complete file:

- `docs/博士研究_全局总档案.md` (the canonical doctoral research context, copied into this repository by the user)

If this file is absent, do not infer or reconstruct its detailed contents; ask for the file or link to the correct source. In this repository, user instructions and the latest explicit user decisions override prior notes.

## Current confirmed P1

- Single GPU: **1x NVIDIA RTX PRO 6000 96GB**.
- Real research workload: **FSD-EY, PDB 1FME** with **OpenMM MD**, **CVAE**, using **DeepDriveMD / Colmena** implementations where feasible.
- Research target: scientific exploration efficiency and GPU-time scheduling of MD vs CVAE training/inference in a fixed end-to-end computation budget.
- Evaluate **conformational-space exploration**, not the biological goal of folding prediction or neural network novelty.
- Important correction: the user's main prediction idea is the **within-workflow decision** to retrain/use AI given arriving scientific data, expected effects on next candidate selections, update cost, and remaining time. **Do not silently switch the research topic to predicting future HPC cluster job arrivals.**
- Heterogeneous HPC cluster allocation is a broader three-year research direction, not the current P1 experimental scope.

## Division of responsibility

- Researcher: chooses goals, assumptions and final scientific conclusions.
- Planning assistant: designs research questions, experiments, baselines, evidence interpretation and paper structure.
- Codex: implements only approved technical specifications, environments, experiments, reproducible scripts and logs.

## Execution rules

1. Don't replace the fixed P1 research object, goal, metric or resources without explicit authorization.
2. Mark choices as `confirmed`, `proposed`, or `unverified`. Never turn tentative suggestions into research decisions.
3. Preserve scientific correctness: stable MD settings, reproducible random seeds, comparable compute budgets, explicit task dependency and scheduling overhead.
4. Report exact library/software versions, commands, data provenance, GPU use, measurement method, failures, and raw experiment outputs.
5. Prefer small reproducible experiments, with clear baselines and failure handling. No broad implementation or integration merely for novelty.
6. Do not claim scientific improvements from GPU utilization or CVAE training loss alone. Evaluate downstream conformational exploration with an independent, fixed metric.
7. Keep code and experimental artifacts reproducible; return a concise report to the planning assistant/user for scientific interpretation.

## Shared GitHub research synchronization — mandatory

The shared, private **source of truth** is `cui-gx/phd-research` on GitHub, branch `main`. The canonical plan is `docs/博士研究_全局总档案.md`; this `AGENTS.md` contains operational rules. The ChatGPT Library copy is a historical backup and must not overwrite the newer GitHub version.

### At the start of EVERY doctoral research session

1. Authenticate with the user's authorized GitHub access; fetch/pull the latest `main` from `https://github.com/cui-gx/phd-research` and read the full canonical plan, this instruction file, and `docs/协作交接记录.md`.
2. If development is in a different repository, read the shared research repository separately; do not assume the files are present in the code repository. If the repository cannot be accessed, report the limitation and request the latest documents; never claim synchronization succeeded.
3. Before changing implementation, check for new research decisions, current P1 resource limits, existing progress, and pending decisions.

### At the end of EVERY doctoral research work session

1. Review whether confirmed research decisions, approved experimental specifications, implementation progress, measured results, failures, or next actions changed. Record all substantive changes; do not create meaningless commits.
2. Preserve scientific status labels: `CONFIRMED` (explicitly approved by researcher), `PROPOSED` (not yet approved), `MEASURED` (actual measurements with evidence), `UNVERIFIED`, and `SUPERSEDED`. Never mark implementation choices as approved research decisions.
3. Update `docs/协作交接记录.md` with date, work completed, code repository/commit references where available, evidence/artifacts, blockers, proposed next actions, and which scientific decisions await approval. Update the canonical plan only for important durable research decisions or established findings; avoid dumping routine logs into it.
4. Fetch/pull latest remote changes immediately before committing; reconcile concurrent changes from the planning chat and implementation work. Never force-push, discard others' edits, or blindly overwrite a stale remote file.
5. Commit and push via the researcher's authorized GitHub account, using the repository's configured identity, without AI co-author trailers or AI-related credit in commit messages. Never change someone else's git identity or bypass authentication controls.
6. Read back the pushed files or remote commit and state the commit SHA. If push or permission fails, retain changes locally, report explicitly that GitHub was NOT updated, and provide a patch/summary for synchronization.

The planning conversation follows the same cycle: read latest shared repository before research discussions when appropriate; after substantive decisions, record and push the confirmed conclusions and outstanding questions. Implementation updates are not themselves proof of scientific validity. The researcher's explicit latest instructions override any document, and conflicts require careful reconciliation.

Never commit credentials, SSH keys, private server details, raw sensitive records, or large simulation outputs into the shared research notes. Commit only concise reproducible references and meaningful findings; use appropriate storage for large experimental data.
