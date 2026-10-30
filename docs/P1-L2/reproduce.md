# L2の再現手順と証拠の境界

2026-10-30。承認済みv1の全36chain・156評価と監査は終了した。本書は新しい再実行の承認ではない。成功済み出力へ再度コマンドを実行しない。全checkpoint/完全logは許可サーバの本輪専用領域、公開側は表・SHA・コードを保持する。

## 固定する版

- 科学設計：`8d34e3714e246afb0bd74fe6943abeafd8f89c5b`。
- 入力凍結・人工CVAE資格・訓練/評価実装：`fea7500e735b6376e23e7cfe89e95bc976ca880e`。
- 制御器修正：`79ab95016b881e8294837137985cc77cd2208af4`。旧05016a2のログ引数衝突は[失敗台帳](execution-failures.json)に残す。
- 記述表・損失曲線の集約：`3d638eba728ce3badd5ec718f7683b9532bd2380`。
- checkpoint/実exposure/RNG監査の最終版：`bd7a0983adf8c0deaf1bb243010587ef1cabc917`。NumPyの省略reprでなく実状態全配列をhashする。
- 集約の固定feature cache：`eb177efb05590643d47d71db671c7d03d8b7dd5e`。評価量は不変。
- 実RMSprop counter・判定集計・図v2と報告補足wrapper：`a9d42afbc6ae2603c0ab1b06d6f22f63baf9ec86`。
- 実配備SHA：[source-state](source-state-sha256.json)、[後処理release](postprocess-release.json)、[報告補足release](report-completion-release.json)。一つのHEADを全過去実行へ流用せず工程別版を使う。

環境はTorch2.7.1+cu128、NumPy1.26.4、scikit-learn1.6.1、mdlearn0.0.10a1（ソース938cb80）。GPUはRTX PRO 6000 Blackwell Max-Q 96GB一枚。実際にimportされたmdlearn5ファイルのSHAは[input-freeze.json](input-freeze.json)。共有システムへの依存追加/更新はしていない。

## 1. 入力と工程資格

別途再実行を承認する場合、本人所有の新しいL2出力先を登録する。原B1の108使用ファイルを旧SHAと再照合し、PDBの28 Cα順、固定800訓練ID、OLD/RECENT200ずつ、時刻、候補7,800/15,800を確認する。既存DCDを再処理しない。

`p1.l2_engineering freeze`と`synthetic`はGPU不可視・単CPUで行う。人工testは同じCVAE/RMSpropを用い、連続6stepと3+保存/再開+3stepを照合した。Python/NumPy/Torchの状態、独立permutationとDataLoader generatorの継続も点検する。人工12stepを科学stepに計上しない。

実入力・実環境・工程test・独立adapterをGitHubにcommit/pushし、全文とGit blobを回読する。その実在commitと各adapter/固定CSVのSHAを`execution-release.json`へ保存する。releaseなしに訓練しない。

## 2. 環境と各実行入口

以下の変数は許可された本人領域と既存runtimeの実際の場所に設定する。内部接続先、鍵、アカウント情報を公開資料へ書かない。

```sh
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
```

GPU訓練の入口は`p1.l2_train PROJECT PLAN OUTPUT CHAIN_ID`、CPU評価の入口は`p1.l2_evaluate PROJECT PLAN OUTPUT CHECKPOINT_ID`。訓練時だけCUDA_VISIBLE_DEVICES=0、CPU時は-1とする。processは単独、親checkpoint SHAを検証する。元B1/R1/Q0/L1ファイルへ書かない。

固定順序を担当する`p1.l2_control PROJECT PLAN OUTPUT`は一つだけ動かす。fcntl lockとprocess状態を確認し、成功resultがある単位は再実行せず参照する。不完全ディレクトリは自動再試行せず停止する。新しい試行はstdout/stderrも別名で保存する。既存制御器が動いていれば第二制御器を起動しない。

## 3. 残すデータ

各chainはmodel/optimizer/全RNGを含むcheckpoint、1,600行lossと6,400行exposure、recipe、親SHA、resource costを保存する。M0の0/200/400/800/1600、子の追加200/400/800/1600を区別する。子のlifetimeは400/600/1000/1800である。

