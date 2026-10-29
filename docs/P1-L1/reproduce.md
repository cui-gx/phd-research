# L1再現手順・保存境界

本輪は終了済み。再実行の自動許可ではない。入力は既存B1のtasks、原SHA索引とmodels.json、固定mdlearn環境が必要。原データ/モデルはGitHubへ同梱していない。

1. mainと承認範囲を読み、本人CPU/RAM/予約/GPUの共有状況を確認する。新出力先を用意する。
2. CUDA_VISIBLE_DEVICES=-1、OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1。既存runtime pythonでl1_frozen_diagnostic.py freeze PROJECT NEW_OUTPUT BUNDLEを実行する。freezeは既存先を拒否する。
3. frozen-cohorts.json/validation-ids.csv/全入力SHAをcommit/pushしてから、同じ実装のevaluate PROJECT NEW_OUTPUT BUNDLEを実行する。方法/IDの変更が必要なら停止する。
4. l1_report_tables.pyは今回の論理出力名artifacts/l1-20261029-v1/outputを固定参照する。将来再現時は独立work areaで参照先を明示的に分離し、成功済み出力を上書きしない。
5. cost-ledgerの実行コードSHAとexpected-mdlearn-sha256、全原入力前後SHAを照合する。同一CPU/batch決定性を他GPUのbit一致へ外挿しない。
6. arrays/の再構成・mu・logstd・固有値と公開CSVを保持し、publicだけをGitHubへ同期。原checkpoint/optimizerを再保存しない。原archive削除/全量Mac転送なし。

統計単位は8歴史根、16状態は入れ子、二学習seedは同一M0の子。200フレームや19,900距離対を独立標本として検定しない。原結果とL1結果のパラメータを混在させない。
