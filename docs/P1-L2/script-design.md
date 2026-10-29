# 将来実装の設計と静的受入条件

2026-10-29、PROPOSED。以下のプログラム名・出力名は実装案であり、現時点に実行可能コードが存在するとは主張しない。本輪は訓練・推論・LOFのコードを追加していない。

## 1. 原コードを保護する構成

将来は独立したL2 adapterを新規作成し、既存mdlearnクラスを固定版で利用する。B1の`b1_science.py`やL1診断器へ機能を埋め込まない。共通数式を参照しても旧ファイルは変更しない。計画commit、実装commit、入力freeze commit、実行環境、最終報告commitを別記する。

|工程案|入力|出力・検証|
|---|---|---|
|inventory / freeze|原B1 decision-pool、Q0系譜、L1 SHA、設計CSV|80原checkpointの索引を保持し、使用4状態の実ファイルSHA/shape/ID/時刻/atom順を再検査。新recipe、8epoch exposure予定、実環境、必要容量を凍結|
|train-chain|行列1行、凍結membership/recipe、指定親snapshot|M0-step0、200/400/800/1600、完全RNG/optimizer、逐step loss、実exposure、費用/失敗。親のmodel/optimizerの一致|
|evaluate-checkpoint|読み取り専用checkpointと固定2集合|決定的mu/logstd/reconstruction、頻度/平均コード/入替え、幾何。SHA前後一致と二回前向一致|
|rank-full-pool|読み取り専用checkpointと原FULL ID|CPU chunk前向、RAW mu、156予定fitのscore/rank/Top1。候補/密度を固定|
|summarize / audit|全セルmanifestと派生表|全対応差、根/状態/seed階層、欠測台帳、費用、入力/出力SHA。下流Y表は入力禁止|

新実装の日本語docstring/コメント/利用案内、全英語識別子を維持する。既存依存版は[環境記録](../P1-L1/execution-status.json)とB1ロックを参照し、科学計算前に実サーバで照合する。新しいlibrary版で古い値を再現したと主張しない。

## 2. 凍結前に必要な検査

1. `[training-membership.csv](training-membership.csv)`の位置順800 IDが原indicesの各臂と一致し、F1とM0が同じ、F2の旧/新構成が旧仕様と一致すること。
2. `[evaluation-ids.csv](evaluation-ids.csv)`の200+200 ID/時刻がL1と完全一致し、訓練と非重複、当該判断時点より後のIDがないこと。float時刻の既存精度処理は元判定に従い、境界を丸めて新点を追加しない。
3. 4状態FULL候補7,800/15,800の原ID/SHA、原子・残基順、325距離feature単位Åを確認する。DCD再処理は不要で、本L2に追加しない。
4. 旧80checkpointの系譜索引を保ち、未使用モデルを学習対象としてロードしない。既存全80SHAのL1監査は既報であり、L2でサーバ全archiveを再hashした証拠にしない。L2使用入力の実SHAだけを新規確認する。
5. 原mdlearn/学習クラスのSHA、RMSpropの全param_groups、clip、dtype、batch・device、Torch/NumPy/sklearn/CUDA/driverを記録する。MIGやGPU二枚構成を前提としない。

不足/不一致があれば実行前に停止する。サーバ入力実SHA、初期化後weight SHA、順序/RNG digestはまだ取得していないため、現在のCSVに架空値を埋めない。

## 3. RNG、checkpoint、実装テスト

model構築による乱数消費と学習streamを分離する。親M0-200をdeep copyしてF1/F2に渡し、親ファイルをimmutableにする。CPU診断は別processで行い、train modeやRNGへ影響させない。保存時点のRNGにPython、NumPy generator、Torch CPU/CUDA、DataLoader generatorを含める。epochの順序だけでなくbatch位置を保存する。

将来の実装時には、実科学データを使わない小さい人工tensorにより、連続訓練とsave/resumeが同じ条件で一致すること、checkpoint保存・評価を挟んでも学習streamが変わらないことを検査する。この検査の実行も現在は行っていない。GPU決定性設定が同環境で未対応なら黙ってoffにせず記録・停止する。異機種間bit一致は要求しない。

原目的のBCE総和とKL平均をそのまま使いながら、独立診断列を保存する。forwardだけの読み取りprocessではbackward/optimizer.stepを拒否するguardを使用する。FULL候補の大きな全対距離行列を作らず、embedding/LOFのメモリを監視する。物理全対幾何は評価集合200点だけに限定する。

## 4. 将来の出力schema

|ファイル案|主キー・重要列|
|---|---|
|run-manifest.json|設計/コードcommit、状態、init_seed、optimization_seed、permutation_seed、device、versions、入力/親SHA、承認情報|
|chain-events.jsonl|chain_id、時刻、step、イベント、試行、費用、故障理由。append-only|
|loss-steps.csv|chain_id、追加/lifetime step、epoch、batch位置、raw_total、BCE_sum、KL_mean、BCE/frame、BCE/element、grad_norm、finite|
|exposures.csv|chain_id、epoch、提示順、元position、global frame ID。全230,400提示を追跡|
|checkpoint-audit.csv|checkpoint ID、SHA、model/optimizer/RNG digest、step、parent、前後不変、実行/欠測理由|
|model-metrics.csv|checkpoint、OLD/RECENT、mask、全BCE基線/ablation、分母、KL/幾何/NA理由。156×2×3=936論理行|
|latent-diagnostics.csv|checkpoint、集合、次元、mu平均/母分散、E sigma²、KL、3固有値、finite|
|paired-contrasts.csv|状態、init、臂、step対/臂対、集合、mask、元値と差。複数比較を省略しない|
|initialization-stability.csv|状態/臂/step、全3init対、距離rank、K10、対内BCE/幾何差|
|ranking.npz / selection-summary.csv|全候補ID/score/order/mu、Top1/10/100、由来時刻、score gap、対間d_phys、NOT_OBSERVED|
|cost-ledger.json / failures.json|wall/CPU/GPU使用時間の区別、peakRSS/VRAM、disk、待機、再試行、未完了分母|
|SHA manifest / review-dossier / handoff|compact証拠とserver raw索引、全条件・陰性・限界、A–G、遠隔回読|

モデル単位値を集約する前に、完全行列とのouter joinで欠測を可視化する。同じモデルの別mask、step、子aliasを独立サンプルとして重み付けしない。報告と図は同じ機械可読表から生成する。