各評価点はOLD/RECENTのmu/logstd/reconstruction、全FULL候補のembedding/LOF/order、Top1/10/100、全mask/ablation/幾何/潜在表を保持する。F1/F2の開始時のRNGはソースの同seed再設定で制御されるが、別の子step0 RNGファイルは作っていない。保存された同stepの48組のRNG一致を監査し、この記録範囲を直接の開始snapshotと混同しない。

## 4. 完了後の監査・集約

制御器終了を確認してから、同じ単CPU/GPU不可視条件で`p1.l2_audit`、`p1.l2_aggregate`、`p1.l2_review_summary`を順次実行する。計算中の第二解析workerを並走させない。入力108 SHA、156 checkpoint/optimizer digest、24親関係、48同step更新RNG組、230,400提示、57,600loss行を検査する。原archive全体の新規SHA監査とは異なる。

全936のモデル×集合×mask行、全624の幾何行、全936次元行を保ち、全step/条件群/init対を出す。root単位は2、同root二状態、3init、同chain checkpoint、相関frameという階層を保つ。未知根CI/p値や科学探索利益を新規算出しない。

公開表とサーバrawへの相対索引をSHAで結び、旧証拠不変性・費用・欠測・陰性結果を報告する。別機種/異なるlibraryのbit再現性は保証しない。Mac原archive免除と原9archive保持を維持する。

## 5. 今回実行済みの後処理と図の復元

実行済み入口は`p1.l2_postprocess PROJECT PLAN OUTPUT`で、監査・全対比集計・記述要約・初版図を単CPUで順次処理した。続いて同入口へ`--report-completion`を付け、実optimizer audit、固定判定/要約、図v2を処理した。既存結果は排他的作成で保護されるため、同じOUTPUTへ再実行しない。[postprocess-costs](postprocess-costs.json)、[report-completion-costs](report-completion-costs.json)にwall/CPU/RSS監視がある。モデルloadはauditでdigest/counter確認だけ、これらの後処理は新訓練・新forward・MD・LOF refitを行わない。

- `p1.l2_audit PROJECT PLAN OUTPUT`：使用108入力と全checkpoint/親/RNG/exposureの照合。
- `p1.l2_aggregate PROJECT PLAN OUTPUT`：全660対比、全mask/集合、幾何・LOF・安定性。保存配列を使い、新しい選点のMDを割り当てない。
- `p1.l2_review_summary PLAN OUTPUT`：overview、状態対応差、288epochの平均/min/max、raw SHA。
- `p1.l2_optimizer_audit PLAN OUTPUT`：保存されたRMSpropの実stepと累積学習量の照合。
- `p1.l2_report_facts OUTPUT`：全48セル/条件群の事前方向判定、歩数/更新/初期化/LOFの記述要約。
- `p1.l2_figures OUTPUT`：保存CSVから日本語図を作る。最新ソースはv2別名を使用し、全個別線を共通最大y値内へ収める。

コマンドの正確な引数は各固定版の`argparse`を参照し、別途の再実行承認後、新規OUTPUTを用意する。環境変数`MPLCONFIGDIR`は本人の本輪専用cacheへ設定する。別機種で図のPNG bit一致を保証しないが、入力CSVとプロット値の一致を確認できる。

潜在範囲JSONは保存`latent.csv`の1600行だけを条件群・集合でグループ化し、母分散・Eσ²・次元KL・固有値のmin/maxを記述した。最大loss caseは全288epoch extremaから最大totalを特定し、該当chainの原`loss-steps.csv`1600行をbyte転記して元SHAと照合した。これらは新しい閾値分類・モデル実行ではない。[case](loss-spike-case.json)、[range](latent-loss-range-summary.json)。

日本語本文の表はサーバCSVの既存要約列を`research-workflow/l2-write-final-docs.py`で整形した。Macで科学値を新計算しない。[最終交付監査](execution-delivery-validation.json)は表件数・保護SHA・相対リンク等の静的検証であり、科学再実験ではない。

## 6. 証拠の保存と停止

原9archiveは削除せず、最新終了点検は存在とサイズを確認した。全量SHAの過去検証と区別する。L2 raw weights/arrays/loss/exposure/logsも専用サーバ領域に保持し、[raw SHA](raw-output-sha256.json)、[ログSHA](execution-log-sha256.json)で特定する。原archiveをMacへ転送しない。GitHubは全統計・コード・図・索引だけを保存し、[遠隔回読](remote-readback.json)で公開側の実内容を検証する。独立科学審査・研究者受入れはPENDING。完了した制御器や科学単位を再始動しない。
