# C/B2の最小・段階的なオンライン検証案

**PROPOSED / NOT APPROVED**。一枚GPU/FSD-EY/OpenMM/既存CVAEを維持。以下は審査可能な候補であり、新しい学習・MD・C predictorを実行しない。P/L資格・native成果が使えることを先に確認する。

## 1. 二つの推定対象を分ける

Cは同じdecision状態からUPDATE_NOW（親を更新→推論→候補MD）とSTALE_NOW（旧モデルで即推論→候補MD）の固定H後の差を測る。観測ラベルV_obs=B_stale(H)−B_update(H)[Å]、正なら更新のnative進捗優位。各分岐の全実費をHへ課金する。等MD nsの旧B1値では代用しない。

B2は複数decisionが起きるcampaignの方策割付効果。強Z/Wのみの方策と、同じ行動/配方/複雑さにXだけ追加した方策のB(H)の根内差が主対比。Cの予測誤差改善とB2の実成果改善は別で、一方だけでも両方成立としない。

これは1組の乱数実現に対する差で、目標とするE[V|s]の真値ではない。更新行動は追加最適化と新dataの両方を含み、旧dataだけ追加訓練するF1をこの最小新行列に置かないため、新data単独の因果効果を識別しない。Cは最初の一decisionだけを介入し、その後のモデルは固定した共通のrollout規則にする。B2は複数decisionのオンライン方策である。

## 2. 5方策と具体的な行動

|方策|制御するもの|推論・選点|費用・重複の注意|
|---|---|---|---|
|CONTINUE_MD|モデル更新なし、同じactive laneを安全checkpointから連続MD|モデル推論/LOFなし。初期固定lane規則|GPUはMDへ。固定長chunkは公開/終了境界のためで、毎chunkの座標minimize/reseedを連続MDと呼ばない|
|PERIODIC_UPDATE|新しい適格MD chunkがk件公開されたら更新。kはcalibrationだけで選んで凍結|その時点の最新model、固定候補集合規則|train/infer/LOF/切替を全課金。DeepDriveMDの反復に対応する適応版で忠実同一実装とはしない|
|STALE_IMMEDIATE|新data時もtrainを待たず固定M0で候補選定|各decisionで旧model inference＋LOF。必要なreseed|CONTINUEと違い候補を変える。queue再順位の効果と更新の効果を混同しない|
|ZW_ONLY|学習配方と行動を固定しZ/WからUPDATE_NOW/STALE_NOWを判断|選ばれたmodelだけで同じselector|余分なXを無料で計算しない。feature/decision/推定費用も課金|
|ZW_PLUS_X|ZW_ONLYに決定前Xだけ追加して同じ二行動を判断|selector・候補規則・GPU・モデル構造は同じ|X計算費も含めて評価。より大きいmodel/探索幅による利益にしない|

k=1が一度だけのdecisionではUPDATE_NOWと同じなら、同一基線と記録する。名前を変えて5独立algorithmと見せない。B2では少なくとも2decisionの余地があるかを資格測定で確認する。大きいtrain costを人工的に付け足して競合を演出しない。kの候補は1/2/4 completed chunksという小さい範囲案だが、chunk長・train recipe・Hと共に別承認して凍結する。

## 3. X、Z、Wの情報境界

元B1のZは実行量・候補数・旧/新数・model age/steps・過去費用、WはRg/Q8要約や既訪問セルも含む。したがってZW_ONLYは純粋な機械情報だけの弱い対照ではない。強い既存Wを削ってXの増分を作らない。

X1の旧/新内部距離新規度、X2の固定物理投影histogram変化を候補とし、元X3/X4がWから決まる部分は重複と明記する。新定義v2の採択は未承認。native r/Q、未来MD、更新後loss/rank/実測訓練費用を決定前featureへ入れない。特徴の入力公開時刻と計算完了を記録する。Xの計算が高価なら正味利益を損ない得る。

**最小情報実験**は同じ4ns時点・固定H・同訓練数・同候補規則に条件付け、まずX1一量の追加を検討する。Z/Wの変動・共線性・共通支持を先に調べる。候補数や時点でXが完全分離し、条件付き比較ができないならCはNOT_IDENTIFIABLE。12状態で多数featureの高次元学習を認定しない。必要calibration数が不足するなら予測器を作る前に停止し、研究者へ再設計を返す。

