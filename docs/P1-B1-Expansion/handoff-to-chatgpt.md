# ChatGPTへの固定引継ぎ：P1-B1 Expansion

2026-10-27。最初にこの文書、次に[完全審査報告](review-dossier.md)を読む。会話の記憶を前提にしない。科学計算は終わったが、研究交付はPARTIAL。計画側の独立科学審査と研究者受入れを依頼する。新しい計算の依頼ではない。

## A. 現在の状態と版

**報告本文の固定版：b77d7110a8a78fd66c32438b3f99507061472fe4（GitHub遠隔回読済み）**。本版以降は回読証跡の追記。最後の同期commitは最終返信/Git履歴とdelivery-verification.jsonで照合する。

バッチ `b1-expansion-20261026`。確認時刻：サーバCPU表再照合23:25 JST、ローカル保存23:27 JST。最終文書のGitHub反映はpush後の遠隔回読で確認し、[交付監査](delivery-audit.md)・同ディレクトリの同期証跡・Git履歴・最終返信の実在SHAを照合する。commit自己参照を事前に捏造しない。手元のcheckoutでは `git log -1 --format=%H -- docs/P1-B1-Expansion/handoff-to-chatgpt.md` と `git rev-parse HEAD` を区別して確認できる。

|段階|状態と実績|
|---|---|
|科学計算|COMPLETE：8根/16状態/240 MD/240評価、1,024成功task、失敗0、未実施0|
|MD量|共通履歴64 ns、下流960 ns。合計1,024 nsは分枝合算|
|工程保護|共有CPU/メモリゲート停止2回、SHA確認後同条件復元。科学失敗とは別|
|サーバ全体集計・時間/SHA監査|COMPLETE、passed、結果SHA不一致0|
|既存表のCPU再照合|PASS、科学妥当性の独立審査ではない|
|サーバ原archive|9/9生成済、20,223,932,863 bytes、SHA索引あり|
|Mac原archive完全複製|0/9、103,972,864 bytesの未検証断片のみ|
|収集と清掃|収集はNEEDS_VPNで退出。VPN復旧後も再開なし、清掃未実施|
|二文書と主題別資料|本輪で完成。内容・リンク・図表整合の技術点検を実施|
|保存/清掃を含む研究交付全体|PARTIAL|
|独立科学審査 / 研究者受入れ|PENDING / PENDING（本報告でPASSにしない）|
|S2独立終審 / S3|INCOMPLETE / NOT APPROVED|

版：事前計画 `060c72e981234a652deae7f3d8db2f4f2dfd4724`、凍結実行科学ソース `40a911e1f36d1365fc5ee7d8753a7feb1edd964d`、結果公開 `344d59d995c2f9b99d6ced600440662ea3481edb`、保護取込 `a61792baf742bde8ce7fd03702644ff6ad929bb5`、CPU報告照合 `4771d2197af3e90609375ff3f8708cc2d3797395`。以後の文書版を実験実行版に置き換えない。

GitHubにはコード・凍結仕様・小型表/JSON/3図・SHA索引を反映。全DCD・80モデル重み・埋込み・全順位・原ログは許可保管先のみ。公開JSONとraw JSONは脱敏によりSHAが違う。完全rawがMac/GitHubにあるとは述べない。[保存実測](../执行证据/2026-10-26-b1-expansion/report-backup-status.json)。

## B. 確認事項と状態ラベル

- **CONFIRMED**：研究者が8履歴根×8 ns、S4/S8、F0共有3本、F1/F2各2T×3M、下流240×4 nsを承認。対象FSD-EY/1FME・OpenMM・既存mdlearn CVAE・1 RTX PRO6000 96GBを維持。Cが主線、Bを共同設計する方針は不変。[AGENTS](../../AGENTS.md)、[事前計画](analysis-plan.md)。
- **CONFIRMED**：今回の追加許可は文書と既存統計CPU照合。未完了backupと並行してよい。転送の再開・中断・重複起動、追加MD/訓練/GPU推論は禁止。
- **MEASURED**：240/240枝、1,024成功task、粗合格1,920,000点、選択座標一致240枝、80checkpoint読戻し、時間/SHA監査passed、9サーバarchiveと0/9Mac完全複製。[validation](../执行证据/2026-10-26-b1-expansion/validation.json)、[品質](../执行证据/2026-10-26-b1-expansion/quality.json)、[checkpoint](../执行证据/2026-10-26-b1-expansion/checkpoint-readback.json)。
- **DERIVED**：下記の対応差、bootstrap、SD/残差、相関、コスト分類と実行端解釈。研究者の最終科学結論ではない。[CPU報告統計](../执行证据/2026-10-26-b1-expansion/report-review-statistics.json)。
- **PROPOSED**：状態束の識別設計、物理/学習配方の資格確認、独立rootでのC/B2確認設計。承認待ち。[次段階案](next-stage-recommendation.md)。
- **UNVERIFIED**：初期unfolded作成史・pH・十分な平衡、唯一の科学的成果指標、一般CVAEへの外挿、XのZ/W条件付き増分価値、固定wall-clock純利益、完全双端原archive一致。未確認を工程PASSで埋めない。

