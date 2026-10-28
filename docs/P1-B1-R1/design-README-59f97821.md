# P1-B1-R1：評価基準と段階差の方法論的再検討

2026-10-28。**設計・文書のみの交付。再解析、MD、学習、推論は未実施。** 研究者の本タスク指示はCONFIRMED、以下の再評価方法・費用・実装案はPROPOSEDであり、実行承認ではない。

読取基準：GitHub main `e7f438c074d02452d57b7602bba810173b22f9b1`。凍結科学ソースは `40a911e1f36d1365fc5ee7d8753a7feb1edd964d`。元の[完全報告](../P1-B1-Expansion/review-dossier.md)、[引継ぎ](../P1-B1-Expansion/handoff-to-chatgpt.md)、[指標契約](../P1-B1-Expansion/metric-contract.md)を変更しない。

## 今回の判断

既存軌道を同じ履歴参照で測り直せば、S4/S8の差に含まれる**評価基準変更の数値的寄与**を調べられる。一方、当時の候補集合・学習窓・M0・起点は変わらないため、これだけで科学フィードバックXの独立効果を同定できない。候補集合を制限したLOFの再計算は選択機構の感度分析であり、その新しいTop1からのMD成果は未観測である。

既報の主平均距離Δ21はS4 −0.363607 Å、S8 +0.335459 Å、同根差+0.699065 Å（8/8根で正）。これは[既存CSV](../执行证据/2026-10-26-b1-expansion/report-main-root-effects.csv)と[既報統計](../执行证据/2026-10-26-b1-expansion/report-review-statistics.json)の引用で、今回の再計算結果ではない。新しい共通参照でこの傾向が残るかはUNVERIFIED。

## 読む順番

1. [事前再検証計画](analysis-plan.md)：推定対象、共通参照、全指標、階層統計、時間合法性。
2. [必要データ索引](data-index.md)：GitHubとサーバrawを分離し、実ファイル名・SHA索引・欠損時の扱いを記載。
3. [解析スクリプト設計](script-design.md)：まだ実装しないCPU専用処理、出力schema、静的/将来の数値検査。
4. [判定基準](decision-criteria.md)：支持、測定交絡の弱化、反証、C未識別を区別。
5. [費用と実行範囲案](cost-and-scope.md)：根拠つきの見積り。測定値や計算許可ではない。
6. [未識別交絡と独立資格ゲート](unidentified-confounders.md)：MD物理条件・CVAE学習十分性を別審査にする。
7. [出典と読取範囲](sources-and-review-notes.md)、[静的入力目録](input-inventory.json)、[静的点検](static-checks.json)。
8. [ChatGPT引継ぎ](handoff-to-chatgpt.md)、[承認後のみ使用する実装依頼案](proposed-execution-prompt.md)。

「事前」は**新たな再評価の開始前**を意味する。既報の結果を知った上で組む事後感度分析であり、B1当初の事前登録や盲検・独立検証への格上げではない。本設計を独立した第三者による科学審査の合格と呼ばない。

本交付後は研究者・計画側審査で停止する。B1の技術交付COMPLETE、独立科学審査PENDING、研究者科学受入れPENDINGを維持し、B2・C予測器・S3へ進まない。Mac raw backupの免除とサーバ原archive保持も変更しない。
