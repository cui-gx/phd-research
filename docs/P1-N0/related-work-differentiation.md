# P1-N0：DeepDriveMD・Colmenaの既知範囲と本P1の差別化案

2026-10-30 JST。文献に記載されていることと、当研究が**これから検証する仮説**を分離する。先行研究の方法が行っていないと確認できない事項を「先行研究は扱わない」と断言しない。全論文と実装の網羅的系統レビューは未完了。

## 1. 比較表

|仕事・代表文献|確認済みの研究内容／尺度|本研究との重なり|必要な差別化・比較検証|
|---|---|---|---|
|Bhowmik et al. 2018 CVAE|既存MDからCα 8Å contactをCVAEにより低次元化し、native RMSD・native contactsで潜在空間の構造差を読む。BBA/FSD-EYも使用|CVAE/contact/latent/折り畳み説明は既知|新しいCVAEアルゴリズムと主張しない。latent診断とfolding progressの関係をB1/L2で確認する|
|Lee et al. DeepDriveMD 2019|DL表現がMDの適応サンプリングを誘導し、Fs-peptide・villinで計算費とfoldingの効率を調査。従来法比の性能利益を報告|AI→MD選点とRMSD/効率の評価は既知|同一の科学ワークフローで単共有GPU時のMD vs 更新の排他・順序・費用を介入因子とし、公平な同一wall-clock比較を設計|
|Ma et al. 2020 FSD-EY|Deep generative modelでFSD-EY adaptive folding。総サンプリング18.562µs、最小native RMSD4.44Å。天然foldを完全サンプルしたとは主張しない|分子対象FSD-EY・CVAE系adaptive workflow・native指標と重なる|同じ分子だからといって成果を直接比較しない。物理条件、初期分布、利用GPU、総MD長、RMSD原子対応を明示する|
|Ward et al. Colmena 2021|ML代理モデル・simulation ensembleのタスクキュー、モデル学習/再学習、動的な順序・資源割当を一般化。実証用途は主に電解液設計|workflow scheduling・ML retrainingは既知|単に「動的にモデルを更新」「AI+MD統合」は新規性ではない。Colmena上でも実現し得る方策と価値関数を定量比較|
|Ward et al. Colmena exascale 2025（オンライン2024）|旧モデルですぐ判断するか、新モデルのために待つかという速度vs精度、専門GPU、非同期AI・simulationの要素を論じる|モデル陳腐化・待機コスト・非同期制御も既知|stale-model使用、周期/固定更新、MD継続、状態依存updateを同一資源で比較し、科学XのZ/Wに対する追加予測価値と純wall-clock利益を独立根で評価|

## 2. 検証可能な研究仮説（まだ新規性・効果が確定していない）

**対象**：単一共有HPCクラスター、研究者が許諾した範囲で実行順序・GPU割当・MD続行とCVAEの更新/推論可否を制御。1枚GPUという資源制約でMD/学習/推論が実際に競合するケースを基準とし、GPU利用率自体は科学成果ではない。

**候補の中心問い**：「**決定前に観測可能な科学状態Xが、費用・利用率・進行状態Z/Wだけの判断に比べ、AI更新の追加科学価値を予測できるか；その情報を使う方策は、同一wall-clock内により低いnative RMSD/より高いnative Qの妥当な構象をサンプリングできるか**」。

これには二つ別の立証が要る：`predictive incremental information`（見えない根への予測改善）と`policy-level causal utility`（現実の共通時間枠での到達）。Xの特徴がWと重なるなら重複したラベルによる見せかけの性能を排除する。B1/R1のS4/S8差、L2のloss/LOFや選点変化からはどちらもまだ確認できない。

## 3. 比較方策とfairnessの最小表（将来試験用提案）

1. `CONTINUE_MD`：更新を実施しない／旧モデルによる選点の扱いを明示（train負担なし）。
2. `PERIODIC_UPDATE`：事前固定周期・更新処理。DeepDriveMD型の繰返し更新に対応する操作的基線。原論文と完全一致するかは別に検証する。
3. `STALE_IMMEDIATE`：新モデル待機をせず既存モデルで決定。Colmenaの速度−鮮度tradeoffに対応した比較基線。
4. `COST_ONLY_UPDATE`：Z/Wのみ（事前更新費用、GPU競合、滞留、MD進行）を判断。Xに追加価値があるかの直接対照。
5. `SCIENCE_AWARE_UPDATE`：同じコスト・候補・訓練アルゴリズムにXだけ追加して判断。未知根で評価し、方策学習・閾値校正・評価根を分離。

上記は**固定済み既存論文の忠実な再実装ではなく、本研究の操作的対照候補**。先行アルゴリズムのコード/更新規則と齟齬がないか個別確認を要する。無制限CPU/GPUの並列基線を1GPU枠内の方策と「同一予算」扱いしない。

必要な同一条件：力場/溶媒/温度、初期構象・乱数階層、モデル学習/入力時点・選点候補、推論、reseed/MD長、品質判定、利用可能GPU/CPUと同一締切秒。学習・推論・I/O・待ち・障害・スケジューラオーバーヘッドを課金。分子軌道のnsとwall-clock秒は混同しない。未来情報のnative referenceは評価器のみで、X/方策へ混入させない。

## 4. scientific outcomesとsystem outcomesを同時に報告する

- **科学主尺度候補**：同じ時間締切までに得られた最小native Cα RMSD[Å]。小さいほどnativeへの近さ。連続量であり、4.44Åや任意のfolded閾値を自動的な成功判定にしない。Q_native、分布、予め固定した閾値への到達率・first-hit、結果品質と構象滞留を補助とする。
- **ワークフロー尺度**：実wall-clock、MD累積サンプリング量、train/infer/MD/待機/I/O別実測、GPU競合・失敗・公開済み観測量。MD量が異なるならその差自体が戦略の効果であり、隠さない。
- **不確実性**：根単位のpaired analysisと複数独立根。学習seedやMDseedは階層として扱う。確認の効果量・成功率等の閾値は新実験前に凍結する。
- **科学資格の上限**：GBn2/NoCutoffの同一モデル内での比較。折り畳みの物理的真値、平衡population、反応速度の正しさを主張しない。より妥当な溶媒条件は研究者/指導教員の別判断。

## 5. 本日時点で確定できること・未解決

**CONFIRMED（文献と原repo）**：CVAEのnative可視化は既知、DeepDriveMDの自適応MDは既知、Colmenaは更新・資源動的制御とstale model tradeoffを既に議論、1FMEはNMR34、L2科学結果は36chain技術完了。これらは差別化を厳しくする根拠。

**PROPOSED**：共通単GPUの資源競合とnative成果への価値に特化した方策対照、X追加価値の確認設計、主尺度・閾値・wall-clock期限の新契約。

**UNVERIFIED**：既存戦略に対する新規性の十分さ、native outcomeのB1事後値、学習の一般的資格、独立根上のX改善、B2固定時間純利益。

**引用資料**：
- Bhowmik et al. 2018, https://pmc.ncbi.nlm.nih.gov/articles/PMC6302667/
- Lee et al. 2019, https://doi.org/10.1109/DLS49591.2019.00007
- Ma et al. 2020, https://journals.sagepub.com/doi/10.3233/APC200023
- Ward et al. 2021, https://arxiv.org/abs/2110.02827
- Ward et al. (online 2024, issue 2025), https://journals.sagepub.com/doi/10.1177/10943420241288242
- RCSB 1FME, https://www.rcsb.org/structure/1FME