## C. 主要科学結果

主量は同状態履歴A0への325対Cα距離dRMSD最小値の平均[Å]、下流4 ns/先頭100 ps除外。正の差は代理が大きいことを意味し、折り畳みや生物学的価値ではない。8根が頂点統計単位。

|比較|根平均差 [Å]|探索的95%区間 [Å]|正/負の根数|
|---|---|---|---|
|F2-F1|-0.0141|[-0.2092, +0.2105]|3/5|
|F2-F0|-0.2036|[-0.4258, +0.0278]|2/6|
|F1-F0|-0.1895|[-0.4975, +0.0893]|3/5|

|比較|S4平均 [Å] (95%区間)|S8平均 [Å] (95%区間)|同根S8−S4 [Å] (95%区間)|時間差が正の根|
|---|---|---|---|---|
|F2-F1|-0.3636 [-0.6769, -0.0310]|+0.3355 [+0.0889, +0.5419]|+0.6991 [+0.3340, +1.0685]|8/8|
|F2-F0|-0.6170 [-1.1058, -0.0773]|+0.2098 [+0.0312, +0.3909]|+0.8268 [+0.1820, +1.4168]|6/8|
|F1-F0|-0.2534 [-0.6888, +0.1400]|-0.1256 [-0.3921, +0.1429]|+0.1278 [-0.2775, +0.4825]|6/8|

|根|S4 Δ21 [Å]|S8 Δ21 [Å]|根平均 [Å]|S8−S4 [Å]|
|---|---|---|---|---|
|r01|+0.2132|+0.5978|+0.4055|+0.3847|
|r02|-0.7784|+0.4809|-0.1487|+1.2593|
|r03|-1.0904|+0.4062|-0.3421|+1.4966|
|r04|-0.4786|-0.2299|-0.3542|+0.2488|
|r05|-0.4840|+0.3569|-0.0636|+0.8410|
|r06|-0.1761|-0.1679|-0.1720|+0.0082|
|r07|-0.5361|+0.6116|+0.0378|+1.1477|
|r08|+0.4216|+0.6279|+0.5247|+0.2063|

区間は根bootstrap10,000回/seed1604000001、探索的、多重性補正/等価性/検出力の認定なし。全体F2優位は未確認。S8−S4が8/8正でも、S8のr04/r06はΔ21負、S4のr01/r08は正。候補数・訓練窓・M0・A0も時点で変わる。

F2/F1 Top1相違32/32、起点距離平均3.7035 Å、各臂15/16状態で学習seedによってTop1変更。決定変更と下流改善は分ける。全6離散条件でΔ21区間は0を含み、根の正/負は4/4、ε1.5/2 Åでは全体平均負、3 Åでは正。全3比較・全指標・全感度は[対応結果](paired-results.md)から追える。

学習とMD乱数を交差させたが2×3各セル1本で純粋な交互作用分散は識別不能。例r07-s4の学習行平均差+2.7646 Åは状態平均−0.5361 Åより大きい。XのJSとΔ21の相関はS8−0.8095に対しS4+0.0476。非反復率相関はS4−0.1905/S8−0.1198。多数の探索的相関から有利な値を選ばない。recent_repeat_fractionはX/W同一、XとYは幾何表現共有、候補数Zの時点間共通支持なし。**Cの正式仮説は未成立・未検証**であり、棄却済みでもない。

## D. 主要技術情報と再現

### データ・処置・時間合法性

