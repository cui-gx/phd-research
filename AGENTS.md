# Doctoral Research — Codex Instructions

> 最新承認：2026-10-28 P1-B1-R1の限定CPU再解析。承認設計59f97821に厳密に従う。新MD/学習/モデル推論/B2/C予測器/S3は禁止。

## P1-B1-R1：CPU復核完了・審査待ち（2026-10-28、MEASURED / DERIVED）

承認59f97821のCPU再解析は完了。15,208原SHA/9archive保持、240原評価再現、四参照/全指標/全窓/8根階層/LOFと最終監査PASS。[完全報告](docs/P1-B1-R1/review-dossier.md)と[A–G引継ぎ](docs/P1-B1-R1/handoff-to-chatgpt.md)を参照。実行器は終了し、再実行しない。共通H4の主平均段階差は残るが共通H2とは不一致、六離散尺度/全体F2優位は不確実。Xの独立価値・B2純利益・P/L資格を認定しない。技術交付と独立科学審査/研究者受入れPENDINGを分離し、次は審査で停止。新MD/学習/モデル推論/B2/C予測器/S3は禁止。下記CPU承認は実施済みの履歴で、継続計算の許可ではない。

## P1-B1-R1：限定CPU実行の承認（2026-10-28、CONFIRMED）

研究者は設計commit `59f97821ae6ffe283c371f710546abf84f691642` のCPU再解析を明示承認した。四参照・全指標/全時間窓・8根階層・保存embedding LOF診断を維持する。まず原入力の実SHA/ID/原子順/時刻/完全性を検査し、ORIGINAL_HISTORYを再現する。不一致なら証拠を保存して停止する。元B1ソース/原データ/旧出力は不変、新CPUモジュール/独立出力を使う。GPU不可視、単worker/数値thread1、計画のメモリ・ディスク・6時間再審査条件を守る。実行カードは [execution-approval.md](docs/P1-B1-R1/execution-approval.md)。

新MD、CVAE学習、CPU/GPUモデル推論、B2/C予測器/S3は禁止。9原archive保持、Mac raw転送なし。終了後は日本語完全報告・A–G引継ぎ・全表/図/SHA/費用/失敗とGitHub回読を完了し、独立科学審査を待つ。下記の設計のみ/未承認という記録は、このCPU実行範囲についてSUPERSEDEDな履歴として残す。

## P1-B1-R1：設計だけの承認（2026-10-28、CONFIRMED）

研究者はB1 Expansionの評価参照A0、S4/S8段階差、候補Top1/候補数、M0と乱数階層の独立した方法論的検討を依頼した。本輪は[再検証設計](docs/P1-B1-R1/README.md)と文書・必要な静的点検・Git同期のみ。旧B1報告、凍結科学ソース、原データ、結果、seedを変更しない。MD/訓練/推論、CPU科学再解析、B2/C予測器/S3を開始しない。

共通参照・候補制限・閾値/CPU運用案はPROPOSEDであり、この文書の完成は実行承認ではない。全事前登録指標/尺度、8根の統計階層、共有F0を維持する。再順位の候補に未実行MDの成果を割り当てない。物理条件とCVAE学習十分性は別資格ゲート。交付後は研究者・計画側審査で停止する。前回のMac raw backup免除とサーバ原archive保持は継続する。

## B1 Expansion保存・技術交付方針の変更（2026-10-28、CONFIRMED）

研究者は本輪のMacへの原科学archive全量複製を必須条件から外した。**MAC_RAW_BACKUP=WAIVED_BY_RESEARCHER**。GitHubは全報告・コード・行列・完全な構造化統計・図・SHA索引・実行/監査証拠を保持し、実際の遠隔回読を必須とする。GitHubに置かないDCD・重み・原ログ等は、既存の許可サーバのarchiveに保持する。9個のMac転送を続けず、元収集が退出済みであることを確認し、新収集を開始しない。

旧「Mac完全backup0/9」は2026-10-27の正しい実測履歴として残すが、今後の必須残件ではない。旧Mac複製/双端照合を技術交付の条件とする記述は、この本輪の運用要件についてのみSUPERSEDED。**サーバ原archiveを削除する許可ではない**。環境・cache・断片も本タスクでは削除/清掃しない。凍結コード・科学データ・条件・結果は変更しない。

