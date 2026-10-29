# ChatGPTへの引継ぎ：L1凍結表現資格

## A. 現在の状態

2026-10-29 JST。COMPLETE：80/80モデル、160 model-set、480 model-mask行、288状態行、32,000frame行。基準6730e493bddce42fb4d86ed93fab05cc88810268、計画3054dafaece0fd855c397b6fb21e91a3d815fa30、前向前ID凍結296752d。最終配送SHAは本資料のGit履歴と最終返信。GitHubは表/図/コード/SHA、全再構成配列と原モデル/9archiveは許可サーバ。Mac原backup免除継続。

## B. 状態

CONFIRMED：ユーザーの限定CPU eval/no_grad前向評価。MEASURED：全80 SHA/digest/有限性/strict load/同CPU繰返しbit一致/前後重み不変。DERIVED：再構成・潜在・幾何/seed診断。UNVERIFIED：収束・十分な科学表現・物理資格。科学的受入/独立審査PENDING。新訓練/MD/LOF0。

## C. 重要結果

NONLOCAL325のrecent BCE/枚はF0 105.3166、F1 107.0408、F2 44.3003、共通旧頻度100.0909。F2は31/32が共通旧頻度より低いが、臂別訓練頻度より低いのは20/32。評価集合LOOは全モデルより低いが、相関した評価点を用いる楽観的参考でありオンライン基線ではない。

RAW物理10近傍重複はrecent F0 .1092/F1 .1162/F2 .1221、入力接触 .3458、時刻 .3466。元接触より弱い幾何近傍保存、学習seed間の局所不一致を残した。r07-s4-M0も有限・非除外。KL OLD2.8011/RECENT2.7732でも一部次元の小さいmu分散があり、collapseなしとはしない。[完全報告](review-dossier.md)に全基線/集合/例外を示した。

## D. 技術

[固定ID](validation-ids.csv)は前向前にGitHubへ登録。OLD_VALIDATION200とRECENT_HELDOUT200を全対応モデル共通に使用し、訓練IDと非重複。M0にrecentは事後汎化で、当時のオンライン情報ではない。二集合とも同根の相関点で外部テストではない。

GPU不可視、1 CPU/thread、batch32、RSS監視2GiB/出力1GiB/2時間復核点。[主実装](../../p1/l1_frozen_diagnostic.py)、[表/図](../../p1/l1_report_tables.py)。全80 optimizer保存digestもCPUで照合したがoptimizerインスタンス/stepなし。前向工程134.207s/CPU134.158s、峰RSS721.449MiB。全台帳[こちら](cost-ledger.json)。計算失敗0。

## E. 独立審査の問い

1. 共通旧頻度と臂別頻度を区別した再構成評価は妥当か。F2の新分布適応と条件付き表現を混同していないか。
2. validation LOOは相関/情報優位を明記しており、公平なオンライン勝敗としていないか。
3. 潜在KL/非zero mu/zero-code ablationを情報の十分性やcollapse否定へ誤用していないか。
4. 3次元圧縮の局所幾何損失とseed安定性をどの限定用途なら許容できるか。
5. r07の最終有限性を過去尖峰が無害だった証明へ変えていないか。
6. L2/P/Oの必要最小範囲を研究者がどう決めるか。現段階で新計算は未承認。

## F. 索引

[報告](review-dossier.md)、[README](README.md)、[計画](analysis-plan.md)、[ID](validation-ids.csv)、[凍結SHA](freeze-input-sha256.json)、[checkpoint監査](checkpoint-audit.csv)、[全モデル](model-metrics.csv)、[全状態](state-metrics.csv)、[frame](frame-diagnostics.csv)、[潜在](latent-diagnostics.csv)、[固有値](covariance-eigenvalues.csv)、[幾何要約](geometry-overview.csv)、[seed](seed-stability.csv)、[r07](r07-s4-case.csv)、[summary](summary.json)、[cost](cost-ledger.json)、[欠測/失敗](failures-and-missing.json)、[追加配列SHA](array-sha256.json)、[派生SHA](output-sha256.json)、[再現](reproduce.md)。原モデル系譜は[Q0](../P1-Q0/model-lineage.csv)と[B1原モデル](../执行证据/2026-10-26-b1-expansion/models.json)。

## G. 次段階

交付後停止。再構成への限定支持と物理近傍保存の弱さを踏まえて、研究者/ChatGPTが採用範囲またはL2の必要性を判断する。L2/P/O/C/B2、新訓練/MD/LOF/候補実行を自動開始しない。
