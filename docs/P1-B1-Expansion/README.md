# B1 Expansion：完了結果と科学審査の入口

2026-10-27。**科学計算COMPLETE、文書作成完了、研究交付PARTIAL。独立科学審査・研究者受入れはPENDING。** 8根/16状態/240下流MD・評価、共通履歴64 ns＋下流960 nsを完了。科学task成功1,024/失敗0、共有資源保護停止2回。サーバ9archiveは生成済みですが、Mac完全検証backupは0/9で清掃も未実施です。

最初に[完全科学審査報告（18項目）](review-dossier.md)と[ChatGPTへの固定引継ぎ（A–G）](handoff-to-chatgpt.md)を読んでください。[教員向け日本語概要](supervisor-summary-ja.md)も用意しました。

主幾何量の全体F2−F1は−0.0141 Å、探索的95%区間[−0.2092,+0.2105] Å（8根、下流4 ns/先頭100 ps除外）。S4−0.3636 Å/S8+0.3355 Åの時点差を認めますが、候補数・学習窓・M0・評価A0も異なります。一般的なF2優位、科学状態Xの独立価値、B2の等wall-clock純利益はまだ結論できません。

## 最終報告と証拠

|主題|資料|
|---|---|
|目的・全18要件・結論の限界|[review-dossier.md](review-dossier.md)|
|別助手が読む固定入口|[handoff-to-chatgpt.md](handoff-to-chatgpt.md)|
|全3比較・連続/離散・根/状態値|[paired-results.md](paired-results.md)|
|学習seedとMDseedの変動|[randomness-analysis.md](randomness-analysis.md)|
|S4/S8・決定前X/Z/W・Cの未検証部分|[state-dependence-analysis.md](state-dependence-analysis.md)|
|時間合法性と祖先|[data-lineage.md](data-lineage.md)|
|M0/optimizer・全16状態seed|[model-training.md](model-training.md)|
|参照なしLOF・起点の構造差|[candidate-selection.md](candidate-selection.md)|
|物理代理の式・単位・適用範囲|[scientific-metrics.md](scientific-metrics.md)|
|粗品質・完全性・保存ゲート|[data-quality.md](data-quality.md)|
|統計単位・交絡・外挿|[statistical-limitations.md](statistical-limitations.md)|
|GPU/CPU/wall・archive/backup|[cost-and-runtime.md](cost-and-runtime.md)|
|失敗・復元・名称訂正|[failures-and-amendments.md](failures-and-amendments.md)、[implementation-errata.md](implementation-errata.md)|
|図表と数値・交付点検|[figure-and-table-audit.md](figure-and-table-audit.md)、[delivery-audit.md](delivery-audit.md)|
|固定版の再現と入力依存|[reproduce.md](reproduce.md)|
|日本の指導教員向け概要|[supervisor-summary-ja.md](supervisor-summary-ja.md)|
|次の判断（PROPOSED）|[next-stage-recommendation.md](next-stage-recommendation.md)|
|時点別の工程履歴・旧自動収集|[execution-progress.md](execution-progress.md)、[automatic-collection-status.md](automatic-collection-status.md)|

## 変更しない事前登録資料

[analysis-plan](analysis-plan.md)、[全行列](experiment-matrix.md)、[CSV](experiment-matrix.csv)、[JSON](experiment-matrix.json)、[乱数](randomization-plan.md)、[指標契約](metric-contract.md)、[系譜計画](data-lineage-plan.md)、[資源/復元](resource-and-recovery-plan.md)、[実機前検証](implementation-and-preflight.md)、[交付要件](review-delivery-requirements.md)。主実装は既存OpenMM/mdlearn/DeepDriveMD科学部品とParsl適応層で、S1/S2原証拠を保護しています。

今回の追加作業は報告と既存表CPU照合だけです。新MD・訓練・GPU推論・転送再開はありません。B1は等MD量の効果で、B2/C正式予測/オンライン方策/S3は未承認。S2独立終審もINCOMPLETEです。交付後は研究者・計画側の審査を待ちます。
