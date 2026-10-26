# Doctoral Research — Codex Instructions

## GQ round 1 approval (2026-10-26)

- Researcher APPROVED a bounded exploratory GQ round, cumulative single-GPU occupation at most 3600s, including failures/retries/warmup. Stage caps: GQ1 600s, GQ2 1200s, GQ3 1200s, reserve 600s; never reset or transfer scope. See `docs/P1-GQ/analysis-plan.md`.
- User separately confirmed laboratory use has been coordinated with no additional deadline; still recheck occupancy before every task. Do not preempt others.
- This latest approval supersedes the old design-only prohibition for this GQ round and permits bounded protocol candidates, short independent random streams, conditional extension and necessary GPU cost tests without awaiting domain-adviser reply. It does not complete the pending S2 independent review or approve B1/B2/C policy comparisons or S3.
- Commit/push and remotely verify the plan before first scientific computation. Preserve original S1/S2 evidence, execute/measure/analyze primarily on server, keep one persistent budget ledger, report all failures, and stop after GQ.


## Confirmed C/B priority and server-first execution (2026-10-25)

- Researcher-confirmed: **P1-C is the current main direction**: test whether pre-decision scientific feedback state adds information about update value beyond costs, remaining time, data quantity and training state. **P1-B is jointly designed** to measure downstream exploration effects and real opportunity costs; whether C, B or both become paper contributions remains evidence-dependent. See `docs/P1-CB-Design/README.md`.
- Preserve FSD-EY/1FME, OpenMM, existing mdlearn CVAE and one RTX PRO 6000 96GB. Mathematical forms, features, thresholds, samples and budgets in the design are PROPOSED, not approved experiment settings. These C/B names are distinct from S2 supplement task labels.
- Main numerical experiments and tests run on the authorized laboratory server. Mac is for development, file management, transfer, GitHub synchronization and lightweight debugging. Never substitute Mac scientific computation for a blocked server run without researcher approval; Mac CPU timings are not target-GPU costs.
- This design task authorizes documents and synchronization only: no new MD, GPU training, S2 reruns or policy experiments. S2 supplement independent final review remains INCOMPLETE; **S3 NOT APPROVED**. After design delivery, stop for researcher/planning review. Any subsequent computation requires a separately approved bounded execution card and fresh shared-resource checks.

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

## Local execution workspace supplement

Read `research-workflow/local-workspace-instructions.md` for local safety, stage, tutorial, snapshot and cleanup rules. This preserves the pre-sync workspace rules. The shared GitHub plan and latest user decisions take precedence over its historical research scope or source-of-truth wording. Research plans are authoritative on GitHub; local code and raw experiment evidence are execution artifacts and must not be represented as already uploaded.

## Latest operational requirements (2026-10-24)

- On the laboratory server, Git identity configuration may only be repository-local inside the researcher-owned project. Never set system or global identity, install credentials for the entire server, or alter other users' configuration.
- If the laboratory SSH connection fails, ask the user to enable the campus VPN and stop investigating other causes unless the user changes that instruction.
- After each bounded implementation stage, publish measured evidence and a stage report. The researcher and planning conversation review and approve the next research stage; implementation success is not permission to advance automatically.

## Shared server and GPU occupancy check — mandatory

- At the start of every server session, first inspect current users/tasks and CPU, memory and GPU use read-only. Before starting an installation, experiment, GPU batch or restarted run, recheck the resources it will use; an earlier idle snapshot is not sufficient.
- Check relevant usage/reservation records where available, plus actual process ownership, CPU/memory load, GPU processes, memory use and utilization. Zero GPU utilization alone does not establish availability or permission.
- If another user occupies the required resources, or their allocation boundary is unclear, pause the resource-consuming action and report to the researcher for coordination. Never preempt, stop, kill or reconfigure another user's work. Resume only when the permitted resource scope is clear.

## Approved P1 stage and research handoff rule (2026-10-24)

- **S1 is officially accepted (PASS) by the researcher** for the real single-GPU MD → CVAE train → inference → restarted MD engineering loop. It is not evidence of scientific exploration benefit.
- **S2 is APPROVED**: follow `docs/阶段实施规格/P1-S2-科学资格与成本测量.md` precisely. Scope: MD science protocol audit, bounded actual run-cost measurements, same-candidate frozen-vs-updated CVAE decision comparison, and a model/reference-independent conformational coverage metric proposal. Do **not** auto-advance to S3.
- On completing S2, publish evidence and phase report, update `docs/协作交接记录.md`, push to GitHub, verify remote contents, and stop pending a new researcher approval.
- **New user-confirmed rule for research planning side**: after each substantive planning analysis, **whenever implementation/execution work is needed**, include a complete ready-to-copy Codex Prompt with scope, requirements, guardrails, expected outputs, acceptance criteria and repository handoff. The operational side should read that prompt together with the newest shared files; a prompt is not a license to widen the agreed research scope.

## S2 conditional acceptance and supplement approval (2026-10-24)

- The researcher has **accepted S2 as `CONDITIONAL PASS`** and **approved a bounded `S2-SUPPLEMENT`**, not S3. Follow `docs/阶段实施规格/P1-S2补充-科学评价协议收敛.md` (read entire file) plus the latest GitHub context before working. Do not mistake the old pending/proposed S2 review notes for the current confirmed decision.
- Prioritize existing S2 trajectories (4,880 frames) and checkpoints for scientifically defensible offline checks of coverage metrics, reference-free candidate selection, and physical-model assumptions. Do **not** start new long GPU MD jobs, broad training runs, or S3 scheduling campaigns without a separate user authorization.
- Scientific reports must be **audit-grade**: predeclared hypotheses and analysis plan, exact mathematics/units, input provenance and versions, data/seed/commit/sha traceability, raw vs derived distinctions, negative results, failure logs, sensitivity/limitations, and reproducibility procedures. Statistical unit is independently generated trajectories, not correlated saved frames. Where Japanese advisor-facing communication is useful, include an accurate Japanese executive summary.
- Any metric threshold must be specified independently of future strategy outcomes. Missing truly independent calibration data is a documented limitation, not permission to claim a validated metric. Existing model update effects on candidate rankings must never be misrepresented as established exploration benefit.
- At completion submit the full evidence-linked S2 supplement report, update handoff log, push via authorized user account, verify remote, and stop for researcher review. `S3 NOT APPROVED`.

## Mandatory model recommendation in every Codex instruction (2026-10-24)

- **Researcher-confirmed rule:** Every ready-to-send Codex instruction or prompt from the planning assistant must explicitly tell the researcher and Codex **which available model and reasoning-effort setting are recommended for this specific task**, plus the task-based rationale and when to switch/upgrade/downgrade. Do not leave the model selection implicit.
- Put a visible header **before the prompt** and include the recommendation **inside the prompt** so it survives forwarding. For multi-phase work, give a model/effort for each materially different phase (e.g. Astra High for scientific methodology; Sol High/Medium for coding/data processing; Astra Extra High/Max for adversarial scientific review), rather than wasting an expensive mode on all steps.
- Astra Ultra is **not the default**: consider only for truly separable, parallel, large-scale reviews where coordination cost is warranted. Name choices based on task complexity, not prestige; where the exact model is unavailable, specify an available-capability fallback and ask the user to select the closest option.
- A text prompt **does not force a Codex model switch**. Do not claim any automatic reconfiguration; the researcher should choose models in their UI unless the client independently supports switching.
- This changes only the presentation and execution efficiency, **not** current S2-SUPPLEMENT approval, scientific scope, access permissions, or S3 status.
