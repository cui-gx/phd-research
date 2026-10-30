# P1-L2：ChatGPT独立審査への引継ぎ（A–G）

2026-10-30 JST。まず[完全報告](review-dossier.md)を読み、[事前判定](decision-criteria.md)と全表を照合する。旧[設計時引継ぎ](design-handoff-8d34e371.md)は8d34e371の原文で保持した。

## A. 現在の状態

バッチ`l2-20261029-v1`。科学計算**COMPLETE**、36/36 chain、156/156評価（144訓練点＋12未学習対照）、57,600歩、230,400提示。未完了科学単位0、除外0、新MD0。[summary](summary.json)、[実行状態](execution-status.json)、[最新交付状態](execution-progress.json)。実行器・後処理終了は[終了点検](final-server-check.json)、最終検証JSTは同ファイルに記載。

設計版8d34e3714e246afb0bd74fe6943abeafd8f89c5b、学習/評価版fea7500e735b6376e23e7cfe89e95bc976ca880e、制御器修正79ab95016b881e8294837137985cc77cd2208af4、報告補足実装a9d42afbc6ae2603c0ab1b06d6f22f63baf9ec86。実配備ファイル別SHAは[source-state](source-state-sha256.json)。報告内容版と最終同期SHAは[remote-readback](remote-readback.json)およびGit履歴/最終返信で確定する。まだ存在しない自引用SHAを記入しない。

GitHubへ渡すものは日本語報告・全小型統計・全対比・図・ID・コード・SHA/監査。重み、全forward配列、全候補embedding/score、全loss/exposure/logは許可サーバの`artifacts/l2-20261029-v1`のみ。原9archive保持、Mac原archive backup要求はWAIVED_BY_RESEARCHER。独立科学審査・研究者科学受入れは**PENDING**。

## B. 確認事項と状態

- **CONFIRMED**：研究者は8d34e371の限定L2を承認。4既知状態、3初期化、固定M0-200親、全step/全指標、GPU学習のみ、CPU診断GPU不可視、単worker/thread。新MD/P/O/C/B2/S3の許可ではない。
- **MEASURED**：108使用原入力SHA、156 checkpoint、24親、48同step RNG組、57,600歩と230,400提示、156実RMSprop counterの監査PASS。[integrity](integrity.json)、[optimizer](optimizer-step-integrity.json)。旧80重み/9archiveを全て本輪で再hashした意味ではない。
- **DERIVED**：最終1600三条件同時支持はM0 26/48、F1 26/48、F2 45/48。全条件群PARTIAL_INCONCLUSIVE。2根の開発診断で、48独立反復ではない。
- **UNVERIFIED**：十分収束、posterior collapse不存在、物理資格、科学探索利益、C、B2。大きな有限KL峰の原因と下流影響も未識別。
- **PROPOSED**：将来の限定利用や追加資格案は審査後に研究者が選択する。新レシピ・新実験を自動採用しない。

## C. 主要科学結果

NONLOCAL325 BCE nats/フレーム、4状態×3init=12依存条件/条件群。最終1600のOLD/RECENTはM0 45.250824/188.861153、F1 44.976686/183.796058、F2 34.642212/44.741664。[overview](overview.csv)。M0/F1のRECENTは800→1600で悪化。200→1600のF1 RECENT BCEは+2.198031だがK10は+0.042333。F2 RECENTで両方改善は7/12。[全maskの対応要約](step-improvement-summary.csv)。

F2−F1最終1600 RECENT BCE平均−139.054394（12/12低下）だがK10平均+0.018500、範囲−0.031500〜+0.083500、正9/12。[update-effects](update-effects-summary.csv)。F2のK10はOLD0.217000/RECENT0.181083で、接触基線0.447125/0.403875、時刻基線0.480125/0.435875を下回る。容量差があるので無価値とは言わず、物理近傍全面保存とも言わない。

