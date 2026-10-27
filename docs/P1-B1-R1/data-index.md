# 必要な既存データと利用可能性

2026-10-28。本輪はGitHub checkoutの読取り・schema点検だけを行った。サーバに接続せず、rawを展開していない。サーバ9archiveの実在/SHAは[前回の検証](../执行证据/2026-10-26-b1-expansion/storage-policy-server-verification-20261028.json)に基づく履歴であり、R1当日の新たな実在確認ではない。

基準commit `e7f438c074d02452d57b7602bba810173b22f9b1`。機械可読の[input-inventory.json](input-inventory.json)は、読取入力のbyte数/SHA-256、全関連CSVの列・全行走査件数、必要raw相対名と既存SHAを記録する。科学統計の再集計ではない。

## GitHubにある小型資料

|入力|粒度・使用目的|
|---|---|
|[experiment-matrix.csv](../P1-B1-Expansion/experiment-matrix.csv) / [JSON](../P1-B1-Expansion/experiment-matrix.json)|240予定枝、根/状態/T/M/実seed/順序。ID結合の基準|
|[branch-status.csv](../执行证据/2026-10-26-b1-expansion/branch-status.csv)|240枝の既存完了状態|
|[continuous.csv](../执行证据/2026-10-26-b1-expansion/continuous.csv)|2,880行、6連続量と12時間条件。旧値の再現基準|
|[discrete-counts.csv](../执行证据/2026-10-26-b1-expansion/discrete-counts.csv)|17,280行、全6尺度。代表座標は含まない|
|[paired-effects.csv](../执行证据/2026-10-26-b1-expansion/paired-effects.csv)|41,472行、3比較の全セル・共有F0 ID|
|[state-effects.csv](../执行证据/2026-10-26-b1-expansion/state-effects.csv) / [root-effects.csv](../执行证据/2026-10-26-b1-expansion/root-effects.csv)|6,912状態行/3,456根行|
|[state-time-differences.csv](../执行证据/2026-10-26-b1-expansion/state-time-differences.csv) / [root-summary.csv](../执行证据/2026-10-26-b1-expansion/root-summary.csv)|3,456同根差/432根要約。原探索区間を保存|
|[report-main-root-effects.csv](../执行证据/2026-10-26-b1-expansion/report-main-root-effects.csv)|24行、主条件の3比較。今回本文の既報数値の出典|
|[selection-comparisons.csv](../执行证据/2026-10-26-b1-expansion/selection-comparisons.csv)|96比較、global ID・構造差・Top-k。全embeddingや全順位ではない|
|[features.json](../执行证据/2026-10-26-b1-expansion/features.json) / [feature-variation.csv](../执行证据/2026-10-26-b1-expansion/feature-variation.csv) / [state-diagnostics.csv](../执行证据/2026-10-26-b1-expansion/state-diagnostics.csv)|16 X/Z/W、10特徴変動行、120既存相関。Cを新規学習しない|
|[randomness-decomposition.json](../执行证据/2026-10-26-b1-expansion/randomness-decomposition.json)|既存2×3記述。独立な新反復ではない|
|[models.json](../执行证据/2026-10-26-b1-expansion/models.json) / [checkpoint-readback.json](../执行证据/2026-10-26-b1-expansion/checkpoint-readback.json)|80モデルの初期/最終/親/optimizer digestと既存復元証拠。重みの再loadは不要|
|[quality.json](../执行证据/2026-10-26-b1-expansion/quality.json) / [time-windows.csv](../执行证据/2026-10-26-b1-expansion/time-windows.csv) / [autocorrelation.json](../执行证据/2026-10-26-b1-expansion/autocorrelation.json)|240品質記録、9,600時間窓、元自己相関。平衡資格と区別|
|[task-manifest.json](../执行证据/2026-10-26-b1-expansion/task-manifest.json) / [events.json](../执行证据/2026-10-26-b1-expansion/events.json) / [temporal-and-SHA-audit.json](../执行证据/2026-10-26-b1-expansion/temporal-and-SHA-audit.json)|1,024要求・結果、公開時計、凍結情報集合。物理psとmonotonic壁時計を混同しない|
|[raw-artifact-sha256.json](../执行证据/2026-10-26-b1-expansion/raw-artifact-sha256.json) / [public-export-index.json](../执行证据/2026-10-26-b1-expansion/public-export-index.json)|raw15,208相対名/SHAと公開名の対応。公開JSON匿名化後SHAはrawと異なる|
|[costs.json](../执行证据/2026-10-26-b1-expansion/costs.json) / [GPU-diagnostics.csv](../执行证据/2026-10-26-b1-expansion/GPU-diagnostics.csv) / [report-review-statistics.json](../执行证据/2026-10-26-b1-expansion/report-review-statistics.json)|既報費用の引用と見積りの根拠。今回は測り直さない|

