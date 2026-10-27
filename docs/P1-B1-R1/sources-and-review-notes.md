# 出典・読取範囲・今回の点検境界

2026-10-28。新規科学結果を計算せず、既存証拠と固定ソースから方法を検討した。

## 一次資料

|資料|確認した箇所と本計画への使用|
|---|---|
|[B1完全報告](../P1-B1-Expansion/review-dossier.md)・[A–G引継ぎ](../P1-B1-Expansion/handoff-to-chatgpt.md)|全文。状態束、元の結果、未識別、保存/科学審査の境界|
|[指標契約](../P1-B1-Expansion/metric-contract.md)・[状態差](../P1-B1-Expansion/state-dependence-analysis.md)・[乱数分析](../P1-B1-Expansion/randomness-analysis.md)|全文。全尺度、X/Z/W、階層と既存交絡|
|[expansion_analysis.py](../../p1/server/expansion_analysis.py)|6連続量、時間mask、角の幾何最近傍、regions呼出、共有F0、根再標本化|
|[expansion_science.py](../../p1/server/expansion_science.py)・[b1_science.py](../../p1/server/b1_science.py)|pool/ID/時刻合法性、selected座標追跡、ranking保存、学習/LOFの手順|
|[gq_r2.py](../../p1/server/gq_r2.py)|dRMSD、block最近傍、持続条件とgreedy計数、角の周期差|
|[mdlearn VAE](../../vendor/mdlearn-938cb80/mdlearn/nn/models/vae/model.py)・[predict](../../vendor/mdlearn-938cb80/mdlearn/nn/models/vae/symmetric_conv2d_vae.py)|固定938cb80でeval時mu、predictのeval/no_grad。新推論を実行していない|
|[scikit-learn 1.6.1 LOF公式仕様](https://scikit-learn.org/1.6/modules/generated/sklearn.neighbors.LocalOutlierFactor.html)|Parameters novelty、Attributes negative_outlier_factor_、score_samplesの注意。LOFの標本内得点とnovelty予測を区別。候補集合変更時は近傍が変わり得るため、保存得点の絞込みと再fitを別操作として設計した|
|[Grossfield et al. 2018, Best Practices for Quantification of Uncertainty and Sampling Quality in Molecular Simulations, Article v1.0](https://pmc.ncbi.nlm.nih.gov/articles/PMC6286151/)|§4.4と§7.2を中心に確認。同一準備構造からの反復の不確実性はその準備条件に限定し、相関フレームを独立試料としない根拠。DOI 10.33011/livecoms.1.1.5067|

外部二資料は上記関連部分の方法確認であり、全分野の文献調査や論文新規性認定ではない。物理定数やMDの科学妥当性をLOF仕様から導かない。COMMON_A4・COMMON_A2・間引き・判定表は本課題に対するPROPOSEDな設計で、上記文献がその有効性を実証したものではない。

## 今回読んだ証拠の意味

GitHub mainを取得し、全局档案・AGENTS・協作記録・協作規範を確認した。全B1 CSVはファイル全体をCSV parserで走査し、列名/行数/指標名を確認した。代表行、全既報根別主表、報告とソースの意味を照合したが、41,472行の差、bootstrap、相関を**再計算したとは主張しない**。全目録は[input-inventory.json](input-inventory.json)。

本輪はサーバraw NPZ/DCD/重みを読み出していない。公開manifestに必要ファイルが登録されていることと、将来の再評価時に実ファイルが同SHAで読めることを区別する。元B1報告・ソース・結果のGit blob不変、文書リンク、schemaの静的検査だけを[点検証跡](static-checks.json)へ記録する。

## 審査上の透明性

既報の段階差を見てから評価参照の影響を検討する計画である。新評価結果を見る前に手順を固定しても、元実験の確認的事前登録や新しい独立標本にはならない。本Codexによる方法論的再検討であり、別の盲検査読者を起動した、S2独立終審を完了した、研究者が科学結論を受理したとは記載しない。