開発上は深いモデルを作らず、同じ簡単な回帰または有限候補のdecision ruleでZW対ZW+Xを比較する案とする。閾値/係数/正則化候補と探索回数はcalibrationでのみ選び、最終的にcommit固定する。本輪はその数値を採択せず、policy実装もしない。Brier等分類を使うならV>0の符号と効果量誤差を併記し、ゼロ近辺不確実性を消さない。

## 4. 開発・校正・未知根：最小行列案

|集合|根候補|役割|件数案|
|---|---|---|---:|
|既存開発|r01–r08のB1、L2はr01/r02のみ|構造・feature・失敗の設計。native新評価も事後|新計算0|
|新calibration|r09–r12、4独立random histories|同一4ns状態からU/Sの費用と作用を校正|4根×2action=8 rollouts|
|新blind diagnosis|r13–r20、8独立random histories|凍結したC予測の外部根誤差を観測|8根×2action=16 rollouts|
|B2 blind policy|同r13–r20の共通状態|凍結5policyの固定H成果|8根×5policy=40 rollouts|

[64行の候補行列](future-experiment-matrix.csv)。r09以降は未生成。全て同じunfolded準備からの異なるrandom履歴で、独立構造・独立物理系ではない。CとB2でr13–r20を共用するなら、**Cのholdout結果を見る前にB2方策も固定**し、全てを一度に開封する。C holdoutを見て再設計したら、同じ根をB2の未知確認と呼ばず、新しい別根を別承認する。二つの用途を16独立根と数えない。

8 blind rootsは最低限の開発性診断案でありpower保証・最終確認的Nではない。4校正根ではモデルやthresholdの安定性が不足し得る。校正の分散・共通支持・実用差・CI精度から最終Nを**blind結果前**に定め、変更には新しい承認を求める。根数が足りなければexploratoryのままにする。

H=600秒/rollout、decision前履歴4nsという**費用算定用案**。時刻0は共通状態/model/候補入力の公開完了、全分岐は独立process・同一GPU条件で順次動かす。根/方策の順序はblocked-randomizedで事前CSV固定。親重み・optimizer・入手可能dataは同じ。学習seedとMDseedは別streamとし、root/decision/MDchunk indexから固定table化する。同じMDseedでも開始座標が異なれば同じ軌跡とは呼ばない。

最小案の新MDstreamは1本/root/rolloutで、training×MD乱数の全面分散分解はできない。checkpoint/chunkを独立標本にしない。M0/更新recipeはL2から都合のよい1600を選ばず、P/L審査後に別承認する。ここが未決なら新実行開始不可。

## 5. 全campaignへ一般化する場合

上記はdecision後Hの条件付き結果で、履歴/初M0生成はsunk costとして別記する。全campaign開始からの同一予算を主張するには、履歴・初M0・warmupを各policy実runに含む別のD_total契約が必要。共有prefixの仮想課金だけを「実測end-to-end」にしない。

未知根のpaired差を主単位に、全根の正負/尺度/失敗を表示する。Cの低い予測誤差だけ、またはB2で1policyが良かっただけでは「科学Xの独立価値」を認定しない。native非可視のまま進捗が得られない、C増分なし、更新不要、cost negligibleという陰性結果も有効な研究結果として残す。

## 6. 動力学・候補・乱数の具体的条件

新historyはまず2ns境界で旧dataから共通M0を作り、同じ物理系で4nsまで継続した共通状態を凍結する案。M0を4ns dataで作り直してmodel ageを変えない。CONTINUEは元final.chkの全状態から連続し、chunkごとの速度再標本化をしない。旧B1の座標reseedとは異なる実装資格を別途検査する。他policyのreseedは最小化/新速度を含む現方式として全費用を残す。CONTINUEとの比較はこの行動束の効果で、更新だけの効果へ分解しない。

同状態Cの最初の候補pool/親は共通、B2が分岐した後の実data/candidateは異なり得る。同じなのは生成・窓・抽出の規則であり、全policyへ未来の共通candidateを供給して公平化しない。各policyで自分のdataしか使わない。MD/training seedのindex上限とevent順を事前固定し、連続MDでは初期seedを一回だけ設定、reseed型ではchunkごとの対応streamを使う。異なる分子状態・異なるMD長を同じ物理軌跡と呼ばない。