旧800は境界b=2/6 ns前の(b−1.9,b−0.4] ns、検証200は(b−0.3,b]、新400は(b,b+1.6]。F1=旧800、F2=旧400＋新400。M0/F1/F2各batch4×200歩、M0から共通weight/optimizer/RNGを復元する。Δ21は容量一定のデータ置換効果、新規性だけの因果効果ではない。S8 M0は同未学習初期化から別作成し、S4モデルの継続更新ではない。

履歴4区間は完全checkpoint継続、下流は選択座標再最小化/速度reseed。S8へS4枝データを入れない。16状態のM0生成→新MD→特徴凍結→分枝の合法性を最終監査済み。全フレームと公開順・入力SHAは[data-lineage](data-lineage.md)と[時間監査](../执行证据/2026-10-26-b1-expansion/temporal-and-SHA-audit.json)を参照。

### ソフトウェア・seed・モデル

Python3.12.3、Torch2.7.1+cu128、OpenMM8.5.2、NumPy1.26.4、MDAnalysis2.9.0、sklearn1.6.1、Parsl2025.10.20、mdlearn938cb80。RTX PRO6000 Blackwell Max-Q96GB、driver590.48.01。Amber14-all/GBn2/NoCutoff、非周期、300 K、2 fs、HBonds、Langevin1 ps⁻¹。既存CVAE接触図とLOF20、native RMSDなし。

M0 seed1600000001、履歴1600000100+r、追加学習1601000000+100r+10s+T、MD1602000000+100r+10s+M（s=4/8）、推論2026102671、順序1603000001、bootstrap1604000001。全実seedとIDは[全行列](experiment-matrix.csv)、[全16状態モデル表](model-training.md)。optimizer・RNG・checkpoint digestと全80CPU復元記録を保存した。

### 実装入口・形式・障害

[制御器](../../p1/server/expansion_run.py)、[凍結契約](../../p1/server/expansion_contract.py)、[科学処理](../../p1/server/expansion_science.py)、[物理/統計集計](../../p1/server/expansion_analysis.py)、[公開/圧縮](../../p1/server/expansion_publish.py)、[CPU表再照合](../../p1/report_review_audit.py)。原MDはPDB/DCD/checkpoint/XML/CSV、特徴npz/contact-map、モデルcheckpoint.pt、要求/結果/公開時計JSON、イベントJSONL。公開側eventsはJSONへ変換、元SHAはraw索引で区別する。

2回の共有ゲート停止後、成功taskと入力/結果SHAを確認して同run remainingで再開し、成功task再計算なし。初回GPU前の境界ID補強、実行中のZ.model_data_age_ns名称訂正、脱敏ログ同名衝突/別名取込、22:53転送退出を[失敗履歴](failures-and-amendments.md)に保存。原科学結果・凍結条件を変更していない。

### 実費用

GPU指定プロセス占有54,422.929387 s、task実行wall61,071.645465 s。追加学習wall平均4.2464 s（内部fit平均0.8449 s）、推論4.2532 s、下流4 ns MD209.5531 s。圧縮wall419.346117 s。worker CPU・処理分類・入れ子計時・GPU標本診断・未完了転送は[cost-and-runtime](cost-and-runtime.md)。これをkernel活動積算や固定wall-clock純利益としない。

## E. 独立審査で優先する問い

1. Δ21は新400への置換総効果として正しく解釈されているか。旧全保持での追加や新規性だけの効果に誤読していないか。
2. 全8根のS8−S4正を、候補数/訓練窓/M0/A0変化からどう区別するか。特に評価参照の増加による物差し変化を扱う必要がある。
3. 同初期化・200歩の制御CVAEを現時点の問いに十分と認めるか。loss・順位変化で科学有用性を代替していないか。
4. X/Y幾何共有、X/W重複、Z支持不足、多数特徴/指標探索、8根全使用の下で、Cの次の検証単位と独立splitをどう決めるか。
5. 局所探索の代理とNoCutoff/GBn2、準備史/pH/平衡未確認、再最小化/reseedを含む下流の解釈範囲は妥当か。
6. 2×3設計が示す変動と識別できない分散を正しく分けているか。bootstrapを確認的証明にしていないか。
7. 実更新費約4秒の条件でB2の検証価値とhorizonをどう設定するか。費用を人工的に膨らませず公平な比較を設計できるか。
8. Mac完全複製0/9、未清掃という保存残件をどの手順で閉じるか。今回の許可下では転送を再開していない。

