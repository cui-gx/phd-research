# P1-L1：凍結モデル表現資格診断

2026-10-29。80/80モデルのCPU前向診断COMPLETE、実行完全性PASS、科学的資格は限定的/審査待ち。新訓練/MD/LOFなし。

- [完全報告](review-dossier.md)、[A–G引継ぎ](handoff-to-chatgpt.md)、[事前計画](analysis-plan.md)、[再現](reproduce.md)
- [80モデル×二集合×三掩码](model-metrics.csv)、[16状態の全臂表](state-metrics.csv)、[32,000 frame診断](frame-diagnostics.csv)
- [潜在診断](latent-diagnostics.csv)、[固有値](covariance-eigenvalues.csv)、[seed安定性](seed-stability.csv)、[幾何要約](geometry-overview.csv)
- [6,400 ID](validation-ids.csv)、[凍結集合](frozen-cohorts.json)、[原SHA](freeze-input-sha256.json)、[80 checkpoint監査](checkpoint-audit.csv)
- [再構成要約](overview.csv)、[r07-s4全比較](r07-s4-case.csv)、[全記述JSON](summary.json)、[cost](cost-ledger.json)、[status](execution-status.json)
- [追加配列SHA](array-sha256.json)、[派生SHA](output-sha256.json)、[異常・欠測](failures-and-missing.json)

再構成全配列と原モデルは許可サーバ保持。GitHubは小型表・図・SHA・コード。原B1/R1/Q0と9archive不変。次は独立審査のみ。
