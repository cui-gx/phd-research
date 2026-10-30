# P1-N1：天然構造評価・資源制約下の意思決定実験の準備

2026-10-30 JST。基準main `73b93ed`（完全SHAは[入力版](preparation-status.json)）。**PREPARATION_ONLY / SCIENTIFIC_EXECUTION_NOT_APPROVED**。文献原文・固定ソース・既存ファイルのbyte SHA/頭部/文字列対応を確認し、人工座標の単体検査だけを行った。新MD、訓練、実座標への推論・LOF・RMSD/Q評価は0。

|入口|内容|
|---|---|
|[準備報告](preparation-report.md)|指導助言、実施した準備、重要な修正、判定と残件|
|[RMSD/Q契約](native-metric-contract.md)|proper Kabsch、二つのQ、全窓、時刻・不確実性・漏洩|
|[先行研究対照](related-work-matrix.md)|物理条件・機構・実測・適用可能な基線・未実証差異|
|[データ・実行準備](data-readiness.md)|8根/16状態/240枝、32履歴、原子対応・保存embeddingの境界|
|[C/B2最小案](cb2-minimal-design.md)|将来の予測情報とオンライン方策の別推定対象|
|[資源・時間計量](resource-and-timing.md)|単GPU直列、並行の資格ゲート、全費用と締切|
|[判定・停止](decision-and-stop.md)|成功/不成立/不確実/要追加承認|
|[証拠と新計算境界](evidence-boundary.md)|何を確認したか、何をしていないか|
|[再現・境界](reproduce.md)|人工検査・metadata監査と今後の未実装範囲|
|[指導教員向け概要](supervisor-summary.md)|短い日本語説明と相談事項|
|[A–G引継ぎ](handoff-to-chatgpt.md)|独立審査の固定入口|

全科学方法・将来件数・予算はPROPOSEDで、研究者が採択した実験条件ではない。旧B1/R1/Q0/L1/L2/N0と指導助言の原記録は変更しない。B1新評価は実行を承認された場合もPOST_HOC_EXPLORATORY。サーバ9archiveを保持し、Mac raw全量バックアップを再要求しない。交付後は審査で停止する。

## 後続の限定CPU実行（2026-10-30）

研究者が別途承認した[CPU-v1完全交付](CPU-v1/README.md)が最新。上記の準備時点の実行0/未承認は正しい履歴として保持する。新規計算へ進まず独立審査を待つ。
