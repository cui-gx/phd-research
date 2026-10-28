# 証拠と原著の索引

2026-10-28 JST。基準はR1最終commit `d43e606755b83ddb9e71399860ef27e550662c57`。本輪は保存済み文書・表・固定ソースの読取りと文献確認のみ。文献の方法を本系の資格証明へ置き換えない。

## E：プロジェクト内の証拠

|ID|所在・確認箇所|支持する内容と限界|
|---|---|---|
|E1|[入力manifest](../../inputs/p1-fsd-ey/manifest.json)、[S2物理監査](../P1-S2/science-protocol-audit.md)、[補充資格](../P1-S2-supplement/science-readiness.md)|ファイルの出所、配列・原子・電荷、準備史の欠落。S2の1nm条件をB1へ混同しない|
|E2|[GQ物理プロトコル](../P1-GQ/physics-protocol.md)、[B1品質](../P1-B1-Expansion/data-quality.md)、[quality.json](../执行证据/2026-10-26-b1-expansion/quality.json)|NoCutoffへの探索的移行、力の分項感度、粗い安全検査。平衡・溶媒精度の証明ではない|
|E3|[B1学習仕様](../P1-B1-Expansion/model-training.md)、[models.json](../执行证据/2026-10-26-b1-expansion/models.json)、[checkpoint読戻し](../执行证据/2026-10-26-b1-expansion/checkpoint-readback.json)|80モデルの系譜、200歩、800提示、復元。loss.jsonのSHAはあるが、全loss本文はこの公開表にない|
|E4|[B1科学関数](../../p1/server/b1_science.py)のai、[Expansion科学関数](../../p1/server/expansion_science.py)のtemporal_indices / selection / state_features、[固定設定](../../configs/p1_server_science.json)|実際の時間split、optimizer復元、seed、候補、LOF。設定の既定random splitはB1で呼ばれず明示時間splitを使用|
|E5|mdlearn固定版：[AE.recon_loss](../../vendor/mdlearn-938cb80/mdlearn/nn/models/ae/model.py)、[VAE.reparametrize / kld_loss](../../vendor/mdlearn-938cb80/mdlearn/nn/models/vae/model.py)、[trainer._train / _validate / predict](../../vendor/mdlearn-938cb80/mdlearn/nn/models/vae/symmetric_conv2d_vae.py)|BCE sum、KL batch mean、batch平均、eval時mu。ソースの静的読取りであり再推論ではない|
|E6|[R1完全報告](../P1-B1-R1/review-dossier.md)、[主根要約](../P1-B1-R1/main-root-summary.csv)、[主参照分解](../P1-B1-R1/main-reference-decomposition.csv)、[分解要約](../P1-B1-R1/reference-decomposition-summary.csv)|4ns/100psの既報値と全条件への索引。引用値を再推定していない|
|E7|[全尺度段階差](../P1-B1-R1/all-scale-stage-differences.csv)、[主離散表](../P1-B1-R1/main-discrete-counts.csv)、[全根要約](../P1-B1-R1/root-summary.csv)|全6連続・6離散・12窓を保存。代表表の陰性を隠さない|
|E8|[候補診断](../P1-B1-R1/pool-selection-diagnostic.csv)、[選点由来](../P1-B1-R1/selected-origins.csv)、[selection-effect-links](../P1-B1-R1/selection-effect-links.csv)、[LOF監査](../P1-B1-R1/LOF-audit.json)|保存embeddingによる制限と再fit。未実行Top1にはMD成果がない|
|E9|[B1乱数審査](../P1-B1-Expansion/randomness-analysis.md)、[R1主乱数表](../P1-B1-R1/main-randomness-diagnostic.csv)、[X/Z/W審査](../P1-B1-Expansion/state-dependence-analysis.md)、[features.json](../执行证据/2026-10-26-b1-expansion/features.json)|8根、2×3階層、共有F0、段階交絡、重複特徴。Xの検証済み独立価値ではない|
|E10|[費用報告](../P1-B1-Expansion/cost-and-runtime.md)、[costs.json](../执行证据/2026-10-26-b1-expansion/costs.json)|4ns MD、訓練・推論の実測時間。B2同一締切比較は未実施|
|E11|[R1入力索引](../P1-B1-R1/data-index.md)、[raw SHA](../执行证据/2026-10-26-b1-expansion/raw-artifact-sha256.json)、[R1入力SHA](../P1-B1-R1/input-file-sha256.csv)、[最終不変性](../P1-B1-R1/final-integrity.json)|原データと9archiveの既報照合。今回サーバ再接続なし|
|E12|[R1再現精度](../P1-B1-R1/original-reproduction-accuracy.json)、[結果監査](../P1-B1-R1/result-audit.json)、[状態](../P1-B1-R1/status.json)|240枝の元評価再現と完了、独立科学審査PENDING|
|E13|[GQ-R2報告](../P1-GQ-R2/README.md)、[R1指標計画](../P1-B1-R1/analysis-plan.md)、[B1指標契約](../P1-B1-Expansion/metric-contract.md)|固定庫の代表性不足、距離・角度・Rg/Q・離散尺度の正確な旧定義|