48セルのF2非成立はr01-s8-i1 RECENT LONGのA_train−0.3964119、r02-s8-i2 OLDのK10−未学習−0.000500（同幾何が二maskへ重複）。[全判定](decision-cells.csv)。微小負を丸めて合格にしない。

1600初期化間のF2潜在距離rank平均OLD0.846732/RECENT0.749873、近傍重複0.342750/0.311750。[initialization](initialization-summary.csv)。LOF F2/F1 Top1一致0/12、Top100重複0.073333、Top1距離平均3.666060 Å。初期化間でも各条件群Top1一致0/12。[LOF](LOF-summary.csv)。全新選点の下流は**NOT_OBSERVED**。

r02-s8-i2-M0第5歩：BCE_sum88,600、KL_mean242,598,880、total242,687,488、clip前norm1,467,631.625。全chainを保持し再実行なし。[原case](loss-spike-case-r02-s8-i2-M0.csv)、[SHA/説明](loss-spike-case.json)。有限最終値は学習安定性を保証しない。

統計単位は2根。同根S4/S8、初期化3対、checkpoint、相関frameを独立数とせず、未知根CI/p値を出さない。root-effects.csvは状態行であり4根ではない。

## D. 技術情報・失敗・費用

固定入力は28×28・8 Å接触、M0/F1旧800、F2旧400+新400。OLD/RECENT200ずつ、訓練とID非重複だが時間相関は残る。M0 RECENTは事後汎化。初期化1700000101/102/103、M0 optimization1701000001、子1702000001、permutationは独立generator。同一stream条件付きの初期化比較。子の累積歩数はchain歩数+200。F0=M0-200。

訓練は[adapter](../../p1/l2_train.py)、CPU評価は[evaluate](../../p1/l2_evaluate.py)、[control](../../p1/l2_control.py)は単一lockで成功skip。不完全chainは無断復旧・上書きしない。人工CPU保存再開bit一致、実GPU親load/digest一致、全保存stepのRNG一致。子step0 RNG直接snapshotはない。GPU中断再開を別に実証していない。

Torch2.7.1+cu128、NumPy1.26.4、sklearn1.6.1、mdlearn0.0.10a1(source938cb80)、RTX PRO6000 Blackwell Max-Q96GB。[環境](hardware-environment.json)。原recipe epochs=1は旧API属性で、実adapter8epoch/1600歩と区別する。train raw BCE batch総和+KL batch平均はevalの単位と異なる。

[費用](runtime-summary.json)：36学習内部wall223.804797s、156 CPU評価3706.232239s、制御器span4344.121058s。後処理15.275740s、報告補足3.515189s。初2processの起動全体は未測、文書/Git/転送時間も別。学習RSS1636.137MiB、CPU評価708.992MiB、Torch reserved108MiB、出力約1.229GB。GPU kernel時間・利用率traceは未測。オフラインFULL診断費用をB2オンライン費用へ代用しない。

[失敗2件](execution-failures.json)：制御器ログ引数衝突は新科学実行前に停止し修正、成功1chain/1評価保持。図v1の軸切断はv2別名で修正、原値不変。全既定単位の科学欠測0。最終内部文書点検への並行支援は利用量制限で完了せず、独立科学終審の実施やPASSを主張しない。

文書静的検査のAppleDouble読込み失敗も台帳に記録し、除外修正後に再検査した。科学データ・数値の変更はない。

## E. 独立審査で確認してほしい論点

1. 巨大有限KL峰の存在と最終表現をどこまで限定利用できるか。step5のμ/logstdが未保存で因果原因は決められない。
2. 頻度以上の再構成・全対応対照の限定支持と、弱い局所幾何/初期化依存/LOF不安定をどう統合して判断するか。
3. 200歩以降の改善と非単調・悪化を踏まえ、1600を正式レシピへ採用する根拠はまだ不足している点。
4. 2既知根/1更新stream、時間相関、旧/新窓とM0/候補数の段階交絡。CのX増分価値や科学Yは未識別。
5. Pの物理準備・溶剤/平衡とOの成果定義は独立ゲート。L2だけで旧B1の科学結論を書き換えない。

