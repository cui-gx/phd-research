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