技術交付はGitHub証拠とサーバ原archiveの実在/SHAを検証後に閉じられる。SCIENTIFIC_COMPUTE、RESULT_AUDIT、GITHUB_EVIDENCE_DELIVERY、MAC_RAW_BACKUP、SERVER_RAW_ARCHIVES、INDEPENDENT_SCIENTIFIC_REVIEW、RESEARCHER_SCIENTIFIC_ACCEPTANCEを分離する。独立科学審査/研究者科学受入れはPENDINGのまま。詳細と最新状態は[保存方針](docs/P1-B1-Expansion/storage-and-delivery-policy.md)と[機械可読状態](docs/P1-B1-Expansion/delivery-status.json)。新MD・訓練・推論・B2・C・S3は一切開始しない。



## 科学審査資料とChatGPTへの完全引継ぎ（2026-10-26、CONFIRMED）

- 研究者は方向・実験目標・重要な科学判断を決め、Codexは実装・実験・処理・検証・再現・保管を担当し、ChatGPTは計画・方法論審査・解釈・論文構成・次段階設計を担当する。Codexは毎回、ChatGPTが独立に確認できる引継ぎを残す。詳細は [共同作業規範](docs/collaboration-policy.md)。
- 大規模実験の終了時には、対応する `review-dossier.md` と固定入口 `handoff-to-chatgpt.md` を新規作成または更新する。公開資料は正確で自然な日本語とし、中国語の研究討議と区別する。要約だけで原証拠を置き換えない。
- B1 Expansionでは、`docs/P1-B1-Expansion/review-dossier.md` と `docs/P1-B1-Expansion/handoff-to-chatgpt.md` を完成する。18項目とA–Gは [本輪の交付要件](docs/P1-B1-Expansion/review-delivery-requirements.md) を厳守する。**2026-10-27の研究者追加承認により、既存表のCPU照合・文書作成はバックアップと並行できる**。旧「バックアップ後に文書作成」の順序だけを置き換え、未完了backup・清掃・独立審査・受入れは別々にPARTIAL/未完了と明示する。
- 本輪の正式文書作業は新MD・CVAE訓練・GPU推論・新バッチを許可しない。必要な既存統計のCPU照合はサーバで実施し、元の表を上書きしない。収集の故障は残件として記録し、この文書作業を伝送の再開や別の移行作業へ変更しない。文書完成後は停止する。
- 重要な結論を実際のCSV/JSON・ソース・実行ログ・manifestへ有効な相対リンクで結び、主要値・単位・分母・統計単位・不確実性を本文にも示す。有利な結果だけでなく、陰性・不一致・未解決・識別不能な部分を記す。
- `CONFIRMED / MEASURED / DERIVED / PROPOSED / UNVERIFIED` を維持する。進行中の実行状態は `RUNNING`、未完了の交付は `PARTIAL` と明記し、計算完了・保管完了・科学審査・研究者受入れを別々に記録する。技術的な自動収集だけで研究交付全体を `COMPLETE` としない。
- 報告作成を理由に凍結条件、seed、評価規則、実行順序、旧証拠を変更しない。追加MD・学習・GPUタスクや無許可の再計算を行わない。大きな軌跡・重み・完全ログは許可された保管先に残し、GitHubには簡潔な証拠・SHA・出典索引を置く。秘密鍵・内部ネットワーク・個人資源情報は載せない。
- 最終返信は、遠隔回読済みの実在する最終commit SHA、二文書のパス、主要な科学的知見、主要な不確実性、研究者に委ねる次の判断を含める。B2/C/S3の提案を承認扱いにせず、自動的に実行しない。

## GQ round 1 delivered and stopped (2026-10-26)

- Completed approved exploratory GQ round: 21 successful GPU tasks, 16.3ns total MD, 928.696225s cumulative GPU occupation of 3600s cap. All phase caps respected. Unused budget is NOT permission to continue. See `docs/P1-GQ/README.md`.
- NoCutoff is an exploratory candidate, not a certified formal MD protocol. Coarse Rg/Q is descriptive; fine fixed libraries still fail held-out representativeness and low-dimensional shape aliasing remains. `evaluation_ready=false`.
- Main science/analysis executed on server. Old S1/S2 integrity verified; stage report, compact evidence, archive and cleanup receipts distinguish local and GitHub contents.
- Stop for researcher/planning review. S2 independent final review remains INCOMPLETE. B1/B2/C effect studies and S3 remain NOT APPROVED; do not reuse the remaining 2671.303775s as a new authorization.


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

## 公開資料の日本語規範とGQ-R2の範囲（2026-10-26）

