# S2補充：復現手順と証拠目録

2026-10-25 JST。計算済み結果の検証用であり、新GPU/MD計算の許可ではない。

## 版と原始入力

- 計画commit：`0ae3d092659be6c32b176ab8fa17612a833f49f9`、計画SHA256：`dbdd38d7153570dc81318351639877a4a17254fe479c3faa249f668d5f5fff42`。
- 有効A/B/C実行commit：`656df0cf2677affaf362ed631b662545321f80e3`。元の実装commit ad61e3cの初回A失敗を保存。
- 計画のGitHub回読blob：`e97cc0357412023153020447e357b6230110e5a6`。事前計画は書換えず、技術修正はamendments.mdに追記。
- 原始S2 archive SHA256：`2d1ae3e1499496c4f60ea3b58974b709e2c47dd5a6ba84efb3df2b8f62a02bd7`。
- 原始ローカル位置：`results/raw/remote/2026-10-24-P1-S2/runs/s2-pilot-02/`。203ファイルの`checksums.json`をA開始時に全件検証。大容量のDCD、checkpoint、入力/実行ログはローカルと既存個人サーバ領域に保存し、GitHubにアップロードしない。
- 派生完全出力：`results/processed/P1-S2-SUPPLEMENT-20261025/attempt-02/{A,B,C}/`。失敗attempt-01とpublication-failed-01も保持。
- 共有可能なJSON/CSV/図/ログ/ロック：`docs/执行证据/2026-10-24-s2-supplement/`。[出力inventory](../执行证据/2026-10-24-s2-supplement/local-output-inventory.json)の相対path/bytes/SHAで対応付ける。

## 環境

[正確なpip lock](../执行证据/2026-10-24-s2-supplement/requirements-cpu.lock.txt)、[測定環境](../执行证据/2026-10-24-s2-supplement/environment.json)。Python3.12.14、macOS ARM64、OpenMM distribution 8.5.2（运行build串8.5.2.dev-36a30cb）CPU、Torch2.7.1 CPU。mdlearnは固定vendor938cb80。新しい再現環境を使う場合は本機上の段階専用venvにだけインストールする。共有サーバのCUDA/driver/global gitに触れない。CPU wheel/浮動小数点差により値が逐位一致するとは限らない。

実行時環境変数：OMP_NUM_THREADS=2、OPENBLAS_NUM_THREADS=2、MKL_NUM_THREADS=2、VECLIB_MAXIMUM_THREADS=2、NUMEXPR_NUM_THREADS=2、CUDA_VISIBLE_DEVICES空、PYTORCH_ENABLE_MPS_FALLBACK=0、PYTHONDONTWRITEBYTECODE=1。PYTHONPATHに固定vendor/mdlearn-938cb80とrepo root。現実装はCPU device、DataLoader workers0、LOF n_jobs2。

## 実行コマンド

以下はワークスペースrootから。`<python>`は段階専用環境。新規出力先のみ許す。過去出力と予算帳簿を削除して再実行しない。

```sh
<python> -B -m unittest tests.p1.test_supplement
<python> -B -m p1.server.supplement_run \
  --raw results/raw/remote/2026-10-24-P1-S2/runs/s2-pilot-02 \
  --output results/processed/P1-S2-SUPPLEMENT-20261025/attempt-02 \
  --analysis-commit 656df0cf2677affaf362ed631b662545321f80e3
```

runnerはHEADと指定commitの一致、計画SHA、累積A600/B900/C300秒・全1800秒を検査する。別commitから実行する際はその実際HEADを指定し、元の結果のコード版と同一と偽らない。既存予算ledgerに未完了runningがあれば先に失敗を照合し、無制限再試行しない。監視は自分の単一解析子プロセスのみ。初回失敗7秒も累積。

Aは全203入力ハッシュと原子順を検査、Bは候補snapshot/contact/checkpointハッシュ、復元model/optimizer摘要を検査。Bは共通初期重みから各臂を独立に復元する。Cは11座標を読み込み3systemで状態取得だけを行い、integrator_steps=0を記録する。

修正したエネルギー集計と図は**状態取得を再実行せず**、既存出力から生成する：

```sh
<python> -B -m p1.server.supplement_publish \
  --attempt results/processed/P1-S2-SUPPLEMENT-20261025/attempt-02 \
  --output <new-review-output-directory>
```

このスクリプトは公開用ファイルを生成するだけで、Git pushや第三者送信をしない。元のC JSONを上書きしない。最終commit中のスクリプトとderivation-receiptのソースSHAを照合する。科学データを再計算せずエネルギー中位数の整合性を修正、GB XML表現抽出、図作成、バージョン記録を行う。失敗出力も保存するため、同名出力への上書きを拒否する。

## 表から証拠への対応

| 主張/表 | 直接確認するファイル |
|---|---|
| A入力とsplit | coverage-manifest.json、ca-mapping.json、prefix-diagnostics.json |
| 全432網格と144主分析 | coverage-sensitivity.json/csv（task_id、parameter_id、seed、入力SHAあり） |
| 固定図と各フレーム値 | baseline-coverage-curves.csv、physical-features.csv |
| 不変性・時間相関・混叠 | coverage-negative-controls.json、autocorrelation.json、within-cell-drmsd.json |
| 中心庫K/訪問/OUL | center-library-results.json（中心frame、SHA、各フレーム距離あり） |
| 壁時計制約 | time-axis-worker-proxy.json、run-receipt.json |
| F0/F1/F2公平性 | selection-manifest.json、matched-arms.json（全exposure index、steps、weights SHA） |
| 候補・順位 | scores-*.json、selection-comparison.json/csv、historical-lof-only.json |
| C科学設定と全試行 | systems.json、gb-parameter-expressions.json、physics-evaluations.json |
| 修正後C結果 | physics-sensitivity.json/csv、derivation-receipt.json |
| 失敗・累積予算・cleanup | stageログ、amendments.md、budget-ledger-final.json、cleanup-verification.json |

Cの全原子力NPZとsystem XMLは完全ローカル派生出力に保存、SHAはinventoryに掲載。GitHubだけで生のMDを再分析できるわけではない。アクセスが必要な審査者には研究者が管理された方法で原データを渡す；パスの存在を公開済みと誤記しない。

実行段階で7項新数学/復元テストと9項関連既存テストに成功。主代理の終了前再検証では新7項＋qualification6項＋component timing6項、合計19項が1.657秒で成功し、test-validation.logに記録。工学テスト成功は科学的妥当性を認定しない。最終独立審査、cleanup及びGitHub回読は別の記録を参照し、未完項を成功と見なさない。