## F. ファイル索引

|資料|内容|
|---|---|
|[review-dossier](review-dossier.md)、[指導教員向け概要](supervisor-summary.md)|完全な方法・数値・陰性・限界と短い日本語説明|
|[事前計画](analysis-plan.md)、[行列](experiment-matrix.csv)、[checkpoint](checkpoint-matrix.csv)|36/156固定条件と凍結方法|
|[metric-contract](metric-contract.md)、[判定](decision-criteria.md)|公式・単位・閾値と見出し規則|
|[training IDs](training-membership.csv)、[evaluation IDs](evaluation-ids.csv)、[freeze](input-freeze.json)|membership、時間、入力SHA|
|[model-metrics](model-metrics.csv)、[geometry](geometry.csv)、[latent](latent.csv)|936/624/936行、全対照・標準化補助・次元診断|
|[overview](overview.csv)、[state-metrics](state-metrics.csv)、[root-effects](root-effects.csv)|全78 overview、状態集計、96状態対比|
|[paired-contrasts](paired-contrasts.csv)、[step-summary](step-improvement-summary.csv)、[update-summary](update-effects-summary.csv)|3960対比、全18歩数改善、全24更新要約|
|[stability](representation-stability.csv)、[init-summary](initialization-summary.csv)|全1320安定性と26要約|
|[LOF-comparisons](LOF-comparisons.csv)、[LOF-summary](LOF-summary.csv)、[selection](selection-summary.csv)|660全比較、55要約、156選択|
|[loss-curves](loss-curves.csv)、[case](loss-spike-case.json)、[latent-range](latent-loss-range-summary.json)|288epoch、巨大KL原事例、潜在範囲|
|[integrity](integrity.json)、[checkpoint audit](checkpoint-audit.csv)、[parent](parent-audit.csv)、[RNG](RNG-pair-audit.csv)、[optimizer](optimizer-step-audit.csv)|156checkpoint/24親/48RNG/実歩数監査|
|[qualification](qualification-checks.json)、[cells](decision-cells.csv)、[numeric](numeric-validation.json)|144判定セル、有限性・欠測|
|[cost-ledger](cost-ledger.json)、[runtime](runtime-summary.json)、[postprocess](postprocess-costs.json)、[completion](report-completion-costs.json)|単位・後処理・起動の測定範囲|
|[raw-output SHA](raw-output-sha256.json)、[log SHA](execution-log-sha256.json)、[source SHA](source-state-sha256.json)|サーバのみの原証拠と実ソース索引|
|[移送1](delivery-sha256.json)、[移送2](completion-delivery-sha256.json)、[交付検証](execution-delivery-validation.json)|各時点小型証拠・最終検証|
|[再現](reproduce.md)、[最終サーバ確認](final-server-check.json)、[遠隔回読](remote-readback.json)|再実行権限と保存・同期の実状態|

## G. 次段階

唯一の次行動は研究者/ChatGPTの科学審査。新実験、1600超への延長、良いseed選別、新レシピ採択、L2/P/O/C/B2/S3の自動開始をしない。将来の追加条件はPROPOSEDとして、必要な情報価値と境界を別に承認する。今回の技術交付完了は科学受入れではない。

### 同期の実測確認

報告内容commit `b3fdd3e6ccbe0b4838b010a3706a7602a8d78f1f` の設計以降89変更ファイルをGitHubから全文回読し、decoded byte数と計算したGit blob SHAを照合してPASS。大きいpaired-contrasts.csvもblob APIで全2,320,032 bytesを取得した。[回読収据](remote-readback.json)。この収据を追加した最終同期commitはGit履歴と最終返信で照合する。独立科学審査・研究者受入れは変わらずPENDING。
