# CPU解析スクリプトの設計（未実装）

2026-10-28 / PROPOSED。ここに示す関数・出力名は設計であり、実行可能な新解析プログラムは作成していない。旧科学ソースを修正せず、新しい独立モジュールに実装する案とする。科学数値は別途承認後にサーバCPUで生成し、Macは静的点検だけに使う。

## 1. 入出力と処理順

|工程/関数案|入力|処理・出力|
|---|---|---|
|`verify_inputs`|基準commit、raw/public SHA、matrix、events|読み取り専用の許可入力一覧。240枝/16状態/8根、atom順、finite/shape、凍結時刻を確認。`input-audit.json`|
|`build_reference_ids`|根ごとのH2/H4/H8、valid、ID|4参照法のIDとSHA、元時刻・公開時刻、根別集合関係。`reference-manifest.json`|
|`audit_selection_origin`|80 selected、indices、順位、枝要求|時間区間・訓練所属・P4所属・実枝対応。`selected-origins.csv`|
|`check_original_evaluation`|240元特徴、旧参照/旧結果|全枝の元計数・6連続値の再現検査。旧ファイルへ書込まない|
|`reevaluate_fixed_trajectories`|同じ240枝特徴、4参照法|全距離/最近傍ID、全12時間条件、全6離散条件、角差、窓/相関。原子再抽出/MDなし|
|`diagnose_pool_selection`|80保存embeddingとP4/P8|FULLのLOF再現、S8の2制限×2操作（score固定/再fit）、下流未観測flag|
|`summarize_hierarchy`|再評価表と実matrix|全2×3、共有F0、根効果、段階差、参照寄与恒等式、根bootstrap/根除外診断|
|`write_review_bundle`|全出力、入力audit、費用|全尺度図、完全表、欠損/失敗、SHA、日本語報告。科学受入れはPENDING|

データschemaの主キーは`reference_mode, root_id, state_id, arm, training_block, MD_block, branch_id, burn_ps, prefix_ns`。離散量は`epsilon_A,tau_ps`を加える。比較表は`comparison`を加え、元F0 branch IDを保持する。全出力にsource commit/SHA、処理版、作成時刻、PROPOSED設定採用の承認記録を付ける。

`pool-selection-diagnostic.csv`は`pool_mode, scoring_mode, checkpoint_sha256, embedding_sha256, candidate_ids_sha256, selected_frame_id, original_selected_retained, top10, top100, downstream_status`を持つ。実行済みY表と自動結合して反実仮想成果を作るAPIは設けない。

## 2. 既存処理の再利用と危険な入口

[expansion_analysis.analyze_branch](../../p1/server/expansion_analysis.py)はA0を内部で決めるので、引数を偽装して上書き実行しない。新wrapperが参照IDを明示し、元の時間mask・統計規則を保つ。`finalize_campaign`は全バッチの出力・監査を行うので、新参照を旧summary-v1へ流し込まない。

[gq_r2.nearest / regions / circular](../../p1/server/gq_r2.py)の固定計算規則を再利用する。距離はquery block64×参照全体で計算し、全1,920,000点×全履歴の距離行列を作らない。branch単位で配列を読み、根参照を共有する。元S4に対するCOMMON_A4等、同じ入力集合の結果は同じファイルを論理参照できるが、schema上の各条件は省略しない。

既存CVAEの[推論](../../vendor/mdlearn-938cb80/mdlearn/nn/models/vae/symmetric_conv2d_vae.py)はeval、[再パラメータ化](../../vendor/mdlearn-938cb80/mdlearn/nn/models/vae/model.py)はeval時に平均muを返す。今回のLOF設計ではそれでも保存済みembeddingに限定し、再推論同値性を実測したとは言わない。異なるモデルの潜在座標を直接引き算しない。共通frame ID上の順位・物理構造差で比較する。

CPUプログラムはTorch/OpenMM/CUDAを不要とし、学習・predict・MD runner・collectorをimport/起動しない。GPU不可視、数値threads1、同時worker1を初期案とする。旧ソースをimportする際もCLIやcontrollerに副作用がないことを確認する。

## 3. 将来の数値検査（本輪では実行しない）

|検査|受入れ規則案|
|---|---|
|原SHA/行列/ID/時刻|完全一致。不一致なら停止。未来情報を時計の付替えで合法化しない|
|元評価の再現|全整数・集合ID・代表/確認IDは完全一致。連続値は絶対1e−8（各元単位）+相対1e−10以内を計算再現の許容案とする。物理的等価幅ではない|
|距離実装|既存精度1e−12 Åの小部分dense/block照合、同一構造0、剛体不変、鏡像不識別を保持|
|H4⊆H8|ID/特徴一致。全枝のm_H8≤m_H4を数値誤差内で確認|
|不変対照|全参照法で同一branch/windowのRg/Q8/eligible frame IDを一致させる|
|参照寄与|全根/比較/指標でΓN−ΓC4=Erefを照合。角/離散には距離の単調性を強制しない|
|LOF FULL|元配列/ソートIDと再fitを比較。scoreは絶対/相対1e−10の許容案、Top1/順位不一致は近接tieも含め別記し当該再順位解析を停止。元dtypeを保持|
|合成fixture|不変A、入れ子A、空集合、mask欠損、既知tie、共有F0、root/state重複を検査。失敗を0効果にしない|
|交付完全性|4参照法それぞれ2,880連続行/17,280離散行と全比較。本文に6連続量・6離散尺度を掲載|

原結果の差が許容外なら新結果を正しいとして旧CSVを修正しない。環境/浮動小数/索引誤りを調査し、追記型の不一致報告で停止する。許容値自体も実行前に研究者が承認するPROPOSED値である。

## 4. 今回行う静的点検との区別

本輪で行うのはMarkdownリンク、CSV全行の構文/列/件数、JSON構文、入力文書/SHA一覧、Git変更範囲、旧科学ソース/旧結果の不変確認だけ。CSVから効果・相関・bootstrapを再算出せず、NPZを開かず、LOF/nearest/regionsを呼ばない。点検結果は[static-checks.json](static-checks.json)に保存する。数値検査PASSを先に書かない。
