# P1-L2：CVAEの学習量と潜在表現を切り分ける最小実験設計

2026-10-29 JST。基準：`83bac631c007366d1492330fe3355677d4f5eeaf`。
**本輪は設計・証拠読取り・静的点検だけである。実験の実行はNOT APPROVED。**

L1では、更新したCVAEの最近データの再構成が改善する一方、潜在近傍と物理近傍の一致や更新seed間の安定性には限界があった。L2は、これが200歩という学習量、初期重み、再構成目的と物理幾何の違いのどれに関係するかを、既存データ上で調べる工程診断案である。CVAEは **convolutional variational autoencoder（畳み込み変分自己符号化器）** を意味する。

提案は、既知の4状態（r01/r02のS4/S8）×3独立初期化×M0/F1/F2、計36学習chainである。各chainの200/400/800/1600歩を保存し、合計57,600新規optimizer steps、144学習済み評価点と12未学習対照を得る。M0の長期学習と、固定M0-200からのF1/F2追加学習を分け、最良の親モデルを結果から選ばない。これは2歴史根の開発診断であり、未知根での確認実験ではない。

|資料|役割|
|---|---|
|[分析計画](analysis-plan.md)|問い、既存証拠で分かること、固定因子、時刻合法性、統計単位|
|[実験行列と乱数仕様](experiment-design.md)|36chain、156評価点、固定親、初期化と更新seedの分離|
|[指標契約](metric-contract.md)|再構成、頻度基線、入力依存性、潜在幾何、安定性、LOF|
|[判定基準](decision-criteria.md)|技術PASSと限定科学支持、FAIL/INCONCLUSIVE、主張の上限|
|[費用・実行範囲](cost-and-scope.md)|既測値に基づく概算、共有資源、停止・保存・再開条件|
|[将来の実装設計](script-design.md)|実行前監査、出力schema、乱数保存、再現検査|
|[リスクと未識別要因](risks-and-unidentified.md)|時間相関、既知データ、因子交互作用、物理資格|
|[証拠・原著索引](evidence-and-sources.md)|内部証拠、固定版ソースコード、一次資料と読取り範囲|
|[A–G引継ぎ](handoff-to-chatgpt.md)|独立審査の固定入口、承認待ち事項|
|[実行依頼案](proposed-execution-prompt.md)|研究者が別途承認する場合の依頼文。現在は実行不可|

機械可読の設計表は [36chain](experiment-matrix.csv)、[156評価点](checkpoint-matrix.csv)、[訓練membership](training-membership.csv)、[OLD/RECENT評価ID](evaluation-ids.csv)。これらは結果ではなく、既存IDの転記と予定条件である。[静的交付検証](delivery-validation.json)は文書/行列/旧証拠不変性の点検であり、科学資格の合格ではない。[入力文書SHA](evidence-input-sha256.json)は基準版を特定する。

本輪に新たなMD・学習・前向推論・LOF・科学再解析・サーバ接続はない。B1/R1/Q0/L1の科学データ・報告・凍結コードを変更せず、Mac原archive免除とサーバ原archive保持を維持した。L2の計算、P/O/C/B2/S3、科学的受入れは自動承認しない。