本輪で独立審査者を新たに起動していない。Codex自身による表・リンク照合を「独立科学査読済み」と呼ばない。

## F. 正確なファイル索引

### 読む順番と主題資料（GitHubで閲覧可能）

|資料|目的|
|---|---|
|[README](README.md)|全資料ナビゲーション|
|[review-dossier](review-dossier.md)|18項目の完全科学審査資料|
|[事前計画](analysis-plan.md) / [指標契約](metric-contract.md)|結果前の問い・条件・全感度|
|[行列](experiment-matrix.csv) / [seed規則](randomization-plan.md)|全240予定枝と順序|
|[系譜](data-lineage.md) / [モデル](model-training.md)|新旧窓・祖先・親・乱数|
|[候補選択](candidate-selection.md)|LOF・起点差・実MD入力|
|[物理代理](scientific-metrics.md) / [品質](data-quality.md)|数式・単位・資格と限界|
|[対応結果](paired-results.md)|全3比較、全連続/離散条件|
|[乱数](randomness-analysis.md) / [状態診断](state-dependence-analysis.md)|内部変動・時点差・X/Z/W|
|[統計制限](statistical-limitations.md)|独立単位と識別不能部分|
|[費用](cost-and-runtime.md)|計時境界・保存残件|
|[失敗](failures-and-amendments.md) / [名称訂正](implementation-errata.md)|保護停止・変更史・原結果保持|
|[再現](reproduce.md)|コード/依存/入力復元とCPU照合|
|[図表監査](figure-and-table-audit.md) / [交付監査](delivery-audit.md)|数値・図・リンク・18/A–G照合|
|[教員概要](supervisor-summary-ja.md)|日本語説明用|
|[次段階案](next-stage-recommendation.md)|未承認の選択肢と研究者判断|

### 元の構造化証拠（全てGitHubで閲覧可能）

