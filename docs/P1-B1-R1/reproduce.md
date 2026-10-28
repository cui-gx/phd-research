# B1-R1 CPU再解析の再現手順

2026-10-28。承認設計は `59f97821ae6ffe283c371f710546abf84f691642`。原B1科学生成版とCPU再解析版を混同しない。現在の実行状態はexecution-progressと最終handoffで確認する。

## 入力と実行条件

既存許可サーバの論理batch `b1-expansion-20261026` を読取り専用で使用する。8根/16状態/240枝、原raw SHA15,208件、9archiveの実在/SHAを検査する。旧B1の `summary-v1`、元ソース、原データ、seedは書き換えない。新出力の論理batchは `b1-r1-cpu-20261028-v1`。Macでrawを読み込んだり科学数値を計算したりしない。

新解析に必要な配備bundleはCPUソース、5境界テスト、元matrix、期待raw SHA、期待固定ソースSHA、期待根集計だけである。Macの `._*` を除外したallowlistを使い、実ファイル6件のSHAを検査する。原データの再作成・インストール・モデルloadは不要。既存B1環境のNumPy/SciPy/scikit-learnを再利用する。Python、ライブラリ版、thread条件は最終environment.jsonに実測保存する。

## 段階的な起動

次の変数は利用者が許可された本人領域に設定する。公開資料に私有ホスト名・絶対サーバパス・秘密鍵を記載しない。

```bash
export CUDA_VISIBLE_DEVICES=-1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export PYTHONDONTWRITEBYTECODE=1
export R1_MATRIX="$BUNDLE/experiment-matrix.json"
```

`PROJECT` は本人プロジェクト、`OUTPUT` は原B1とは別の新出力、`BUNDLE` は検証済み小型配備入力、`PYTHON` は既存許可環境の実行ファイルを指す。CPU worker/threadは1、単一CPU affinity、nice10。利用者・CPU/RAM/GPU/ディスクと利用記録を先に読取り専用で確認する。旧B1環境やarchiveを削除しない。

```bash
"$PYTHON" -m unittest discover -s tests/p1 -p test_r1_cpu_review.py -v
"$PYTHON" -m p1.r1_cpu_review --project "$PROJECT" --output "$OUTPUT" --bundle "$BUNDLE" --stage audit
"$PYTHON" -m p1.r1_cpu_review --project "$PROJECT" --output "$OUTPUT" --bundle "$BUNDLE" --stage original
"$PYTHON" -m p1.r1_cpu_review --project "$PROJECT" --output "$OUTPUT" --bundle "$BUNDLE" --stage references
"$PYTHON" -m p1.r1_cpu_review --project "$PROJECT" --output "$OUTPUT" --bundle "$BUNDLE" --stage lof
"$PYTHON" -m p1.r1_cpu_review --project "$PROJECT" --output "$OUTPUT" --bundle "$BUNDLE" --stage summary
"$PYTHON" -m p1.r1_cpu_report --project "$PROJECT" --output "$OUTPUT" --implementation-commit "$CPU_CODE_COMMIT"
"$PYTHON" -m p1.r1_cpu_review --project "$PROJECT" --output "$OUTPUT" --bundle "$BUNDLE" --stage finish
```

テスト時だけ `R1_FROZEN_GQ_SOURCE` に、期待SHAと一致する原B1 `executed-source/p1/server/gq_r2.py` を指定する。importしているのはNumPy/SciPyの距離・領域・角度関数であり、OpenMMやTorchを起動しない。

各段階の終了コードとPASS証跡を確認してから次へ進む。上記を失敗後も継続するシェル列として実行しない。原再現不一致時は追加参照を実行せず、失敗ファイルとログを保存して停止する。配備版/manifest不一致も停止条件。成功した新出力の上書き再計算をしない。

## 許容と完全性

- 原連続量：絶対1e−8＋相対1e−10（元単位）。整数・代表/確認・最近傍IDは完全一致。小部分dense/block誤差1e−12 Å。
- FULL LOF：保存dtypeを維持、score絶対/相対1e−10、全順位とTop1一致。20近傍/Minkowski p2/novelty=False、global ID tie。
- 各参照2,880連続行/17,280離散行、合計11,520/69,120行。全165,888対応行、27,648状態行、13,824根段階行、6,912根要約行、3,456根寄与行、36,864乱数記録を要求する。
- 8根bootstrap10,000回/seed1604000001を全条件で共有する。下位seed、保存フレーム、窓、選択を独立根へ追加しない。
- メモリ余裕4 GiB、RSS2 GiB、新出力2 GiB、ディスク空き100 GiB、6時間再審査の各ゲートを維持する。先頭枝の費用投影を先に保存する。

## 保存と交付

全CSV/JSONの数値はサーバ生成物から取得する。原NPZ/DCD/モデル/9archiveはMacへ転送しない。新しい最小距離配列、全代表/確認ID、完全ログは許可サーバへ保持し、GitHubには可読全表・図・監査・SHA索引と再現コードを置く。新出力SHAと元入力再照合を完了し、通常のcommit/pushと遠隔本文回読を行う。原B1保存政策は変更しない。

科学的受入れと独立審査はPENDING。完了後は審査で停止し、新MD/学習/モデル推論/B2/C予測器/S3を実行しない。
