# 証拠索引と一次資料

2026-10-29 JST。GitHub mainの基準`83bac631c007366d1492330fe3355677d4f5eeaf`を取得して読んだ。本輪は公開済み表・報告・固定版ソースコードの静的読取りであり、サーバ原ファイルの実在・SHAを新たに確認していない。設計前ファイルSHAは[evidence-input-sha256.json](evidence-input-sha256.json)。

## 1. 内部証拠

|ID|実資料|読取り/使用目的と限界|
|---|---|---|
|E1|[B1完全報告](../P1-B1-Expansion/review-dossier.md)、[metric contract](../P1-B1-Expansion/metric-contract.md)、[費用](../P1-B1-Expansion/cost-and-runtime.md)|等MD量、固定800/200歩、8根階層、実測費用。L2下流Yへ流用しない|
|E2|[R1完全報告](../P1-B1-R1/review-dossier.md)、[A–G](../P1-B1-R1/handoff-to-chatgpt.md)|参照依存、候補と密度の交絡、NOT_OBSERVED。L2はR1の再解析ではない|
|E3|[Q0完全報告](../P1-Q0/review-dossier.md)、[model-lineage](../P1-Q0/model-lineage.csv)、[recipe](../P1-Q0/model-recipes.json)|80モデル系譜、batch/lossの尺度、r07有限尖峰、未保存分項。新実験を既報に混ぜない|
|E4|[Q0 exposure](../P1-Q0/model-exposures.csv)|各armの800 membershipと位置順の転記。将来サーバindicesと照合が必要|
|E5|[L1完全報告](../P1-L1/review-dossier.md)、[A–G](../P1-L1/handoff-to-chatgpt.md)、[全モデル値](../P1-L1/model-metrics.csv)、[幾何](../P1-L1/geometry-overview.csv)、[seed安定性](../P1-L1/seed-stability.csv)|既報80モデルの再構成/幾何/seedの限界。今回の4状態で数値を再計算していない|
|E6|[L1評価ID](../P1-L1/validation-ids.csv)、[cohort](../P1-L1/frozen-cohorts.json)、[checkpoint監査](../P1-L1/checkpoint-audit.csv)|固定二集合の転記、既報原SHA/有限性/同CPU決定性|
|E7|[L1保存配列SHA](../P1-L1/array-sha256.json)、[原入力SHA](../P1-L1/freeze-input-sha256.json)|serverのmu/logstd/reconstruction配列と入力のlogical path。E0案の可用性根拠、今回ロードしていない|
|E8|[原models](../执行证据/2026-10-26-b1-expansion/models.json)、[原raw索引](../执行证据/2026-10-26-b1-expansion/raw-artifact-sha256.json)|親/weight/optimizer/RNGdigest、原入力への追跡。archiveをMacへ移さない|
|E9|[L1費用](../P1-L1/cost-ledger.json)、[環境](../P1-L1/execution-status.json)|CPU134.207秒wall、peakRSS721.449MiB等の既報。新L2性能ではない|
|E10|[Post-R1最小設計](../P1-Post-R1-Qualification/minimal-design.md)、[費用案](../P1-Post-R1-Qualification/cost-and-gates.md)、[資格審査](../P1-Post-R1-Qualification/qualification-review.md)|r01/r02の4状態案、36chainの出発点。親を事前固定する本案は旧案の選択的親設定を具体化・変更する提案|
|E11|[B1学習/選択](../../p1/server/b1_science.py)、[L1診断](../../p1/l1_frozen_diagnostic.py)|学習直前RNG、親optimizer、permutation、eval mu、mask、LOF定義のソースコード確認。旧ソースコードは変更なし|
|E12|[mdlearn VAE](../../vendor/mdlearn-938cb80/mdlearn/nn/models/vae/model.py)、[CVAE trainer](../../vendor/mdlearn-938cb80/mdlearn/nn/models/vae/symmetric_conv2d_vae.py)|train時sample/eval時mu、BCE総和/KL平均、clip、RMSpropの固定実装。commit938cb80ac3ebe33498dbcb2780f97f81ec80e0f8|

今回のID表は公開されたmetadataの部分集合であり、新しく抽出した科学frameではない。実行時には原入力に対する検査を省略しない。サーバにのみ残る原重み・軌跡・forward配列の取得/計算は本輪の実施事項ではない。

## 2. 方法の一次資料

### L1 — Kingma & Welling, Auto-Encoding Variational Bayes

[arXiv:1312.6114v11](https://arxiv.org/html/1312.6114v11)、原稿2013/ICLR2014、参照版v11。今回確認した範囲はabstract、§2.2–2.3、Gaussianの場合の式とAppendix B。対角GaussianのKL式と再パラメータ化の根拠を用いる。物理近傍保存や本P1の200/1600歩の十分性を保証する文献ではない。全実験の再読・再現を行ったとは主張しない。

### L2 — Bhowmik et al., Deep clustering of protein folding simulations

[BMC Bioinformatics 19, 484 (2018), DOI 10.1186/s12859-018-2507-5](https://link.springer.com/article/10.1186/s12859-018-2507-5)。確認範囲はabstract、Methodsのデータ/前処理/CVAE、Fig.1の説明。接触図を畳み込みVAEへ入力し低次元化する方法上の出典である。同論文の1FME/BBA長時間データは325 K、CHARMM22*と明示的溶媒の条件で、本P1の短いGBn2履歴と異なる。原著の学習epochや成績を本P1の合格閾値へ転用しない。モデル形が似ているだけで同じ科学資格を認めない。

### L3 — scikit-learn LocalOutlierFactor公式API

[scikit-learn 1.6 API](https://scikit-learn.org/1.6/modules/generated/sklearn.neighbors.LocalOutlierFactor.html)。negative_outlier_factor_、novelty、score_samplesの説明を確認した。fit集合内で低いnegative factorを外れ側とする現在の順位方向、novelty=Falseと未知点スコアの区別を確認するために使用。LOF順位が科学探索に有効であることを示す資料ではない。実行時libraryの実版はサーバで別確認する。

## 3. 文献から導けない設計値

3初期化、4状態、200/400/800/1600歩、平均コード/5offset、全候補評価、運用保護値は本L2の操作的提案で、原著が最適性や検出力を保証した値ではない。K10、NONLOCAL/LONG、頻度0.5擬似度数はL1との比較可能性を優先して継続する。研究者が採択するまではPROPOSEDである。