|ファイル|粒度・用途|
|---|---|
|[validation.json](../执行证据/2026-10-26-b1-expansion/validation.json) / [branch-status.csv](../执行证据/2026-10-26-b1-expansion/branch-status.csv)|予定/成功/MD量/独立単位|
|[continuous.csv](../执行证据/2026-10-26-b1-expansion/continuous.csv) / [discrete-counts.csv](../执行证据/2026-10-26-b1-expansion/discrete-counts.csv)|2,880連続行/17,280離散行、枝元値|
|[paired-effects.csv](../执行证据/2026-10-26-b1-expansion/paired-effects.csv)|41,472対応行、共有F0 ID|
|[state-effects.csv](../执行证据/2026-10-26-b1-expansion/state-effects.csv) / [root-effects.csv](../执行证据/2026-10-26-b1-expansion/root-effects.csv)|6,912状態行/3,456根行|
|[root-summary.csv](../执行证据/2026-10-26-b1-expansion/root-summary.csv) / [state-time-differences.csv](../执行证据/2026-10-26-b1-expansion/state-time-differences.csv)|432根要約/3,456同根時間差|
|[randomness-decomposition.json](../执行证据/2026-10-26-b1-expansion/randomness-decomposition.json)|9,216変動記録|
|[features.json](../执行证据/2026-10-26-b1-expansion/features.json) / [feature-variation.csv](../执行证据/2026-10-26-b1-expansion/feature-variation.csv) / [state-diagnostics.csv](../执行证据/2026-10-26-b1-expansion/state-diagnostics.csv)|16事前X/Z/W、変動、全相関|
|[selection-comparisons.csv](../执行证据/2026-10-26-b1-expansion/selection-comparisons.csv)|96起点/順位比較|
|[models.json](../执行证据/2026-10-26-b1-expansion/models.json) / [checkpoint-readback.json](../执行证据/2026-10-26-b1-expansion/checkpoint-readback.json)|80モデル、80CPU復元|
|[quality.json](../执行证据/2026-10-26-b1-expansion/quality.json) / [time-windows.csv](../执行证据/2026-10-26-b1-expansion/time-windows.csv) / [autocorrelation.json](../执行证据/2026-10-26-b1-expansion/autocorrelation.json)|240枝の品質・100 ps窓・系列相関|
|[costs.json](../执行证据/2026-10-26-b1-expansion/costs.json) / [GPU-diagnostics.csv](../执行证据/2026-10-26-b1-expansion/GPU-diagnostics.csv)|1,024費用記録、GPU標本診断|
|[failures.json](../执行证据/2026-10-26-b1-expansion/failures.json) / [events.json](../执行证据/2026-10-26-b1-expansion/events.json)|科学task失敗表（空）、公開イベント。controller停止は文書/復元記録で別計上|
|[temporal-and-SHA-audit.json](../执行证据/2026-10-26-b1-expansion/temporal-and-SHA-audit.json) / [task-manifest.json](../执行证据/2026-10-26-b1-expansion/task-manifest.json)|16状態時刻監査、1,024task要求/結果SHA|
|[raw-artifact-sha256.json](../执行证据/2026-10-26-b1-expansion/raw-artifact-sha256.json) / [public-export-index.json](../执行证据/2026-10-26-b1-expansion/public-export-index.json)|raw相対名/SHA、公開名の対応|
|[post-compute-status-20261027.json](../执行证据/2026-10-26-b1-expansion/post-compute-status-20261027.json) / [server-final-export-v1-public-sha256.json](../执行证据/2026-10-26-b1-expansion/server-final-export-v1-public-sha256.json)|9archive SHA/bytes、41公開ファイルSHA|
|[environment.json](../执行证据/2026-10-26-b1-expansion/environment.json) / [requirements.lock.txt](../执行证据/2026-10-26-b1-expansion/requirements.lock.txt) / [executed-source-sha256.json](../执行证据/2026-10-26-b1-expansion/executed-source-sha256.json)|実行環境・ソース固定|
|[server-final-export-v1-unit-b1-final.txt](../执行证据/2026-10-26-b1-expansion/server-final-export-v1-unit-b1-final.txt) / [unit-r2.txt](../执行证据/2026-10-26-b1-expansion/unit-r2.txt)|既存工程17B1＋9R2回帰、追加MDではない|
|[report-review-statistics.json](../执行证据/2026-10-26-b1-expansion/report-review-statistics.json) / [report-main-root-effects.csv](../执行证据/2026-10-26-b1-expansion/report-main-root-effects.csv) / [report-review-cpu-stdout.log](../执行证据/2026-10-26-b1-expansion/report-review-cpu-stdout.log)|今回のCPU復核、根別24行、照合結果|
|[report-backup-status.json](../执行证据/2026-10-26-b1-expansion/report-backup-status.json) / [report-archive-runtime-readback.json](../执行证据/2026-10-26-b1-expansion/report-archive-runtime-readback.json)|今回の保存真値/圧縮費用|

3図は[根別](../执行证据/2026-10-26-b1-expansion/root-state-effects.png)、[多尺度](../执行证据/2026-10-26-b1-expansion/multiscale-effects.png)、[X診断](../执行证据/2026-10-26-b1-expansion/feedback-diagnostic.png)。元PNGは変更していない。

### 許可保管先のみの資料

raw DCD、sim.csv、完全checkpoint/XML、80重み、全embedding/score/rank、recipe/exposure/frame index、原stdout/stderr/telemetry/private environment。logical batchとtask相対パスからraw SHA索引をたどり、根別r01…r08.tar.gzとmetadata.tar.gzのmanifest SHAで確認する。私有接続情報や絶対serverパスは本文に記さない。現時点でMac完全複製はない。コードのみで全原入力が自動取得されるstandalone公開artifactではない。

## G. 次段階（全て未承認）

まず独立審査で、状態束の識別と物理/学習配方の資格を確認する。その後の選択肢は①共通評価基準/候補制約を意図的に設計した状態差の検証、②配方と初期条件の資格確認、③別祖先rootのC増分情報検証と別途固定wall-clock B2設計。具体的根数・時間・GPU使用・停止条件は研究者が新仕様として承認する。[比較案](next-stage-recommendation.md)。

既存8根を独立最終テストに転用しない。バックアップ再開も今回の自動実行範囲外。文書作成を終えて停止し、研究者とChatGPTの科学審査を待つ。B2、正式C予測器、オンライン方策、S3、追加MD/訓練/推論を自動で実行しない。
