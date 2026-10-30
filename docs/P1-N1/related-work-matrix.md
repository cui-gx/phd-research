# 原文・実装とP1の対照行列

2026-10-30。原文の事実、当研究の適応案、未実証仮説を分離。原論文の全補足・artifactを実行したという意味ではない。[版・取得範囲](sources.json)。著者版と出版者版の違いを明示し、数値の機種横断順位を作らない。

|論文・確認箇所|物理系・資源・学習|実際の制御／科学評価|当研究で可能な再利用|未実証差異と必要な新証拠|
|---|---|---|---|---|
|Bhowmik 2018、Methods/Results、Table1、Fig7 [DOI](https://doi.org/10.1186/s12859-018-2507-5)|BBA/1FME、Antonの223/102µs、325K、CHARMM22*＋modified TIP3P。contact<8Å。BBA最適latent10、3Dも比較|既存長軌跡のCVAE表現・他軌跡への転用。native RMSD/Qで着色。オンライン資源方策の比較ではない|contact/CVAE・物理色付き表示と独立軌跡検証。現在のmdlearn recipeは忠実同一でない|200歩・800枚・3Dの十分性は原結果から認定不能。L1/L2陰性を保持。将来nativeへの関係を別承認で評価|
|Ma et al. 2020出版書誌／2019著者版§2–3.1、Table1–2 [著者原文](https://arxiv.org/abs/1908.00496)|Fs/BBA、OpenMM7.3、ff99SB-ILDN/OBC、300K、非周期10Å cutoff、2fs、friction91ps⁻¹。DGX-2 V100×16をMD12/ML4。CVAE100epochs|Celery反復、latent/DBSCANとnative RMSDによる起点絞込み。BBA45軌跡18.562µs、最小4.44Å、完全native到達とはしていない|同期/非同期task機構、同じFSD-EYという載体。選点をnative可視にする原条件は本主案へ混ぜない|本B1のff14SB/GBn2/NoCutoff/300K/friction1、少量データと相違。4.44Åをfolded閾値にしない。正式2020全文の実装差は未確認|
|Lee et al. 2019、§III–V、Fig1/3/4 [原文](https://arxiv.org/abs/1909.07817)|Summit、OpenMM/CVAE/RADICAL。Fs implicit OBC/ff99SB-ILDN/300KとVHP explicit TIP3P。VHP合計0.9µs|MD→learn→outlier→再MD、計算・学習のscaleを評価。2.33×はFsの初期学習後6µsと従来14µsの比較で、初期12µsを含む総wall利益ではない|反復段階の基線、初期学習費を含む比較の必要性|VHPの未foldをFSD-EYや全explicit solventの失敗へ一般化しない。個別MD長について本文50ns/議論100nsの表記差があり、参照条件を単一値へ補完しない|
|Brace et al. IPDPS2022、arXiv v5 §IV–VI/Fig3/TableI/7 [原文](https://arxiv.org/abs/2104.04797v5)|UC1 BBA、ff99SB-ILDN/OBC。UC2大蛋白TIP3P。CVAE latent10、64filters、dropout0.4。最大1020nodesの尺度化|Fは段階同期、Sはstreaming同時loop。UC1はDBSCAN＋native絞込。12h×10試行でgreedy native平均best2.37±0.30Å、ML+native1.81±0.21Å。ML-onlyで同じRMSDシフトは見られない|周期更新・旧モデル再利用・native-informed陽性対照の区分。実wall比較自体は既存|単GPU・native非可視条件へ数値利益を移せない。モデル更新時刻だけで初創を主張せず、X増分と機会費用を新試験で検証|
|Ward et al. Colmena2021、§II–IV-C、Fig4 [原文](https://arxiv.org/abs/2110.02827v1)|Theta256nodesの分子QC(NWChem B3LYP/3-21G)/MPNN、FSD MDではない|Thinker/TaskServer/Workers、ResourceCounter、QC成功8件でupdate-8。random/no-retrain対比。約5%少ないsimulation時間で高価値候補約10%多い例。feedback遅延57min|到着件数trigger、旧モデル/更新、学習とsimulation poolの調整を制約内で適応|資源対科学成果の取捨は既存。単GPU性能やnative RMSD利益の証明ではない。63/537と原文15%は集計定義が不明で独自整合率にしない|
|Ward et al. online2024/issue2025、§5.2/Fig6 [原文](https://arxiv.org/html/2408.14434)|Colmena複数応用とDeepDriveMD連携、非同期simulation/ML、専用accelerator・ProxyStore等|stale modelですぐ判断か、train完了を待つかを明記。on-demand inference、streaming、resource steering。DDMD100–1000×は引用先由来で独立再現ではない|STALE_IMMEDIATE、更新待機、非同期実装パターン|待つ/再学習する問題自体は既知。固定資源下のnative非可視X条件付き価値と実方策の効果は今回未測|

## 固定した現在の公開コードを静的に確認した事実

DeepDriveMD-pipeline commit `a44d394fa3dc500c4f02b6086ed5b1f87df2556a`：`deepdrivemd.py` L66–80はstage_idx%retrain_freqでtrain stageを生成、`config.py` L146–147の既定retrain_freq=1、`selection/latest/select_model.py` L109–127は非更新iterationで旧checkpointを再使用する。stream側は四成分を別pipelineで走らせ、資源は各stageのcpu/gpu requestで規定する。現行スナップショットの静的読解で、2022全実行版の同一性や当環境での機能成功ではない。

Colmena commit `88314f341b18fc598c3124a1c246272f820b6829`：`thinker/resources.py`のacquire/release/reallocateはslot poolを管理する。実hardwareのCUDAメモリ分割や動作中OpenMMの任意resizeを実装した意味ではない。Thinkerは方策を利用者が定義する構造で、ライブラリだけから最適な更新時点が得られるわけでもない。各固定URL/SHAは[sources](sources.json)。原コードは実行・変更せずlocal参考コピーのみ。

## 重複と残る仮説

AI+MD、CVAE・LOF/DBSCAN選点、再学習頻度、同期/非同期、固定wall-clockでの科学成果、staleness/資源配分は直接重複する。残すのは**同じ許可GPU、同じnative非可視条件、同じモデル配方の下で、既定の強いZ/Wを超える決定前Xの情報があるか／その情報が同じ真の締切で低RMSD成果へ伝わるか**という未実証仮説。ハードウェア移植と実証条件の違いには探索価値があるが、新規性の十分性や投稿可能性を保証しない。

忠実再現可能な要素（計量・頻度・旧checkpoint）と、一枚カードへの本研究の適応（stage直列・CPU LOF・終了規則）を区別する。native-guided先行法をblinded方策の公平baselineと称さず、必要なら別情報条件の上限参考として追加承認を求める。
