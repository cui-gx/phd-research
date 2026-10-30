# 一次文献と指導助言の照合

2026-10-30。本文・図表の根拠と当研究の解釈を分ける。著者版PDFと公開本文、既存の固定[文献SHA索引](../P1-N1/sources.json)、[前回の全比較](../P1-N1/related-work-matrix.md)を参照した。商用最終版と著者版の細部一致が確認できない箇所は残す。論文の文章を長く転載せず、必要な条件を要約する。

|一次資料・具体箇所|論文で確認した事実／実験境界|P1への含意と未検証部分|
|---|---|---|
|Bhowmik et al. (2018), *Deep clustering of protein folding simulations*, Methods、Results冒頭、Table 1、Fig.2–4/7。[本文](https://pmc.ncbi.nlm.nih.gov/articles/PMC6302667/)、[DOI](https://doi.org/10.1186/s12859-018-2507-5)|BBA/1FMEはAntonの223/102 μs、325 K、CHARMM22*とmodified TIP3P。CVAEで構造を表現し、別軌跡へ写像。Q記述にはCA8 Å以下、75%、native RMSD1.1 Å条件が含まれる。BBAの潜在次元最適化と3D可視化の選択は別。|既にCVAEの構造表現・汎化を扱う。300 K/Amber14/GBn2・短枝とは異なり、同じモデル名だけで学習資格を移転できない。Qをmodel1の42接触やNMR34の75%共識と同一視しない。原解析コード・Qの完全操作的再現は未取得。|
|Ma et al., *Deep Generative Model Driven Protein Folding Simulations*、著者版arXiv1908.00496v1、§4.1/Table1。[著者版](https://arxiv.org/abs/1908.00496v1)、[2020出版DOI](https://doi.org/10.3233/APC200023)|DGX2/V100、MDとMLに別GPU、OpenMM/ff99SB-ILDN/OBC、CVAE学習と候補選択。FSD-EYの45軌跡合算18.562 μs、最良4.44 Åだがnativeを得たとの主張ではない。|4.44 Åは観測値で成功閾値ではない。P1の3.614 Åと直接性能順位をつけない。物理条件、実時間、参照とnativeによる選点の有無が異なる。出版最終版との差はUNVERIFIED。|
|Lee et al. (2019), *DeepDriveMD: Deep-Learning Driven Adaptive Molecular Simulations for Protein Folding*, §3–4。[著者版](https://arxiv.org/abs/1909.07817v1)、[DOI](https://doi.org/10.1109/DLS49591.2019.00007)|MD→集約→CVAE→選点の反復、Summit上の実行。Fs-peptideとVHPを区別。Fsの14対6 μsという比較は既学習データ等の境界を持つ。明示溶媒でfoldしなかった例はVHP。|先生の溶媒コメントを「FSD-EYは明示水で不可能」と一般化しない。学習時間を除いたsampling量の比較をend-to-end速度改善としない。|
|Brace et al. (2022), *Coupling streaming AI and HPC ensembles to achieve 100–1000x faster biomolecular simulations*, v5 §IV–VI、Fig.3/5/6、Table I/II。[全文](https://arxiv.org/html/2104.04797v5)、[版情報](https://arxiv.org/abs/2104.04797v5)|DeepDriveMD-F/S、同期/streaming並行を比較。UC1はFSD-EY、ff99SB-ILDN/OBC。ML-only、native greedy、ML+nativeを比較し、12時間10試行の最良RMSD平均2.37±.30対1.81±.21 Å。Fig.3のML-onlyでは小RMSDへの分布移動を示さなかった。|同時間・更新・科学指標自体は既存。良い結果にはnativeでの選点も含み、nativeを隠すP1のLOFと同一基線ではない。ML-onlyの陰性例は選点目的とnative目標の不一致を検討する根拠だが、P1の失敗を予言する証拠ではない。|
|Ward et al. (2021), *Colmena: Scalable Machine-Learning-Based Steering of Ensemble Simulations for HPC*, §IV-C。[著者版](https://arxiv.org/abs/2110.02827v1)、[DOI](https://doi.org/10.1109/MLHPC54614.2021.00007)|QC結果→MPNN更新→再順位、Theta上でrandom/no-retrain/update方策を比較。simulation量だけでなく高価値候補を評価する。|AI+simulation閉ループ、再学習、科学応答への時間配分は既にある。分子選択問題と蛋白質構造サンプリング、CPU大規模実行と1共有GPUを分ける。ハード変更だけで普遍的新規性としない。|
|Ward et al., *Employing Artificial Intelligence to Steer Exascale Workflows with Colmena*, arXiv2408.14434v1、§5.2/Fig.6。[全文](https://arxiv.org/html/2408.14434v1)、[出版DOI](https://doi.org/10.1177/10943420241288242)|旧モデルを使い直ちに判断する場合と、学習を待って判断する場合の取捨を明示する。非同期学習・streaming・on-demand推論、worker資源の調整を実装可能にする。|「いつ更新するか」を初提案とは書けない。今回の候補は、固定情報・強いZ/W対照・未知根でXが追加情報を持つかと、その費用込み実時間利益の実測。まだ実証されていない。|
|RCSB PDB 1FME、Experimental Data Snapshot。[公式](https://www.rcsb.org/structure/1FME)|solution NMR、49構造を計算し、拘束違反の少ない34構造を提出。28残基。|34個は34独立MD試行でも平衡分布からのiid標本でもない。model1以外を使う感度は合理的だが、最小を取ると必ず近く見える選択効果が生じる。|

## 主張の整理

**DERIVED**：再利用するのは既存科学関数、参照なしの表現/選択、固定・更新・周期更新の基線である。原DeepDriveMDのnative-informed選点を取り除いた実験は、原論文の忠実な最強結果再現とは名乗らず、情報条件を統一した基線への適応と書く。現在は既存Parsl適配層であり、Colmena全runtimeの性能を評価したことにもならない。

**PROPOSED**：研究仮説は「科学フィードバックXが、費用・残時間・学習履歴・既存の物理要約Wを含む強い基線に追加情報を与えるか」「その情報を計算する費用を払ってもnativeへの有限時間進捗に利益が残るか」。純予測の改善、単一decisionの更新価値、複数decisionのスケジューリング利益を分ける。相関や他GPUの既報結果だけでは、この差異を確定的貢献にしない。

**UNVERIFIED**：本設定の新規性の排他性、現配方での良質なlatent反応座標、単GPU競合の大きさ、600秒で検出できる差。文献と重なる部分があっても、条件を明示した性能実証・陰性結果・再現可能な判断境界には価値があり得る。採択可能性や論文成立を保証しない。

## 速水先生の助言の位置

[元記録](../研究打合せ/2026-10-30-速水先生-差別化と科学評価.md)は、FSD-EYを具体的な題材として保ち、native RMSDや潜在分布を用い、先行研究との条件比較を明確にする助言である。物理的健全性の点検を省く許可や、本書の閾値・新GPU計算の承認ではない。暗黙溶媒から明示溶媒へ本作業で変更しない。

今回の引用確認は上記の原文・図表を対象とする。参照PDFの元SHAは前回sources.jsonに保存済みで、新しいPDFをGitHubへ再配布しない。取得日時と本文版を将来の最終論文で再確認する。
