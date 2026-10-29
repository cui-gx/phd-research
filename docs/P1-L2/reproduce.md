# L2の再現手順と証拠の境界

2026-10-29。現在は承認済みv1を実行中であり、本書は新しい再実行の承認ではない。成功済み出力へ再度コマンドを実行しない。全checkpoint/完全logは許可サーバの本輪専用領域、公開側は表・SHA・コードを保持する。

## 固定する版

- 科学設計：`8d34e3714e246afb0bd74fe6943abeafd8f89c5b`。
- 入力凍結・人工CVAE資格・訓練/評価実装：`fea7500e735b6376e23e7cfe89e95bc976ca880e`。
- 制御器修正：`79ab95016b881e8294837137985cc77cd2208af4`。旧05016a2のログ引数衝突は[失敗台帳](execution-failures.json)に残す。
- 記述表・損失曲線の集約：`3d638eba728ce3badd5ec718f7683b9532bd2380`。
- checkpoint/実exposure/RNG監査：`09110f122b27925ed2b74343172f0e4e8785e2ed`。

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

全936のモデル×集合×mask行、全624の幾何行、全936次元行を保ち、全step/臂/init対を出す。root単位は2、同root二状態、3init、同chain checkpoint、相関frameという階層を保つ。未知根CI/p値や科学探索利益を新規算出しない。

公開表とサーバrawへの相対索引をSHAで結び、旧証拠不変性・費用・欠測・陰性結果を報告する。別機種/異なるlibraryのbit再現性は保証しない。Mac原archive免除と原9archive保持を維持する。
