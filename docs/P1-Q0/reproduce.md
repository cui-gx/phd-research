# Q0の再現と停止境界

既にQ0は終了している。以下は再現用記録であり、再実行の自動許可ではない。原ログは許可サーバに必要で、GitHubから原DCD/重みを取得できるという意味ではない。

1. mainとAGENTS、analysis-planを読み、別途許可された本人CPUと共有予約/利用状況を確認する。
2. 新出力先を選ぶ。bundleは旧公開models.json、task-manifest.json、raw-artifact-sha256.json、quality.json。原run/artifactは読取り専用として扱う。
3. CUDA_VISIBLE_DEVICES=-1、OMP_NUM_THREADS/OPENBLAS_NUM_THREADS/MKL_NUM_THREADS=1でp1/q0_log_audit.pyへproject/new-output/bundleを渡す。本輪の実出力論理名はartifacts/q0-20261029-v1/output。主コードは既存先を拒否する。補助コードの今回の出力名は固定されているため、将来再現時には新しいwork area版へ明示的に分離し、成功済みQ0出力を上書きしない。
4. q0_log_summary.pyは保存CSV/品質記録の記述だけ。q0_log_figures.pyは既存Matplotlib環境で図生成のみ。モデルloadやDCD読取りなし。code SHAはcosts/supplemental-costs/figure-costsを照合する。
5. output-sha256.jsonと全派生ファイルを照合する。これは文書作成前のサーバ派生24ファイルのSHA。後付け本文はGit配送commitと検証記録で追う。

main監査の最初の版には窓境界問題があり、サーバoutput-before-boundary-fixへ保持した。公開の窓分類は報告indexによる修正版。原B1/R1やseedは変更していない。

技術結果を科学資格合格と同一視しない。終了後は独立審査待ち、P/L/O/C/B2/S3は別承認。