## 許可サーバだけにある入力

論理バッチは`b1-expansion-20261026`。以下はバッチ内相対名であり、ホスト・絶対パス・利用者情報を公開しない。各項はraw SHA索引の実エントリに照合する。新規抽出先は原ディレクトリ外とし、archiveを更新/削除しない。全量をMacへ転送しない。

|相対名の型|必要内容・想定数|用途|
|---|---|---|
|`tasks/{state}-decision-pool/science/features.npz`|16。`distances_A, angles_rad, ca, rg_A, q, time_ps, valid`|H4/H8、A2抽出、候補物理形状。実際の配列shape/単位は実行許可後に検査|
|`tasks/{state}-decision-pool/science/indices.json`|16。old/new/validation/F1/F2/candidate ID|候補集合・訓練所属・Kの基準|
|`tasks/{branch}-md-prep/science/features.npz`|240。各8,000点の同じ特徴/品質列|共通参照での再評価。原DCD再処理を原則不要にする|
|`tasks/{branch}-analysis/science/distances.npz`|240。d_min_A、nearest_A0_id、time_ps、valid|元評価の数値読戻し。これ単独から別参照への距離は復元できない|
|`tasks/{branch}-analysis/science/discrete.json`|240。全尺度の代表/確認ID・時刻|元のgreedy計数の一致検査|
|`tasks/{state}-infer-{label}/science/ranking.npz`|label=F0,F1-t1,F1-t2,F2-t1,F2-t2：80。別にF0-repeat16|`frame_ids, embedding, lof, order`。新CVAE推論なしのLOF診断|
|`tasks/{state}-selection/science/selected.json`|16、計80選択|frame/time/segment/local、選点座標SHA、DCD SHA、checkpoint SHA|
|`tasks/{state}-selection/science/{label}.npy`|80全原子起点|起点の不変性。必要時だけ読取|
|`tasks/{state}-{label}/science/recipe.json`, `exposure.json`, `loss.json`|M0,F1/F2各2、計80モデル|学習条件/提示ID/元lossの資格資料。再訓練しない|
|`tasks/{branch}-md/request.json`, `initial-coordinates-A.npy`（後者はscience内）|240|実MD条件・入力同一性を確認。近い構造から成果を流用しない|

例として`tasks/r01-s4-F0-t0-m2-md-prep/science/features.npz`は既存索引に存在し、SHAは`a37be63d1b48070f0aca82e97817d8f729b659977554f0843d2eaed71682b3ce`。未検査のraw内容を本輪で読んだとは主張しない。タスク名の`-md-prep`を`-prepare`と推測で置換しない。

## 何がこの索引だけではできないか

公開CSVの平均・中央値・p90、旧最小距離配列だけから、別Aへの最近傍とgreedy代表を復元できない。全候補scoreをフィルタするだけでは縮小集合LOFにならない。保存embeddingの不在をCPU再推論で補うことも今回の案の範囲外である。必要rawが欠ければその分析を停止し、失われた値を推定で埋めない。

根archive r01…r08とmetadataの対応は[元archive索引](../执行证据/2026-10-26-b1-expansion/post-compute-status-20261027.json)を利用する。既存の展開済み本人データが残る場合はSHA確認して直接読む。追加展開の必要性/容量は実行前に確認し、丸ごと複製しない。Mac原archive免除はサーバ原archive削除の許可ではない。
