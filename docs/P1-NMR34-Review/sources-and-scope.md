# 出典と確認範囲

2026-10-31 JST。以下は本審査で実際に参照した資料と、主張できる範囲である。原論文全文を読んでいないものを「精読済み」としない。

|資料|今回の確認範囲|用途・限界|
|---|---|---|
|[RCSB 1FME](https://www.rcsb.org/structure/1FME)|構造エントリ：SOLUTION NMR、49 calculated/34 submitted、least restraint violations、28残基|34参照の由来。原NMR論文の全手法を審査したわけではない。新PDBへ差し替えず凍結SHAを保持|
|[Grossfield et al., Best Practices for Quantification of Uncertainty and Sampling Quality in Molecular Simulations](https://pmc.ncbi.nlm.nih.gov/articles/PMC6286151/)|全文ページの概要、§4.4、§7.2–7.5、§8を重点確認。DOI 10.33011/livecoms.1.1.5067|相関標本、初期条件付き独立性、samplingとsystematic errorの区別。本研究の8根区間の被覆を認証する論文ではない|
|[Kabsch 1976](https://doi.org/10.1107/S0567739476001873)、[Kabsch 1978](https://doi.org/10.1107/S0567739478001680)|IUCr出版社の書誌・抄録。1978全文は購読制限|最適回転/proper rotationの原典。実装の正しさは固定ソース・既存試験で別に確認|
|[MDAnalysis公式単位文書](https://userguide.mdanalysis.org/stable/units.html)|Å/psへのreader変換、表示版2.9.0|単位契約の補助。凍結環境は既存software記録に依存|
|OpenMM 8.5.2固定版の参照先|本輪のweb取得はcache miss。新規全文確認とは数えない|物理設定の監査は[既存資格報告](../P1-Post-R1-Qualification/qualification-review.md)と実験記録に基づく。検索で得た別版を8.5.2の証拠へ置き換えていない|
|[NMR34-FULL全報告](../P1-NMR34-FULL/review-dossier.md)、[全量監査](../P1-NMR34-FULL/delivery-audit.json)|全文と全compact SHA、272保存窓JSONのSHA/metadata|今回の主要一次証拠。raw座標の新規再計算はしない|
|[B1計画](../P1-B1-Expansion/analysis-plan.md)、[情報時刻](../P1-B1-Expansion/data-lineage-plan.md)、[乱数報告](../P1-B1-Expansion/randomness-analysis.md)|条件、祖先、乱数階層、識別制限|F0とContinue MDの違い、F2−F1の推定対象|
|[R1報告](../P1-B1-R1/review-dossier.md)、[Post-R1資格](../P1-Post-R1-Qualification/qualification-review.md)|既存審査と保存結果|共通履歴集合依存、未識別交絡。今回再計算しない|
|[Q0](../P1-Q0/review-dossier.md)、[L1](../P1-L1/review-dossier.md)、[L2](../P1-L2/review-dossier.md)|既報の資格結果と失敗/制限|物理準備、学習量、表現・seed安定性。旧結果を書き換えない|
|[N1 CPU](../P1-N1/CPU-v1/review-dossier.md)、[N1独立審査](../P1-N1-Review/review-dossier.md)|native結果・歴史進展・窓境界・C/B2の未決事項|minimumと新規進展の区別、既存主張の継承|
|[速水先生の助言記録](../研究打合せ/2026-10-30-速水先生-差別化と科学評価.md)|研究者が共有した文章と記録の状態|HPC用途の科学評価。本人による全パラメータ承認と解釈しない|

DeepDriveMD/Colmenaの新規性を本輪で再認定していない。既存の[文献対照](../P1-N1/README.md)を継承し、「AI＋MD」や「再訓練時刻」だけを新規性としない。本報告はNMR参照感度の査読であり、先行研究全体の最新網羅調査を称しない。