- **CONFIRMED**: 本研究の公開用コメント、docstring、README、利用案内、再現手順、技術資料、利用者向けメッセージは日本語を基本とする。英語の識別子・API・ファイル名は維持する。内部研究記録は中国語でもよいが、公開最終資料には完全な日本語版を用意する。既存の歴史報告や原証拠を一括上書きしない。詳細は `docs/collaboration-policy.md`。
- **CONFIRMED GQ-R2**: 物理的に意味のある局所構造多様性と新構造領域の探索を評価する。折り畳み・天然構造回復・準安定状態発見は必要目標ではない。既存16 ns NoCutoff軌跡のサーバCPU解析のみ承認。GPU計算、新MD、CVAE訓練/推論、B1/B2/C効果実験、S3は禁止。R1残GPU時間は再利用しない。
- 新しい系統的解析は `docs/P1-GQ-R2/analysis-plan.md` のcommit/push/遠隔確認後に行う。数値・図はサーバで作成する。完了後停止して審査を待つ。S2補充独立終審はINCOMPLETEのまま。

- GQ-R2は本輪終了後に閉鎖する。実行端判定は工学PASS、唯一の確認的科学指標NOT READY。`docs/P1-GQ-R2/README.md` の研究者審査を待ち、CPU解析も無断再実行しない。独立校正の提案は新計算許可ではない。

## B1 Pilot の最新承認（2026-10-26）

- **CONFIRMED**：研究者が1共同歴史（NoCutoff 2+2 ns）、F0/F1/F2、2対応乱数ブロック×下流4 ns（計24 ns）の探索的B1を承認。最新指示は旧R2の実行禁止に優先する。`docs/P1-B1-Pilot/analysis-plan.md` をGPU計算前にcommit/push/遠隔確認する。
- **CONFIRMED**：唯一の絶対的構象指標を前提にせず、事前固定した複数の解釈可能な物理代理指標で診断する。R2の負の結果/未確認の物理条件は保持する。B1は等MD量の効果であり固定wall-clock純利益ではない。
- **CONFIRMED長期GPU規則**：本研究のGPU研究計算は、研究者が今後明示しない限り人為的な総時間上限を設けない。旧GQ60分を適用しない。範囲/共有資源許可/単体異常監視/メモリ・保存量保護は必須で、時間無上限を範囲拡大と解釈しない。
- 本Pilot完了後停止。正式B1、B2、C予測/S3は未承認。日本語公開規範、本人領域のみの操作、旧証拠保護、S2独立終審INCOMPLETEを維持。

## B1 Pilot の数値計算完了・審査待ち（2026-10-26）

- **MEASURED**：新NoCutoff共通履歴4 ns＋下流24 ns、29成功/1配備失敗を記録した。F1/F2の共通初期モデル・optimizer・初期RNG・200歩/800サンプル提示、F0再推論、実MD投入座標、時刻合法性を検査した。旧証拠を保護する。
- **DERIVED**：F2−F1の平均幾何新規度差は−0.0478/+0.3588 Å、離散領域差も不一致。新データの安定した上乗せ改善はINCONCLUSIVE。同じ一状態の二乱数ブロックは、Cの科学状態依存効果の証拠ではない。工学完了は研究者受入れではない。
- 本Pilotの承認済み科学計算は終了した。バックアップ・清掃・同期の状態は個別の検証記録を確認し、追加解析/MD/学習を自動実行しない。次は研究者/計画側の審査のみ。正式B1/B2/C/S3未承認、S2独立終審INCOMPLETEを維持する。

- **MEASURED閉鎖**：B1の完全アーカイブはサーバ/Mac双方SHA一致、登録済み一時環境とキャッシュを清掃済み。原始証拠と旧結果を再照合した。詳細はB1報告のbackup/cleanup検証を参照。次の計算には新たな研究者承認が必要。

## B1 Expansion の承認（2026-10-26）

- **CONFIRMED**：研究者が8根×連続8 ns、4/8 nsの16状態、F0共有3本・F1/F2各2学習seed×3MDseed、各4 ns（下流240本/960 ns、履歴64 ns）を承認した。既存Pilot完了停止をこの範囲で更新する。唯一の絶対指標は要件としない。
- 事前計画・全乱数/順序/指標・X/Z/WをGPU計算前にpushし回読する。8祖先根を頂点単位とし、同根2状態と共有F0を独立複製としない。固定MD量でありB2純利益ではない。
- GPU合計の人為上限なし、共有資源の再検査・範囲・RSS/ディスク/単体異常保護は維持する。主数値はサーバ、Macは開発/同期/SHA。本人領域のみ、旧証拠は不変。
- X/Z/Wの前置診断のみ許可。正式C価値予測器/B2/オンライン方策/S3、16状態/240本を超える追加科学実験は未承認。今回全範囲を評価・保存・清掃・同期した後停止して審査を待つ。S2独立終審INCOMPLETEを維持する。