原lossの論理位置は `tasks/{state}-{label}/science/loss.json`。labelはM0、F1-t1/t2、F2-t1/t2。各ファイルのSHAはE3とE11で追跡できる。本輪は80個の原loss本文を新規取得しておらず、loss曲線の具体的な傾向・値・収束を認定しない。原DCD、重み、全ログのMac転送を要求しない。

## L：今回確認した一次資料

以下は2026-10-28にアクセス。引用は必要箇所の要約であり、全文転載しない。

|ID|一次資料・locator|今回の読取範囲・使用法|
|---|---|---|
|L1|[RCSB 1FME](https://www.rcsb.org/structure/1FME)、Experimental Data Snapshot / Literature、Sarisky & Mayo (2001), DOI [10.1006/jmbi.2000.4345](https://doi.org/10.1006/jmbi.2000.4345)|PDB記録本文と原著抄録。28残基、solution NMR、34提出構造。原著全文を本輪で精読したとはしない。実験条件を未記録MDのpHへ転記しない|
|L2|[OpenMM 8.5.2公式ソースガイド](https://github.com/openmm/openmm/blob/8.5.2/docs-source/usersguide/application/02_running_sims.rst#L620-L675)、Implicit Solvent|固定版該当節本文。GBn2、cutoff選択、dielectric、salt screeningのAPI意味。一般的推奨は本系の精度保証ではない|
|L3|Nguyen, Roe & Simmerling (2013), [Improved Generalized Born Solvent Model Parameters for Protein Simulations](https://pmc.ncbi.nlm.nih.gov/articles/PMC4361090/), Results: Parameter fitting / Results on test sets、Tables 1–3|検索経由で原著本文該当節・表を確認。直接openはrecaptcha。GBn2は検証系に対する近似改良であり、FSD-EY/本設定の独立検証ではない。補足全体は未読|
|L4|Grossfield et al. (2019), [Best Practices for Quantification of Uncertainty and Sampling Quality](https://livecomsjournal.org/index.php/livecoms/article/download/v1i1e5067/913/2595), §§4.4,5,7.2–7.3、PDF pp.10–16、DOI10.33011/livecoms.1.1.5067|該当本文を確認。初期緩和、独立系列、相関と不確実性の扱いを参照。未訪問状態や力場誤差が解消したとは言わない|
|L5|Chodera (2016), [A Simple Method for Automated Equilibration Detection in Molecular Simulations](https://pubmed.ncbi.nlm.nih.gov/26771390/), DOI10.1021/acs.jctc.5b00784|一次抄録とL4の解説箇所。実効標本数最大化を将来の診断候補とする。実施済み/全系平衡証明とは扱わない|
|L6|Bhowmik et al. (2018), [Deep clustering of protein folding simulations](https://link.springer.com/article/10.1186/s12859-018-2507-5), Methods、Figs.1–4,7、DOI10.1186/s12859-018-2507-5|本文のデータ・学習/検証・別軌道への適用を確認。BBAは223+102μs、325K、CHARMM22*系の別条件。本研究の短いGBn2軌道や200歩の十分性へ移植しない。epoch数をそのまま要求しない|
|L7|Hruška et al. (2018), [Quantitative comparison of adaptive sampling methods for protein dynamics](https://www.kavrakilab.org/publications/hruska2018quantitative-comparison-of-adaptive-sampling.pdf), §§II-B–D、III、DOI10.1063/1.5053582|著者公開原稿のMSM構築・synthetic trajectory手順・目的別評価を確認。既存軌道から構成したMSM上の比較で、全方策を新たな実MDで比較した論文ではない。本提案の連続幾何スコアを直接認証する文献ではない|
|L8|[scikit-learn 1.6.1 LocalOutlierFactor](https://scikit-learn.org/1.6/modules/generated/sklearn.neighbors.LocalOutlierFactor.html), novelty / negative_outlier_factor_ / score_samples|公式API本文を確認。fit集合に対するLOFと未知点へのnovelty scoringは同じではない。将来案で暗黙に切り替えない|
|L9|Athey & Imbens, [Recursive Partitioning for Heterogeneous Causal Effects, arXiv v3](https://arxiv.org/pdf/1504.01132), pp.1–3；出版版DOI10.1073/pnas.1510489113|著者原稿のhonest splitの動機・定義を確認。発見と効果評価の分離を設計原則として参照。本研究へ木手法や有効な小標本CIの保証を移植しない|

## 審査方法と限界

根/枝の既報数値、ソースの意味、文献の一般原則、本輪の提案を分けた。新しい蛋白質物理の専門家意見、loss値、未保存のモデル表現、実wall-clock反実仮想は得ていない。検索で見つけた関連レビューや二次記事を資格の主根拠にしない。未取得文献を読んだとせず、原著の結果と本研究への推論を分離した。
